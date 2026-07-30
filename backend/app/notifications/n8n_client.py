"""
AI Prozorro Intelligence - n8n Webhook Client.
Відправка зведення дашборду за сьогодні на n8n webhook (10:00 та 17:00 за Києвом).
"""
import logging
from datetime import date

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send_webhook(payload: dict) -> bool:
    """Відправити POST-запит на n8n webhook. Повертає True при успіху."""
    if not settings.n8n_webhook_url:
        logger.debug("N8N_WEBHOOK_URL не налаштовано, пропуск відправки")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.n8n_webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Webhook відправлено успішно (type={payload.get('type')})")
            return True
    except Exception as e:
        logger.error(f"Помилка відправки webhook: {e}")
        return False


async def send_daily_report(report_data: dict) -> bool:
    """
    Відправити щоденний звіт на n8n webhook.
    report_data очікується у форматі, аналогічному DailyReportResponse.
    Повертає True при успішній відправці.
    """
    payload = {
        "type": "daily_report",
        "report": report_data,
    }
    return await _send_webhook(payload)


def _compact_tender(t: dict) -> dict:
    """Компактний запис тендера для зведення (лише потрібні n8n поля)."""
    pid = t.get("prozorro_id")
    return {
        "title": (t.get("title") or "")[:200],
        "status": t.get("status") or "",
        "region": t.get("region") or "",
        "date": t.get("published_date") or "",
        "amount": t.get("amount"),
        "currency": t.get("currency") or "UAH",
        "participants_count": t.get("participants_count"),
        "risk_score": t.get("risk_score"),
        "risk_factors": t.get("risk_factors") or [],
        "url": f"https://prozorro.gov.ua/tender/{pid}" if pid else "",
    }


def build_dashboard_summary(dashboard: dict) -> dict:
    """
    Плоске зведення дашборду за сьогодні для n8n.
    dashboard - DashboardResponse.model_dump(mode="json") з days=1.
    Усі поля на верхньому рівні - зручно читати як {{$json.field}} в n8n.
    """
    kpi = dashboard.get("kpi") or {}
    chart = dashboard.get("chart_data") or []
    suspicious = dashboard.get("suspicious_tenders") or []
    active = dashboard.get("active_suspicious_tenders") or []

    # При days=1 у графіку одна точка - сьогодні
    today_point = chart[-1] if chart else {}

    high_risk = settings.high_risk_threshold
    critical_completed = [_compact_tender(t) for t in suspicious if (t.get("risk_score") or 0) >= high_risk]
    critical_active = [_compact_tender(t) for t in active if (t.get("risk_score") or 0) >= high_risk]
    watchlist = [_compact_tender(t) for t in suspicious if (t.get("risk_score") or 0) < high_risk]

    all_risky = suspicious + active
    max_risk = max(((t.get("risk_score") or 0) for t in all_risky), default=0)
    largest = max(all_risky, key=lambda t: t.get("amount") or 0, default=None)

    return {
        "type": "dashboard_summary",
        "period": "today",
        "report_date": date.today().isoformat(),
        "generated_at": dashboard.get("last_updated"),
        # Показники за сьогодні
        "total_tenders": kpi.get("total_tenders"),
        "suspicious_total": kpi.get("suspicious_tenders"),
        "today_new": kpi.get("today_new"),
        "today_volume": kpi.get("today_volume"),
        "competitive_count": today_point.get("tenders_count", 0),
        "reports_count": today_point.get("reports_count", 0),
        "competitive_volume": today_point.get("tenders_volume", 0),
        "reports_volume": today_point.get("reports_volume", 0),
        "high_risk_count": today_point.get("high_risk_count", 0),
        # Довідково (за всю базу)
        "total_companies": kpi.get("total_companies"),
        "total_buyers": kpi.get("total_buyers"),
        # Екстремуми за сьогодні
        "max_risk_score": max_risk,
        "largest_risky_tender": _compact_tender(largest) if largest else None,
        # Критичні тендери
        "critical_completed_count": len(critical_completed),
        "critical_active_count": len(critical_active),
        "critical_completed": critical_completed,
        "critical_active": critical_active,
        "watchlist_count": len(watchlist),
        "watchlist": watchlist,
    }


async def send_dashboard_summary(dashboard: dict) -> bool:
    """
    Відправити зведення дашборду за сьогодні на n8n webhook.
    dashboard - DashboardResponse.model_dump(mode="json") з days=1.
    Повертає True при успішній відправці.
    """
    return await _send_webhook(build_dashboard_summary(dashboard))
