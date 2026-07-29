"""
AI Prozorro Intelligence - Procurement Risk Engine.
Розраховує Індекс ризику (AI) для кожного тендера з урахуванням типу процедури.
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tender import Tender

logger = logging.getLogger(__name__)


# === Типізація процедур Prozorro (procurementMethodType) ===
# competitive - відкриті торги, конкурентний діалог (справжня конкуренція з е-аукціоном)
# simplified  - спрощена/допорогова закупівля (аукціон не гарантований)
# negotiation - переговорна процедура (законно допускає 1 учасника)
# reporting   - звіт про договір (пряма закупівля, аукціону немає)

PROCEDURE_SIMPLIFIED = {"belowThreshold", "priceQuotation"}
PROCEDURE_REPORTING = {"reporting"}

# Стеля Індексу ризику за типом процедури
PROCEDURE_SCORE_CAP = {
    "competitive": 100,
    "simplified": 50,
    "negotiation": 55,
    "reporting": 55,
}


def get_procedure_type(procurement_method: Optional[str]) -> str:
    """Визначити тип процедури. Невідомий/порожній тип вважаємо competitive."""
    if not procurement_method:
        return "competitive"
    if procurement_method in PROCEDURE_REPORTING:
        return "reporting"
    if procurement_method.startswith("negotiation"):
        return "negotiation"
    if procurement_method in PROCEDURE_SIMPLIFIED:
        return "simplified"
    return "competitive"


# Фактори ризику та їх ваги
RISK_FACTORS = {
    "single_participant": {
        "weight": 25,
        "uk": "Лише один учасник",
        "en": "Single participant",
    },
    "no_price_reduction": {
        "weight": 10,
        "uk": "Відсутність зниження ціни при конкуренції",
        "en": "No price reduction despite competition",
    },
    "repeat_winner": {
        "weight": 25,
        "uk": "Переможець регулярно виграє у цього замовника",
        "en": "Repeat winner for same buyer",
    },
    "bid_rotation": {
        "weight": 20,
        "uk": "Ротація між сталим пулом учасників у замовника",
        "en": "Rotation within a fixed pool of suppliers for the buyer",
    },
    "above_median_amount": {
        "weight": 15,
        "uk": "Сума вище медіани по категорії (останні 12 місяців)",
        "en": "Amount above category median (last 12 months)",
    },
    "short_deadline": {
        "weight": 10,
        "uk": "Короткий термін подачі пропозицій",
        "en": "Short submission deadline",
    },
    "unusual_amount": {
        "weight": 5,
        "uk": "Незвичайно висока сума закупівлі",
        "en": "Unusually high procurement amount",
    },
}


def attention_priority(risk_score: Optional[int], amount: Optional[float]) -> float:
    """
    Пріоритет уваги для сортування топів: risk_score x log10(сума).
    Сам Індекс ризику (0-100) не змінюється - множник впливає лише на порядок,
    щоб копійчані закупівлі з високим score не витісняли мільйонні з середнім.
    """
    score = risk_score or 0
    amt = max(amount or 1.0, 10.0)
    return score * math.log10(amt)


def dedupe_tenders(tenders, limit: int):
    """
    Прибрати візуальні дублі: однакова назва + замовник + сума
    (напр. серія однотипних закупівель) - залишаємо з найвищим ризиком.
    """
    seen = set()
    unique = []
    for t in tenders:
        key = (t.title.strip().lower(), t.buyer_id, t.amount)
        if key in seen:
            continue
        seen.add(key)
        unique.append(t)
        if len(unique) >= limit:
            break
    return unique


def top_by_attention(tenders, limit: int):
    """
    Відсортувати кандидатів за пріоритетом уваги (risk_score x log10(сума))
    і прибрати візуальні дублі. Спільна логіка топів дашборду та AI-аналізу.
    """
    ranked = sorted(
        tenders,
        key=lambda t: attention_priority(t.risk_score, t.amount),
        reverse=True,
    )
    return dedupe_tenders(ranked, limit=limit)


async def check_single_participant(tender: Tender) -> bool:
    """Перевірка: лише один учасник (лише для competitive)."""
    return tender.participants_count <= 1


async def check_no_price_reduction(tender: Tender) -> bool:
    """
    Перевірка: реальна відсутність торгу - 2+ учасники, але фінальна ціна
    не знизилась відносно очікуваної (факт з даних award, не евристика).
    """
    if tender.participants_count < 2:
        return False
    if not tender.amount or not tender.final_amount:
        return False
    return tender.final_amount >= tender.amount * 0.995


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


async def check_bid_rotation(tender: Tender, session: AsyncSession) -> bool:
    """
    Перевірка: ротація між сталим пулом учасників - ті самі 2-3 компанії
    по черзі виграють у одного замовника (ознака імітації конкуренції).
    Наближення на наявних даних: у замовника 4+ тендерів з переможцями,
    але всі перемоги розподілені між 2-3 компаніями, і кожна виграла 2+ разів.
    """
    if not tender.winner_id or not tender.buyer_id:
        return False

    result = await session.execute(
        select(Tender.winner_id, func.count(Tender.id))
        .where(
            Tender.buyer_id == tender.buyer_id,
            Tender.winner_id.isnot(None),
        )
        .group_by(Tender.winner_id)
    )
    wins_by_company = {row[0]: row[1] for row in result.all()}

    total_awarded = sum(wins_by_company.values())
    distinct_winners = len(wins_by_company)

    return (
        total_awarded >= 4
        and 2 <= distinct_winners <= 3
        and all(c >= 2 for c in wins_by_company.values())
        and tender.winner_id in wins_by_company
    )


async def check_above_median_amount(tender: Tender, session: AsyncSession) -> bool:
    """
    Перевірка: сума > 150% медіани по тій же CPV-категорії за останні
    12 місяців (медіана стійкіша до викидів, вікно знижує інфляційне спотворення).
    """
    if not tender.amount or not tender.cpv_code:
        return False
    
    window_start = datetime.utcnow() - timedelta(days=365)
    result = await session.execute(
        select(func.percentile_cont(0.5).within_group(Tender.amount)).where(
            Tender.cpv_code == tender.cpv_code,
            Tender.amount.isnot(None),
            Tender.published_date >= window_start,
            Tender.id != tender.id,
        )
    )
    median_amount = result.scalar()
    
    if median_amount and median_amount > 0:
        return tender.amount > float(median_amount) * 1.5
    return False


async def check_short_deadline(tender: Tender) -> bool:
    """Перевірка: короткий термін подачі (лише для competitive)."""
    if not tender.published_date or not tender.end_date:
        return False
    
    delta = tender.end_date - tender.published_date
    return delta.days <= 3  # Менше 3 днів


async def check_unusual_amount(tender: Tender, session: AsyncSession) -> bool:
    """Перевірка: незвичайно висока сума (> 3x медіани по всій базі)."""
    if not tender.amount:
        return False
    
    result = await session.execute(
        select(func.percentile_cont(0.5).within_group(Tender.amount)).where(
            Tender.amount.isnot(None)
        )
    )
    median_all = result.scalar()
    
    if median_all and median_all > 0:
        return tender.amount > float(median_all) * 3
    
    # Fallback: сума > 10M UAH
    return tender.amount > 10_000_000


async def calculate_risk_score(tender: Tender, session: AsyncSession) -> Tuple[int, List[Dict]]:
    """
    Розрахувати Індекс ризику для тендера з типізацією процедури.
    
    Returns:
        Tuple[score (0-100, зі стелею за типом процедури), triggered_factors]
    """
    score = 0
    triggered_factors = []
    
    procedure_type = get_procedure_type(tender.procurement_method)

    # Фактори, спільні для всіх типів процедур
    checks = [
        ("repeat_winner", check_repeat_winner(tender, session)),
        ("bid_rotation", check_bid_rotation(tender, session)),
        ("above_median_amount", check_above_median_amount(tender, session)),
    ]

    # Фактори конкуренції - лише там, де конкуренція передбачена процедурою:
    # simplified/negotiation/reporting законно допускають 1 учасника,
    # а етапу подачі пропозицій у simplified/reporting немає
    if procedure_type == "competitive":
        checks = [
            ("single_participant", check_single_participant(tender)),
            ("no_price_reduction", check_no_price_reduction(tender)),
            ("short_deadline", check_short_deadline(tender)),
        ] + checks
    elif procedure_type == "negotiation":
        # Для переговорної 1 учасник - норма, але відсутність зниження
        # не застосовна за визначенням; короткий термін теж не має сенсу
        pass
    
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
    
    # Стеля за типом процедури + обмеження 0-100
    cap = PROCEDURE_SCORE_CAP.get(procedure_type, 100)
    score = min(cap, max(0, score))
    
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
