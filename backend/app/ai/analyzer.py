"""
AI Prozorro Intelligence - AI Analyzer (оркестратор).
Координує Risk Engine та Groq для повного аналізу тендерів.

Аналіз розділено на дві фази:
1. Скоринг (Risk Engine) - локальний, без Groq, виконується для ВСІХ
   тендерів без оцінки, щоб індекс ризику ніколи не чекав на квоту AI.
2. Генерація AI-коментарів (Groq) - лише для ризикових тендерів,
   поки не вичерпано денну квоту (реальне вузьке місце - ліміт токенів).
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.tender import Tender
from app.models.buyer import Buyer
from app.models.company import Company
from app.ai.risk_engine import analyze_tender_risk, top_by_attention, attention_priority
from app.ai.groq_client import generate_ai_explanation, rate_limiter
from app.core.config import settings
from app.notifications.n8n_client import notify_suspicious_tender, SUSPICIOUS_NOTIFY_THRESHOLD

logger = logging.getLogger(__name__)

# Поріг ризику, вище якого генерується розгорнутий AI-коментар
EXPLANATION_RISK_THRESHOLD = 30


async def score_tender(tender: Tender, session: AsyncSession) -> int:
    """
    Фаза 1: розрахунок Risk Score через Risk Engine (без Groq).

    Returns:
        Розрахований risk_score (0-100).
    """
    risk_score, risk_factors_json = await analyze_tender_risk(tender, session)

    # Сповіщаємо лише при ПЕРШОМУ перетині порогу, щоб повторний скоринг
    # stale-тендерів не дублював сповіщення кожні 15 хвилин
    was_below_threshold = (tender.risk_score or 0) <= SUSPICIOUS_NOTIFY_THRESHOLD

    tender.risk_score = risk_score
    tender.risk_factors = risk_factors_json

    if risk_score <= EXPLANATION_RISK_THRESHOLD:
        # Низький ризик - розгорнутий коментар не потрібен, прибираємо застарілий
        tender.ai_analysis = None
        tender.analysis_stale = False

    logger.debug(f"Tender {tender.prozorro_id}: risk_score={risk_score}")

    # Миттєве сповіщення про підозрілий активний тендер (якщо умови виконані)
    if was_below_threshold:
        await notify_suspicious_tender(tender)

    return risk_score


async def generate_tender_explanation(tender: Tender, session: AsyncSession) -> bool:
    """
    Фаза 2: генерація AI-коментаря через Groq для ризикового тендера.
    Збирає додатковий контекст (замовник, переможець, ціни по категорії).

    Returns:
        True - коментар згенеровано, False - не вдалося (квота/помилка API).
    """
    risk_factors = json.loads(tender.risk_factors) if tender.risk_factors else []

    # Додатковий контекст для глибшого аналізу
    buyer_name = None
    winner_name = None
    buyer_tenders_count = 0
    buyer_avg_participants = None
    if tender.buyer_id:
        buyer = await session.get(Buyer, tender.buyer_id)
        if buyer:
            buyer_name = buyer.name
            buyer_tenders_count = buyer.tenders_count or 0
            buyer_avg_participants = buyer.avg_participants
    if tender.winner_id:
        winner = await session.get(Company, tender.winner_id)
        winner_name = winner.name if winner else None

    # Історія переможця: скільки разів він вигравав у ЦЬОГО замовника
    # та скільки перемог має загалом у базі (критерій 5)
    winner_wins_with_buyer = 0
    winner_total_wins = 0
    if tender.winner_id:
        winner_total_wins = (await session.execute(
            select(func.count(Tender.id)).where(Tender.winner_id == tender.winner_id)
        )).scalar() or 0
        if tender.buyer_id:
            winner_wins_with_buyer = (await session.execute(
                select(func.count(Tender.id)).where(
                    Tender.buyer_id == tender.buyer_id,
                    Tender.winner_id == tender.winner_id,
                )
            )).scalar() or 0

    # Розподіл перемог серед постачальників цього замовника (критерії 8, 9)
    buyer_winners = []
    if tender.buyer_id:
        dist = (await session.execute(
            select(Company.name, func.count(Tender.id).label("wins"))
            .join(Tender, Tender.winner_id == Company.id)
            .where(Tender.buyer_id == tender.buyer_id)
            .group_by(Company.name)
            .order_by(func.count(Tender.id).desc())
            .limit(5)
        )).all()
        buyer_winners = [(row[0], int(row[1])) for row in dist]

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

    # Медіана цін за одиницю по категорії (та ж CPV + та ж одиниця виміру)
    unit_price_median = None
    unit_price_count = 0
    if tender.unit_price and tender.cpv_code and tender.unit_name:
        unit_stats = (await session.execute(
            select(
                func.percentile_cont(0.5).within_group(Tender.unit_price),
                func.count(Tender.id),
            ).where(
                Tender.cpv_code == tender.cpv_code,
                Tender.unit_name == tender.unit_name,
                Tender.unit_price.isnot(None),
                Tender.id != tender.id,
            )
        )).first()
        if unit_stats and unit_stats[0]:
            unit_price_median = float(unit_stats[0])
            unit_price_count = int(unit_stats[1])

    explanation = await generate_ai_explanation(
        tender_title=tender.title,
        tender_amount=tender.amount or 0,
        risk_score=tender.risk_score or 0,
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
        quantity=tender.quantity,
        unit_name=tender.unit_name,
        unit_price=tender.unit_price,
        unit_price_median=unit_price_median,
        unit_price_count=unit_price_count,
        procurement_method=tender.procurement_method,
        final_amount=tender.final_amount,
        winner_total_wins=winner_total_wins,
        winner_wins_with_buyer=winner_wins_with_buyer,
        buyer_tenders_count=buyer_tenders_count,
        buyer_avg_participants=buyer_avg_participants,
        buyer_winners=buyer_winners,
    )

    if not explanation:
        # Квота вичерпана або помилка API: НЕ знімаємо analysis_stale,
        # щоб тендер залишився у черзі на генерацію коментаря
        return False

    tender.ai_analysis = explanation
    # Коментар актуальний - знімаємо прапорець переаналізу
    tender.analysis_stale = False
    return True


async def _run_scoring_phase(session: AsyncSession, limit: int) -> int:
    """
    Фаза 1: порахувати Risk Score всім тендерам без оцінки та тим,
    що позначені analysis_stale (значуще оновлення даних).
    Groq не використовується - обмежень квоти немає.
    """
    result = await session.execute(
        select(Tender)
        .where(
            (Tender.risk_score.is_(None)) |
            (Tender.analysis_stale.is_(True))
        )
        .order_by(Tender.published_date.desc().nullslast())
        .limit(limit)
    )
    tenders = result.scalars().all()

    scored = 0
    for tender in tenders:
        try:
            await score_tender(tender, session)
            # Прапорець stale лишаємо тільки якщо є що освіжати у фазі 2:
            # активний тендер з наявним коментарем. Коментар завершеного
            # тендера фінальний, а без коментаря достатньо ai_analysis IS NULL
            if tender.analysis_stale:
                is_active = (tender.status or "").startswith("active")
                if tender.ai_analysis is None or not is_active:
                    tender.analysis_stale = False
            scored += 1
        except Exception as e:
            logger.error(f"Помилка скорингу тендера {tender.id}: {e}")

    if scored:
        await session.commit()
    return scored


async def _top_candidates_for_period(session: AsyncSession, period_start) -> list:
    """
    Топ-кандидати дашборду для одного варіанта періоду:
    топ-10 завершених + топ-10 активних (логіка та пороги як у dashboard.py).
    """
    not_reporting = (Tender.procurement_method.is_(None)) | (Tender.procurement_method != "reporting")
    min_amount = settings.dashboard_suspicious_min_amount

    def with_period(query):
        if period_start is not None:
            return query.where(Tender.published_date >= period_start)
        return query

    # Топ за індексом ризику - ЗАВЕРШЕНІ (високий індекс, fallback >= 40)
    completed = (await session.execute(
        with_period(
            select(Tender)
            .where(
                Tender.risk_score >= settings.high_risk_threshold,
                Tender.status.in_(["complete", "unsuccessful", "cancelled"]),
                Tender.amount >= min_amount,
                not_reporting,
            )
        )
        .order_by(Tender.risk_score.desc(), Tender.amount.desc())
        .limit(40)
    )).scalars().all()
    if not completed:
        completed = (await session.execute(
            with_period(
                select(Tender)
                .where(
                    Tender.risk_score >= settings.dashboard_suspicious_fallback_risk,
                    Tender.status.in_(["complete", "unsuccessful", "cancelled"]),
                    Tender.amount >= min_amount,
                    not_reporting,
                )
            )
            .order_by(Tender.risk_score.desc(), Tender.amount.desc())
            .limit(40)
        )).scalars().all()
    completed_top = top_by_attention(completed, limit=10)

    # Топ підозрілі АКТИВНІ тендери (risk >= 50)
    active = (await session.execute(
        with_period(
            select(Tender)
            .where(
                Tender.risk_score >= settings.dashboard_active_risk_min,
                Tender.status.like("active%"),
                not_reporting,
            )
        )
        .order_by(Tender.risk_score.desc(), Tender.amount.desc())
        .limit(40)
    )).scalars().all()
    active_top = top_by_attention(active, limit=10)

    return completed_top + active_top


async def _select_top_tenders(session: AsyncSession) -> list:
    """
    Відібрати тендери, які реально показуються у топах дашборду за БУДЬ-ЯКОГО
    вибору періоду користувачем: за весь час, 7, 30 та 90 днів.
    Дзеркалить логіку dashboard.py: ті самі пороги, фільтри та ранжування.
    Денна квота Groq мала (~30-35 коментарів) - витрачаємо її лише на те,
    що бачить користувач.
    """
    candidates = []
    for days in (None, 7, 30, 90):
        period_start = None
        if days:
            period_start = datetime.combine(
                date.today() - timedelta(days=days - 1), datetime.min.time()
            )
        candidates.extend(await _top_candidates_for_period(session, period_start))

    # Об'єднання без дублів, найважливіші (пріоритет уваги) - першими
    seen_ids = set()
    merged = []
    for tender in candidates:
        if tender.id in seen_ids:
            continue
        seen_ids.add(tender.id)
        merged.append(tender)
    merged.sort(
        key=lambda t: attention_priority(t.risk_score, t.amount),
        reverse=True,
    )
    return merged


async def _run_explanation_phase(session: AsyncSession, limit: int, force: bool) -> int:
    """
    Фаза 2: згенерувати AI-коментарі ЛИШЕ для тендерів з топів дашборду,
    поки не вичерпано денну квоту Groq.
    """
    top_tenders = await _select_top_tenders(session)

    if force:
        # Перегенерація: всі тендери з топів, навіть з наявним коментарем
        tenders = top_tenders[:limit]
    else:
        # Без коментаря, АБО активні з застарілим коментарем (analysis_stale).
        # Для завершених тендерів наявний коментар фінальний - не чіпаємо
        tenders = [
            t for t in top_tenders
            if t.ai_analysis is None or (t.analysis_stale and (t.status or "").startswith("active"))
        ][:limit]

    if not tenders:
        return 0

    logger.info(
        f"Генерація AI-коментарів для {len(tenders)} тендерів з топів дашборду "
        f"(force={force}, залишок денної квоти Groq: {rate_limiter.daily_remaining} запитів)..."
    )

    generated = 0
    for tender in tenders:
        # Квота вичерпана (запити або токени) - зупиняємось, продовжимо завтра
        if rate_limiter.daily_remaining == 0:
            logger.warning("Денну квоту Groq вичерпано - зупинка генерації, продовжимо завтра")
            break

        try:
            if force:
                # У force-режимі освіжаємо і сам Risk Score
                await score_tender(tender, session)
                if (tender.risk_score or 0) <= EXPLANATION_RISK_THRESHOLD:
                    continue

            if await generate_tender_explanation(tender, session):
                generated += 1
                # Пауза між запитами: реальне вузьке місце Groq - ліміт
                # токенів за хвилину (TPM), а не кількість запитів
                await asyncio.sleep(settings.groq_request_pause_seconds)
        except Exception as e:
            logger.error(f"Помилка генерації коментаря для тендера {tender.id}: {e}")

    if generated or force:
        await session.commit()
    return generated


async def run_ai_analysis_batch(force: bool = False, limit: int = 50):
    """
    Запустити AI аналіз тендерів у дві фази:
    1. Risk Score для всіх тендерів без оцінки (без Groq, без квот).
    2. AI-коментарі для ризикових тендерів у межах денної квоти Groq.

    Args:
        force: Якщо True - перегенерувати коментарі навіть для вже проаналізованих
               ризикових тендерів (найризиковіші першими).
        limit: Максимальна кількість тендерів для генерації коментарів у пакеті.
    """
    async with async_session_factory() as session:
        # Фаза 1: скоринг - дешевий (локальні запити до БД), тому ліміт більший
        scored = await _run_scoring_phase(session, limit=settings.ai_scoring_batch_limit)
        if scored:
            logger.info(f"Risk Score розраховано для {scored} тендерів")

        # Фаза 2: AI-коментарі у межах квоти Groq
        generated = await _run_explanation_phase(session, limit=limit, force=force)

        logger.info(
            f"AI аналіз завершено: скоринг={scored}, коментарі={generated}, "
            f"залишок денної квоти Groq: {rate_limiter.daily_remaining}"
        )
