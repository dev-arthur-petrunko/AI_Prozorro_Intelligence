"""
AI Prozorro Intelligence - Нормалізатор даних.
Перетворює сирі дані Prozorro у внутрішні моделі.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Парсинг дати з різних форматів Prozorro."""
    if not date_str:
        return None
    try:
        # ISO формат - видаляємо timezone для простоти
        if "T" in date_str:
            # Прибираємо timezone offset
            clean = date_str.split("+")[0].split("Z")[0]
            return datetime.fromisoformat(clean)
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def extract_amount(tender_data: Dict[str, Any]) -> Tuple[Optional[float], str]:
    """Витягнути суму та валюту з даних тендера."""
    value = tender_data.get("value", {})
    if isinstance(value, dict):
        amount = value.get("amount")
        currency = value.get("currency", "UAH")
        return amount, currency
    return None, "UAH"


def extract_buyer_info(tender_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Витягнути інформацію про замовника."""
    procuring = tender_data.get("procuringEntity", {})
    if not procuring:
        return None
    
    identifier = procuring.get("identifier", {})
    address = procuring.get("address", {})
    
    return {
        "name": procuring.get("name", "Невідомий замовник"),
        "edrpou": identifier.get("id"),
        "region": address.get("region") or address.get("locality"),
    }


def extract_winner_info(tender_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Витягнути інформацію про переможця."""
    awards = tender_data.get("awards", [])
    
    for award in awards:
        if award.get("status") == "active":
            suppliers = award.get("suppliers", [])
            if suppliers:
                supplier = suppliers[0]
                identifier = supplier.get("identifier", {})
                address = supplier.get("address", {})
                return {
                    "name": supplier.get("name", "Невідома компанія"),
                    "edrpou": identifier.get("id"),
                    "region": address.get("region") or address.get("locality"),
                }
    return None


def extract_final_amount(tender_data: Dict[str, Any]) -> Optional[float]:
    """Фінальна ціна з активного award (ціна переможця після аукціону)."""
    for award in tender_data.get("awards", []):
        if award.get("status") == "active":
            value = award.get("value", {})
            if isinstance(value, dict):
                return value.get("amount")
    return None


def count_participants(tender_data: Dict[str, Any]) -> int:
    """Підрахувати кількість учасників."""
    bids = tender_data.get("bids", [])
    if bids:
        return len(bids)
    
    # Альтернатива - через awards
    awards = tender_data.get("awards", [])
    return len(awards) if awards else 0


def extract_cpv(tender_data: Dict[str, Any]) -> Optional[str]:
    """Витягнути CPV код категорії."""
    items = tender_data.get("items", [])
    if items:
        classification = items[0].get("classification", {})
        return classification.get("id")
    return None


def extract_quantity(tender_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """
    Витягнути кількість та одиницю виміру.
    Лише для тендерів з ОДНИМ item: коли позицій декілька, загальну суму
    не можна коректно розділити між ними (API не дає ціни по позиціях).
    """
    items = tender_data.get("items", [])
    if len(items) != 1:
        return None, None
    quantity = items[0].get("quantity")
    unit = items[0].get("unit") or {}
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return None, None
    if quantity <= 0:
        return None, None
    return quantity, unit.get("name")


def extract_region(tender_data: Dict[str, Any]) -> Optional[str]:
    """Витягнути регіон з даних тендера."""
    items = tender_data.get("items", [])
    if items:
        delivery = items[0].get("deliveryAddress", {})
        region = delivery.get("region")
        if region:
            return region
    
    # Спробувати з замовника
    procuring = tender_data.get("procuringEntity", {})
    address = procuring.get("address", {})
    return address.get("region")


def normalize_tender(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормалізувати дані тендера з Prozorro API.
    
    Args:
        raw_data: Сирі дані з API Prozorro
        
    Returns:
        Нормалізований словник для створення моделі
    """
    amount, currency = extract_amount(raw_data)
    quantity, unit_name = extract_quantity(raw_data)
    unit_price = (amount / quantity) if (amount and quantity) else None
    
    return {
        "prozorro_id": raw_data.get("id", ""),
        "title": raw_data.get("title", "Без назви"),
        "description": raw_data.get("description"),
        "status": raw_data.get("status", "active"),
        "procurement_method": raw_data.get("procurementMethodType"),
        "cpv_code": extract_cpv(raw_data),
        "region": extract_region(raw_data),
        "published_date": parse_date(raw_data.get("dateCreated") or raw_data.get("date")),
        "end_date": parse_date(raw_data.get("tenderPeriod", {}).get("endDate")),
        "amount": amount,
        "final_amount": extract_final_amount(raw_data),
        "currency": currency,
        "quantity": quantity,
        "unit_name": unit_name,
        "unit_price": unit_price,
        "participants_count": count_participants(raw_data),
        "buyer_info": extract_buyer_info(raw_data),
        "winner_info": extract_winner_info(raw_data),
    }
