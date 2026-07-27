"""
AI Prozorro Intelligence - Retention (утримання даних).
Видаляє застарілі записи за межами вікна утримання та дедуплікує дані.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select, func

from app.database import async_session_factory
from app.models.tender import Tender
from app.core.config import settings

logger = logging.getLogger(__name__)


async def dedupe_tenders() -> int:
    """
    Страховка від дублів тендерів за prozorro_id.
    На рівні БД є unique-індекс, тож дублі неможливі, але якщо база
    створювалась без нього (стара міграція) - прибираємо зайві копії,
    лишаючи найсвіжішу (max updated_at, потім max id).
    """
    async with async_session_factory() as session:
        dup_rows = (await session.execute(
            select(Tender.prozorro_id)
            .group_by(Tender.prozorro_id)
            .having(func.count(Tender.id) > 1)
        )).scalars().all()

        if not dup_rows:
            return 0

        removed = 0
        for pid in dup_rows:
            copies = (await session.execute(
                select(Tender)
                .where(Tender.prozorro_id == pid)
                .order_by(Tender.updated_at.desc().nullslast(), Tender.id.desc())
            )).scalars().all()
            # Перша копія - найсвіжіша, лишаємо; решту видаляємо
            for extra in copies[1:]:
                await session.delete(extra)
                removed += 1

        await session.commit()
        if removed:
            logger.warning(f"Дедуплікація: видалено {removed} дублів тендерів за prozorro_id")
        return removed


async def cleanup_old_data():
    """Видалити записи старіші за DATA_RETENTION_DAYS та прибрати дублі."""
    async with async_session_factory() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.data_retention_days)

        result = await session.execute(
            delete(Tender).where(Tender.created_at < cutoff_date)
        )
        deleted_count = result.rowcount

        await session.commit()

        if deleted_count > 0:
            logger.info(f"Видалено {deleted_count} застарілих записів (старіших {settings.data_retention_days} днів)")
        else:
            logger.debug("Немає застарілих записів для видалення")

    # Дедуплікація як частина регулярного очищення
    await dedupe_tenders()

    return deleted_count
