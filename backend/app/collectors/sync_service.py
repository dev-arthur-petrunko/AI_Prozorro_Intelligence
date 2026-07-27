"""
AI Prozorro Intelligence - Сервіс синхронізації даних.
Відповідає за імпорт та оновлення даних з Prozorro.
"""

import logging
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.collectors.prozorro_client import prozorro_client
from app.collectors.data_normalizer import normalize_tender
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.core.config import settings

logger = logging.getLogger(__name__)

# Завершені статуси: дані фінальні, готовий AI-аналіз лишаємо як є
COMPLETED_STATUSES = {"complete", "unsuccessful", "cancelled"}


async def get_or_create_buyer(session: AsyncSession, buyer_info: dict) -> Buyer:
    """Отримати або створити замовника."""
    edrpou = buyer_info.get("edrpou")

    if edrpou:
        result = await session.execute(select(Buyer).where(Buyer.edrpou == edrpou))
        buyer = result.scalar_one_or_none()
        if buyer:
            return buyer

    result = await session.execute(select(Buyer).where(Buyer.name == buyer_info["name"]))
    buyer = result.scalar_one_or_none()
    if buyer:
        return buyer

    buyer = Buyer(name=buyer_info["name"], edrpou=edrpou, region=buyer_info.get("region"))
    session.add(buyer)
    await session.flush()
    return buyer


async def get_or_create_company(session: AsyncSession, company_info: dict) -> Company:
    """Отримати або створити компанію."""
    edrpou = company_info.get("edrpou")

    if edrpou:
        result = await session.execute(select(Company).where(Company.edrpou == edrpou))
        company = result.scalar_one_or_none()
        if company:
            return company

    result = await session.execute(select(Company).where(Company.name == company_info["name"]))
    company = result.scalar_one_or_none()
    if company:
        return company

    company = Company(name=company_info["name"], edrpou=edrpou, region=company_info.get("region"))
    session.add(company)
    await session.flush()
    return company


async def import_tender(session: AsyncSession, normalized_data: dict) -> bool:
    """
    Імпортувати або оновити один тендер.
    Повертає True, якщо створено НОВИЙ запис.
    """
    prozorro_id = normalized_data.get("prozorro_id")
    if not prozorro_id:
        return False

    result = await session.execute(select(Tender).where(Tender.prozorro_id == prozorro_id))
    existing = result.scalar_one_or_none()

    if existing:
        await _update_existing_tender(session, existing, normalized_data)
        return False

    buyer_id = None
    buyer_info = normalized_data.pop("buyer_info", None)
    if buyer_info:
        buyer = await get_or_create_buyer(session, buyer_info)
        buyer_id = buyer.id

    winner_id = None
    winner_info = normalized_data.pop("winner_info", None)
    if winner_info:
        company = await get_or_create_company(session, winner_info)
        winner_id = company.id

    tender = Tender(
        prozorro_id=normalized_data["prozorro_id"],
        title=normalized_data["title"],
        description=normalized_data.get("description"),
        status=normalized_data.get("status", "active"),
        procurement_method=normalized_data.get("procurement_method"),
        cpv_code=normalized_data.get("cpv_code"),
        region=normalized_data.get("region"),
        published_date=normalized_data.get("published_date"),
        end_date=normalized_data.get("end_date"),
        amount=normalized_data.get("amount"),
        final_amount=normalized_data.get("final_amount"),
        currency=normalized_data.get("currency", "UAH"),
        participants_count=normalized_data.get("participants_count", 0),
        buyer_id=buyer_id,
        winner_id=winner_id,
    )
    session.add(tender)
    return True


async def _update_existing_tender(session: AsyncSession, existing: Tender, normalized_data: dict) -> None:
    """
    Оновити наявний тендер новими даними з Prozorro.

    Логіка переаналізу (analysis_stale):
    - якщо тендер БУВ завершений (COMPLETED_STATUSES) - дані фінальні,
      готовий AI-аналіз не чіпаємо;
    - якщо був НЕзавершений і змінилися значущі для ризику поля
      (статус, к-сть учасників, фінальна ціна, переможець) -
      ставимо прапорець на повторний аналіз.
    """
    old_status = existing.status
    was_completed = old_status in COMPLETED_STATUSES

    new_status = normalized_data.get("status", old_status)
    new_participants = normalized_data.get("participants_count", existing.participants_count)
    new_final = normalized_data.get("final_amount")

    significant_change = False
    if new_status != old_status:
        significant_change = True
    if new_participants != existing.participants_count:
        significant_change = True
    if new_final is not None and new_final != existing.final_amount:
        significant_change = True

    # Переможець міг з'явитися при переході active -> complete
    winner_info = normalized_data.pop("winner_info", None)
    if winner_info and not existing.winner_id:
        company = await get_or_create_company(session, winner_info)
        existing.winner_id = company.id
        significant_change = True

    existing.status = new_status
    existing.participants_count = new_participants
    if not existing.procurement_method:
        existing.procurement_method = normalized_data.get("procurement_method")
    if new_final is not None:
        existing.final_amount = new_final
    existing.updated_at = datetime.utcnow()

    # Переаналіз лише для тендерів, що ще НЕ були завершені раніше
    if significant_change and not was_completed:
        existing.analysis_stale = True


async def run_initial_import():
    """Виконати початковий імпорт (якщо база порожня)."""
    async with async_session_factory() as session:
        result = await session.execute(select(func.count(Tender.id)))
        count = result.scalar()

        if count and count > 0:
            logger.info(f"База вже містить {count} тендерів, пропуск початкового імпорту")
            return

        logger.info("База порожня. Запуск імпорту останніх тендерів...")

        # Завантажуємо 200 останніх тендерів (найновіші першими)
        raw_tenders = await prozorro_client.fetch_recent_tenders(max_tenders=200)

        new_count = 0
        batch_size = 20
        for i, raw_tender in enumerate(raw_tenders):
            normalized = normalize_tender(raw_tender)
            is_new = await import_tender(session, normalized)
            if is_new:
                new_count += 1

            # Комітимо кожні 20 записів
            if (i + 1) % batch_size == 0:
                await session.commit()
                logger.info(f"Збережено {new_count} тендерів...")

        await session.commit()
        logger.info(f"Початковий імпорт завершено: {new_count} нових тендерів")

        # Одразу запускаємо аналітику
        from app.analytics.engine import recalculate_all
        await recalculate_all()

        # Одразу запускаємо AI аналіз
        from app.ai.analyzer import run_ai_analysis_batch
        await run_ai_analysis_batch()


async def run_sync():
    """Інкрементальна синхронізація."""
    async with async_session_factory() as session:
        logger.info("Запуск синхронізації...")

        raw_tenders = await prozorro_client.fetch_recent_tenders(max_tenders=50)

        new_count = 0
        for raw_tender in raw_tenders:
            normalized = normalize_tender(raw_tender)
            is_new = await import_tender(session, normalized)
            if is_new:
                new_count += 1

        await session.commit()
        logger.info(f"Синхронізація завершена: {new_count} нових тендерів")

        # Аналітику/AI запускаємо, якщо є нові АБО є тендери, що потребують переаналізу
        stale_count = (await session.execute(
            select(func.count(Tender.id)).where(Tender.analysis_stale.is_(True))
        )).scalar() or 0

        if new_count > 0 or stale_count > 0:
            from app.analytics.engine import recalculate_all
            await recalculate_all()
            from app.ai.analyzer import run_ai_analysis_batch
            await run_ai_analysis_batch()

        return new_count
