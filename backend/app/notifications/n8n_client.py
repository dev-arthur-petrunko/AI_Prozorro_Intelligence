"""
AI Prozorro Intelligence - n8n Webhook Client.
Відправка даних на n8n webhook: щоденний звіт та миттєві сповіщення
про підозрілі активні тендери.
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings
from app.models.tender import Tender

logger = logging.getLogger(__name__)

KYIV_TZ = ZoneInfo("Europe/Kyiv")

# Порог risk_score для миттєвого сповіщення про підозрілий тендер
SUSPICIOUS_NOTIFY_THRESHOLD = 60

# Часове вікно для миттєвих сповіщень (за київським часом)
NOTIFY_HOUR_START = 9
NOTIFY_HOUR_END = 20


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


def _is_within_notify_window() -> bool:
    """Перевірити, чи поточний час у межах 9:00-20:00 за Києвом."""
    now_kyiv = datetime.now(KYIV_TZ)
    return NOTIFY_HOUR_START <= now_kyiv.hour < NOTIFY_HOUR_END


def is_active_status(status: str | None) -> bool:
    """Перевірити, чи статус тендера є 'активним' (active.tendering, active.qualification тощо)."""
    if not status:
        return False
    return status.startswith("active")


async def notify_suspicious_tender(tender: Tender) -> None:
    """
    Відправити миттєве сповіщення про підозрілий активний тендер,
    якщо виконані всі умови: статус активний, risk_score > порогу,
    і поточний час у межах 9:00-20:00 за Києвом.
    """
    if not is_active_status(tender.status):
        return

    if (tender.risk_score or 0) <= SUSPICIOUS_NOTIFY_THRESHOLD:
        return

    if not _is_within_notify_window():
        logger.debug(
            f"Тендер {tender.prozorro_id} підозрілий, але поза часовим вікном сповіщень (9:00-20:00 Київ)"
        )
        return

    payload = {
        "type": "suspicious_tender",
        "tender": {
            "prozorro_id": tender.prozorro_id,
            "title": tender.title,
            "status": tender.status,
            "amount": float(tender.amount) if tender.amount else None,
            "currency": tender.currency,
            "region": tender.region,
            "risk_score": tender.risk_score,
            "ai_analysis": tender.ai_analysis,
            "participants_count": tender.participants_count,
            "url": f"https://prozorro.gov.ua/tender/{tender.prozorro_id}",
        },
    }
    await _send_webhook(payload)


async def send_daily_report(report_data: dict) -> None:
    """
    Відправити щоденний звіт на n8n webhook.
    report_data очікується у форматі, аналогічному DailyReportResponse.
    """
    payload = {
        "type": "daily_report",
        "report": report_data,
    }
    await _send_webhook(payload)