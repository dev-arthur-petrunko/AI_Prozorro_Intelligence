"""
AI Prozorro Intelligence - Планувальник задач.
Запускає періодичну синхронізацію, аналітику та очищення даних.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from app.core.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

KYIV_TZ = ZoneInfo("Europe/Kyiv")


async def sync_job():
    """Задача синхронізації з Prozorro."""
    from app.collectors.sync_service import run_sync
    logger.info("⏰ Запуск задачі синхронізації...")
    await run_sync()


async def analytics_job():
    """Задача перерахунку аналітики."""
    from app.analytics.engine import recalculate_all
    logger.info("⏰ Запуск задачі аналітики...")
    await recalculate_all()


async def retention_job():
    """Задача очищення застарілих даних."""
    from app.analytics.retention import cleanup_old_data
    logger.info("⏰ Запуск задачі очищення...")
    await cleanup_old_data()


async def ai_analysis_job():
    """Задача AI аналізу нових тендерів."""
    from app.ai.analyzer import run_ai_analysis_batch
    logger.info("⏰ Запуск AI аналізу...")
    await run_ai_analysis_batch()


async def daily_report_job():
    """Зведення дашборду за сьогодні на n8n webhook о 10:00 та 17:00 за Києвом."""
    from app.database import async_session_factory
    from app.api.routes.dashboard import get_dashboard
    from app.notifications.n8n_client import send_dashboard_summary

    logger.info("⏰ Запуск зведення дашборду за сьогодні...")
    async with async_session_factory() as session:
        dashboard = await get_dashboard(days=1, db=session)
        await send_dashboard_summary(dashboard.model_dump(mode="json"))


async def initial_import_job():
    """Початковий імпорт (виконується один раз)."""
    from app.collectors.sync_service import run_initial_import
    logger.info("⏰ Запуск початкового імпорту...")
    await run_initial_import()


def start_scheduler():
    """Запуск планувальника."""
    # Синхронізація кожні N хвилин
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(minutes=settings.sync_interval_minutes),
        id="sync_prozorro",
        name="Синхронізація з Prozorro",
        replace_existing=True,
    )

    # Перерахунок аналітики кожну годину
    scheduler.add_job(
        analytics_job,
        trigger=IntervalTrigger(hours=1),
        id="recalc_analytics",
        name="Перерахунок аналітики",
        replace_existing=True,
    )

    # Очищення застарілих даних раз на добу (о 03:00)
    scheduler.add_job(
        retention_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_old_data",
        name="Очищення застарілих даних",
        replace_existing=True,
    )

    # AI аналіз кожні 15 хвилин
    scheduler.add_job(
        ai_analysis_job,
        trigger=IntervalTrigger(minutes=15),
        id="ai_analysis",
        name="AI аналіз тендерів",
        replace_existing=True,
    )

    # Зведення дашборду на n8n о 10:00 та 17:00 за Києвом
    scheduler.add_job(
        daily_report_job,
        trigger=CronTrigger(hour="10,17", minute=0, timezone=KYIV_TZ),
        id="daily_report",
        name="Зведення дашборду за сьогодні",
        replace_existing=True,
    )

    # Початковий імпорт через 10 секунд після старту
    scheduler.add_job(
        initial_import_job,
        trigger="date",
        id="initial_import",
        name="Початковий імпорт",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"✅ Планувальник запущено (синхронізація кожні {settings.sync_interval_minutes} хв)")


def stop_scheduler():
    """Зупинити планувальник."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("🛑 Планувальник зупинено")