"""
AI Prozorro Intelligence - Retention (утримання даних).
Видаляє застарілі записи за межами вікна утримання.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete

from app.database import async_session_factory
from app.models.tender import Tender
from app.core.config import settings

logger = logging.getLogger(__name__)


async def cleanup_old_data():
    """Видалити записи старіші за DATA_RETENTION_DAYS."""
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
        
        return deleted_count
