"""
AI Prozorro Intelligence - Клієнт Prozorro API.
Збирає дані з публічного API Prozorro.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = settings.prozorro_api_url
API_VERSION = settings.prozorro_api_version


class ProzorroClient:
    """Клієнт для роботи з Prozorro Public API."""

    def __init__(self):
        self.base_url = f"{BASE_URL}/api/{API_VERSION}"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "AI-Prozorro-Intelligence/1.0"},
        )

    async def close(self):
        """Закрити HTTP клієнт."""
        await self.client.aclose()

    async def get_tenders_page(self, offset: Optional[str] = None) -> Dict[str, Any]:
        """Отримати одну сторінку тендерів."""
        params = {"limit": 100, "descending": 1}
        if offset:
            params["offset"] = offset

        try:
            response = await self.client.get(
                f"{self.base_url}/tenders",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "data": data.get("data", []),
                "next_page": data.get("next_page", {}).get("offset"),
            }
        except Exception as e:
            logger.error(f"Помилка Prozorro API: {e}")
            return {"data": [], "next_page": None}

    async def get_tender_detail(self, tender_id: str) -> Optional[Dict[str, Any]]:
        """Отримати детальну інформацію про тендер."""
        try:
            response = await self.client.get(
                f"{self.base_url}/tenders/{tender_id}",
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data")
        except Exception as e:
            logger.warning(f"Не вдалося отримати тендер {tender_id}: {e}")
            return None

    async def fetch_recent_tenders(self, max_tenders: int = 200) -> List[Dict[str, Any]]:
        """
        Завантажити останні тендери (descending=1 дає найновіші першими).
        """
        all_tenders = []
        offset = None
        pages = 0
        max_pages = max_tenders // 100 + 1

        logger.info(f"Завантаження останніх {max_tenders} тендерів...")

        while len(all_tenders) < max_tenders and pages < max_pages:
            result = await self.get_tenders_page(offset=offset)
            items = result["data"]

            if not items:
                break

            for item in items:
                tid = item.get("id")
                if tid and len(all_tenders) < max_tenders:
                    detail = await self.get_tender_detail(tid)
                    if detail:
                        all_tenders.append(detail)

            offset = result.get("next_page")
            if not offset:
                break

            pages += 1
            logger.info(f"Завантажено {len(all_tenders)} тендерів (сторінка {pages})...")

        logger.info(f"Всього завантажено: {len(all_tenders)} тендерів")
        return all_tenders


prozorro_client = ProzorroClient()
