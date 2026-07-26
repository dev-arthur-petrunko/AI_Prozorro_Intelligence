"""
AI Prozorro Intelligence - Dashboard endpoint.
"""

import json
from datetime import datetime, date

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.models.analytics import AnalyticsSnapshot
from app.schemas import (
    DashboardResponse, DashboardKPI, ChartDataPoint, TenderResponse
)

router = APIRouter()


def _tender_to_response(tender: Tender) -> TenderResponse:
    """Серіалізація тендера у відповідь API."""
    return TenderResponse(
        id=tender.id,
        prozorro_id=tender.prozorro_id,
        title=tender.title,
        description=tender.description,
        status=tender.status,
        cpv_code=tender.cpv_code,
        region=tender.region,
        published_date=tender.published_date,
        end_date=tender.end_date,
        amount=tender.amount,
        currency=tender.currency,
        participants_count=tender.participants_count,
        buyer_id=tender.buyer_id,
        winner_id=tender.winner_id,
        risk_score=tender.risk_score,
        ai_analysis=tender.ai_analysis,
        risk_factors=tender.risk_factors,
        created_at=tender.created_at,
        updated_at=tender.updated_at,
    )


def _dedupe_tenders(tenders, limit: int):
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


@router.get("", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Отримати дані для головної сторінки дашборду."""
    
    # KPI
    total_tenders = (await db.execute(select(func.count(Tender.id)))).scalar() or 0
    suspicious = (await db.execute(
        select(func.count(Tender.id)).where(Tender.risk_score > 60)
    )).scalar() or 0
    total_companies = (await db.execute(select(func.count(Company.id)))).scalar() or 0
    total_buyers = (await db.execute(select(func.count(Buyer.id)))).scalar() or 0
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    # Обсяг сьогодні - за датою ПУБЛІКАЦІЇ тендера в Prozorro (а не датою імпорту в базу),
    # інакше старі тендери, завантажені сьогодні, завищують суму
    today_volume = (await db.execute(
        select(func.coalesce(func.sum(Tender.amount), 0))
        .where(Tender.published_date >= today_start)
    )).scalar() or 0
    today_new = (await db.execute(
        select(func.count(Tender.id)).where(Tender.published_date >= today_start)
    )).scalar() or 0

    kpi = DashboardKPI(
        total_tenders=total_tenders,
        suspicious_tenders=suspicious,
        total_companies=total_companies,
        total_buyers=total_buyers,
        today_volume=float(today_volume),
        today_new=today_new,
    )

    # Chart data з аналітичного знімку
    chart_data = []
    snapshot = (await db.execute(
        select(AnalyticsSnapshot).order_by(desc(AnalyticsSnapshot.snapshot_date)).limit(1)
    )).scalar_one_or_none()
    
    if snapshot and snapshot.data_json:
        try:
            raw_chart = json.loads(snapshot.data_json)
            chart_data = [ChartDataPoint(**point) for point in raw_chart]
        except (json.JSONDecodeError, TypeError):
            pass

    # Топ підозрілі ЗАВЕРШЕНІ тендери (статус complete/unsuccessful/cancelled)
    suspicious_result = await db.execute(
        select(Tender)
        .where(
            Tender.risk_score > 60,
            Tender.status.in_(["complete", "unsuccessful", "cancelled"]),
        )
        .order_by(desc(Tender.risk_score))
        .limit(40)
    )
    suspicious_tenders = [
        _tender_to_response(t)
        for t in _dedupe_tenders(suspicious_result.scalars().all(), limit=10)
    ]

    # Топ підозрілі АКТИВНІ тендери (ще відкриті: active.*)
    active_result = await db.execute(
        select(Tender)
        .where(
            Tender.risk_score > 60,
            Tender.status.like("active%"),
        )
        .order_by(desc(Tender.risk_score))
        .limit(40)
    )
    active_suspicious_tenders = [
        _tender_to_response(t)
        for t in _dedupe_tenders(active_result.scalars().all(), limit=10)
    ]

    # Останні тендери (без візуальних дублів)
    recent_result = await db.execute(
        select(Tender).order_by(desc(Tender.created_at)).limit(40)
    )
    recent_tenders = [
        _tender_to_response(t)
        for t in _dedupe_tenders(recent_result.scalars().all(), limit=10)
    ]

    return DashboardResponse(
        kpi=kpi,
        chart_data=chart_data,
        suspicious_tenders=suspicious_tenders,
        active_suspicious_tenders=active_suspicious_tenders,
        recent_tenders=recent_tenders,
    )
