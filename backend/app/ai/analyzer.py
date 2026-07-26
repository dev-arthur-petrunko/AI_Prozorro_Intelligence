"""
AI Prozorro Intelligence - AI Analyzer (оркестратор).
Координує Risk Engine та Groq для повного аналізу тендерів.
"""

import asyncio
import json
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.tender import Tender
from app.models.buyer import Buyer
from app.models.company import Company
from app.ai.risk_engine import analyze_tender_risk
from app.ai.groq_client import generate_ai_explanation, rate_limiter

logger = logging.getLogger(__name__)


async def analyze_single_tender(tender: Tender, session: AsyncSession) -> None:
    """
    Повний AI аналіз одного тендера: Risk Score + Groq пояснення.
    """
    # Крок 1: Розрахунок Risk Score
    risk_score, risk_factors_json = await analyze_tender_risk(tender, session)
    
    tender.risk_score = risk_score
    tender.risk_factors = risk_factors_json
    
    # Крок 2: Генерація AI пояснення (тільки для ризикових тендерів)
    if risk_score > 30:
        risk_factors = json.loads(risk_factors_json) if risk_factors_json else []

        # Додатковий контекст для глибшого аналізу
        buyer_name = None
        winner_name = None
        if tender.buyer_id:
            buyer = await session.get(Buyer, tender.buyer_id)
            buyer_name = buyer.name if buyer else None
        if tender.winner_id:
            winner = await session.get(Company, tender.winner_id)
            winner_name = winner.name if winner else None

        # Порівняльні дані цін по категорії CPV (для аналізу критерію "Ціна")
        category_avg = None
        category_count = 0
        price_examples = []
        if tender.cpv_code and tender.amount:
            stats = (await session.execute(
                select(func.avg(Tender.amount), func.count(Tender.id))
                .where(
                    Tender.cpv_code == tender.cpv_code,
                    Tender.amount.isnot(None),
                    Tender.id != tender.id,
                )
            )).first()
            if stats and stats[1]:
                category_avg = float(stats[0])
                category_count = int(stats[1])
                # Приклади цін схожих тендерів тієї ж категорії (найсвіжіші)
                examples_result = await session.execute(
                    select(Tender.title, Tender.amount)
                    .where(
                        Tender.cpv_code == tender.cpv_code,
                        Tender.amount.isnot(None),
                        Tender.id != tender.id,
                    )
                    .order_by(Tender.published_date.desc().nullslast())
                    .limit(3)
                )
                price_examples = [(row[0], float(row[1])) for row in examples_result.all()]

        explanation = await generate_ai_explanation(
            tender_title=tender.title,
            tender_amount=tender.amount or 0,
            risk_score=risk_score,
            risk_factors=risk_factors,
            currency=tender.currency,
            region=tender.region,
            status=tender.status,
            participants_count=tender.participants_count or 0,
            buyer_name=buyer_name,
            winner_name=winner_name,
            cpv_code=tender.cpv_code,
            prozorro_id=tender.prozorro_id,
            published_date=str(tender.published_date) if tender.published_date else None,
            end_date=str(tender.end_date) if tender.end_date else None,
            category_avg=category_avg,
            category_count=category_count,
            price_examples=price_examples,
        )
        if explanation:
            tender.ai_analysis = explanation
    
    logger.debug(f"Tender {tender.prozorro_id}: risk_score={risk_score}")


async def run_ai_analysis_batch(force: bool = False, limit: int = 50):
    """
    Запустити AI аналіз для тендерів без оцінки ризику.
    Обробляє пакетами (за замовчуванням 50) для збереження rate limits Groq.

    Args:
        force: Якщо True - перегенерувати пояснення навіть для вже проаналізованих
               ризикових тендерів (найризиковіші першими).
        limit: Максимальна кількість тендерів у пакеті.
    """
    async with async_session_factory() as session:
        if force:
            # Перегенерація: усі ризикові тендери, найризиковіші першими
            query = (
                select(Tender)
                .where(Tender.risk_score > 30)
                .order_by(Tender.risk_score.desc())
                .limit(limit)
            )
        else:
            # Знайти тендери без оцінки ризику АБО без AI пояснення (для ризикових)
            query = (
                select(Tender)
                .where(
                    (Tender.risk_score.is_(None)) |
                    ((Tender.risk_score > 30) & (Tender.ai_analysis.is_(None)))
                )
                .order_by(Tender.risk_score.desc().nullslast())
                .limit(limit)
            )

        result = await session.execute(query)
        tenders = result.scalars().all()

        if not tenders:
            logger.info("Немає тендерів для AI аналізу")
            return

        logger.info(
            f"Запуск AI аналізу для {len(tenders)} тендерів (force={force}, "
            f"залишок денного ліміту Groq: {rate_limiter.daily_remaining})..."
        )

        analyzed = 0
        for tender in tenders:
            try:
                # Якщо денний ліміт Groq вичерпано - Risk Score все одно рахуємо,
                # але зупиняємось, коли пояснення вже не генеруються
                needs_explanation = (tender.risk_score or 0) > 30 or tender.risk_score is None
                if needs_explanation and rate_limiter.daily_remaining == 0 and force:
                    logger.warning("Денний ліміт Groq вичерпано - зупинка пакету, продовжимо завтра")
                    break

                await analyze_single_tender(tender, session)
                analyzed += 1
                # Пауза між запитами: ліміт Groq 30 запитів/хв => ~2.2 сек між запитами
                await asyncio.sleep(2.2)
            except Exception as e:
                logger.error(f"Помилка аналізу тендера {tender.id}: {e}")

        await session.commit()
        logger.info(f"AI аналіз завершено: {analyzed}/{len(tenders)} тендерів оброблено")
