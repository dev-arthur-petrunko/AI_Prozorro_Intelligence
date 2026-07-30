"""
AI Prozorro Intelligence - Health & Admin endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.config import settings
from app.models.tender import Tender
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Перевірка стану системи."""
    try:
        result = await db.execute(select(func.count(Tender.id)))
        count = result.scalar() or 0
        db_status = "connected"
        last_sync = (await db.execute(select(func.max(Tender.updated_at)))).scalar()
    except Exception:
        count = 0
        db_status = "disconnected"
        last_sync = None

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        database=db_status,
        tenders_count=count,
        last_sync=last_sync.isoformat() if last_sync else None,
    )


@router.post("/admin/run-analytics")
async def run_analytics_now():
    """Вручну запустити перерахунок аналітики."""
    from app.analytics.engine import recalculate_all
    await recalculate_all()
    return {"status": "ok", "message": "Analytics recalculated"}


@router.post("/admin/run-ai-analysis")
async def run_ai_analysis_now(force: bool = False, limit: int = 50):
    """Вручну запустити AI аналіз. force=true перегенерує пояснення для ризикових тендерів."""
    from app.ai.analyzer import run_ai_analysis_batch
    await run_ai_analysis_batch(force=force, limit=limit)
    return {"status": "ok", "message": "AI analysis completed", "force": force}


@router.post("/admin/send-daily-report")
async def send_daily_report_now(db: AsyncSession = Depends(get_db)):
    """
    Вручну сформувати та відправити зведення дашборду за сьогодні на n8n webhook.
    Використовується для перевірки, що вебхук дійсно отримує дані.
    """
    from app.api.routes.dashboard import get_dashboard
    from app.notifications.n8n_client import send_dashboard_summary

    if not settings.n8n_webhook_url:
        return {"status": "error", "message": "N8N_WEBHOOK_URL не налаштовано"}

    dashboard = await get_dashboard(days=1, db=db)
    delivered = await send_dashboard_summary(dashboard.model_dump(mode="json"))
    return {
        "status": "ok" if delivered else "failed",
        "delivered": delivered,
        "webhook_configured": True,
    }
