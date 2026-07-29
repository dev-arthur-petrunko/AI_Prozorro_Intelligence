"""
AI Prozorro Intelligence - n8n Webhook Client.
Відправка щоденного звіту на n8n webhook (10:00, 13:00, 16:00, 19:00 за Києвом).
"""
import logging

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
