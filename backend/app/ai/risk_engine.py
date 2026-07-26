"""
AI Prozorro Intelligence - Procurement Risk Engine.
Розраховує оцінку ризику для кожного тендера.
"""

import json
import logging
from typing import List, Dict, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tender import Tender
from app.models.company import Company

logger = logging.getLogger(__name__)


# Фактори ризику та їх ваги
RISK_FACTORS = {
    "single_participant": {
        "weight": 30,
        "uk": "Лише один учасник",
        "en": "Single participant",
    },
    "repeat_winner": {
        "weight": 20,
        "uk": "Переможець регулярно виграє у цього замовника",
        "en": "Repeat winner for same buyer",
    },
    "above_avg_amount": {
        "weight": 15,
        "uk": "Сума вище середньої по категорії",
        "en": "Amount above category average",
    },
    "minimal_price_reduction": {
        "weight": 15,
        "uk": "Мінімальне зниження ціни на аукціоні",
        "en": "Minimal price reduction at auction",
    },
    "short_deadline": {
        "weight": 10,
        "uk": "Короткий термін подачі пропозицій",
        "en": "Short submission deadline",
    },
    "unusual_amount": {
        "weight": 10,
        "uk": "Незвичайно висока сума закупівлі",
        "en": "Unusually high procurement amount",
    },
}


async def check_single_participant(tender: Tender) -> bool:
    """Перевірка: лише один учасник."""
    return tender.participants_count <= 1


async def check_repeat_winner(tender: Tender, session: AsyncSession) -> bool:
    """Перевірка: переможець регулярно виграє у цього замовника."""
    if not tender.winner_id or not tender.buyer_id:
        return False
    
    result = await session.execute(
        select(func.count(Tender.id)).where(
            Tender.buyer_id == tender.buyer_id,
            Tender.winner_id == tender.winner_id,
            Tender.id != tender.id,
        )
    )
    repeat_count = result.scalar() or 0
    return repeat_count >= 3  # 3+ перемоги у одного замовника


async def check_above_avg_amount(tender: Tender, session: AsyncSession) -> bool:
    """Перевірка: сума вище середньої по категорії."""
    if not tender.amount or not tender.cpv_code:
        return False
    
    result = await session.execute(
        select(func.avg(Tender.amount)).where(
            Tender.cpv_code == tender.cpv_code,
            Tender.amount.isnot(None),
        )
    )
    avg_amount = result.scalar()
    
    if avg_amount and avg_amount > 0:
        return tender.amount > avg_amount * 1.5  # На 50%+ вище середньої
    return False


async def check_minimal_price_reduction(tender: Tender) -> bool:
    """Перевірка: мінімальне зниження ціни (placeholder - потребує даних аукціону)."""
    # В повній версії порівнювати стартову та фінальну ціну
    # Поки використовуємо евристику: 1 учасник = немає зниження
    return tender.participants_count == 1 and tender.amount is not None


async def check_short_deadline(tender: Tender) -> bool:
    """Перевірка: короткий термін подачі."""
    if not tender.published_date or not tender.end_date:
        return False
    
    delta = tender.end_date - tender.published_date
    return delta.days <= 3  # Менше 3 днів


async def check_unusual_amount(tender: Tender, session: AsyncSession) -> bool:
    """Перевірка: незвичайно висока сума."""
    if not tender.amount:
        return False
    
    # Перевіряємо чи сума значно вище середньої
    result = await session.execute(
        select(func.avg(Tender.amount)).where(Tender.amount.isnot(None))
    )
    avg_all = result.scalar()
    
    if avg_all and avg_all > 0:
        return tender.amount > avg_all * 3  # 3x вище середньої
    
    # Fallback: сума > 10M UAH
    return tender.amount > 10_000_000


async def calculate_risk_score(tender: Tender, session: AsyncSession) -> Tuple[int, List[Dict]]:
    """
    Розрахувати оцінку ризику для тендера.
    
    Returns:
        Tuple[score (0-100), triggered_factors]
    """
    score = 0
    triggered_factors = []
    
    # Перевірка кожного фактора
    checks = [
        ("single_participant", check_single_participant(tender)),
        ("repeat_winner", check_repeat_winner(tender, session)),
        ("above_avg_amount", check_above_avg_amount(tender, session)),
        ("minimal_price_reduction", check_minimal_price_reduction(tender)),
        ("short_deadline", check_short_deadline(tender)),
    ]
    
    for factor_key, check_coro in checks:
        try:
            result = await check_coro
            if result:
                factor = RISK_FACTORS[factor_key]
                score += factor["weight"]
                triggered_factors.append({
                    "key": factor_key,
                    "weight": factor["weight"],
                    "description_uk": factor["uk"],
                    "description_en": factor["en"],
                })
        except Exception as e:
            logger.warning(f"Помилка перевірки фактора {factor_key}: {e}")
    
    # Додаткова перевірка unusual_amount (може не працювати без percentile)
    try:
        if await check_unusual_amount(tender, session):
            factor = RISK_FACTORS["unusual_amount"]
            score += factor["weight"]
            triggered_factors.append({
                "key": "unusual_amount",
                "weight": factor["weight"],
                "description_uk": factor["uk"],
                "description_en": factor["en"],
            })
    except Exception:
        pass
    
    # Обмеження 0-100
    score = min(100, max(0, score))
    
    return score, triggered_factors


async def analyze_tender_risk(tender: Tender, session: AsyncSession) -> Tuple[int, str]:
    """
    Повний аналіз ризику тендера.
    
    Returns:
        Tuple[risk_score, risk_factors_json]
    """
    score, factors = await calculate_risk_score(tender, session)
    factors_json = json.dumps(factors, ensure_ascii=False)
    
    return score, factors_json
