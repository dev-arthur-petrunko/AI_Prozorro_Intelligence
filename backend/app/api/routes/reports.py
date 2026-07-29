"""
AI Prozorro Intelligence - Daily Report endpoint.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.config import settings
from app.models.tender import Tender
from app.schemas import DailyReportResponse, TenderResponse

router = APIRouter()


@router.get("", response_model=DailyReportResponse)
async def get_daily_report(db: AsyncSession = Depends(get_db)):
    """Отримати щоденний звіт для Telegram та Dashboard."""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Нові тендери за сьогодні
    new_count = (await db.execute(
        select(func.count(Tender.id)).where(Tender.created_at >= today_start)
    )).scalar() or 0
    
    # Якщо сьогодні даних ще немає - звіт за останній день з даними
    if new_count == 0:
        last_created = (await db.execute(
            select(func.max(Tender.created_at))
        )).scalar()
        if last_created:
            today = last_created.date()
            today_start = datetime.combine(today, datetime.min.time())
            new_count = (await db.execute(
                select(func.count(Tender.id)).where(Tender.created_at >= today_start)
            )).scalar() or 0
    
    # Підозрілі
    suspicious = (await db.execute(
        select(func.count(Tender.id)).where(
            Tender.risk_score >= settings.high_risk_threshold,
            Tender.created_at >= today_start,
        )
    )).scalar() or 0
    
    # Найвищий Risk Score
    highest_risk = (await db.execute(
        select(func.max(Tender.risk_score))
    )).scalar() or 0
    
    # Найбільша закупівля
    largest_amount = (await db.execute(
        select(func.max(Tender.amount)).where(Tender.created_at >= today_start)
    )).scalar() or 0
    
    # Топ категорія
    top_cat = await db.execute(
        select(Tender.cpv_code, func.count(Tender.id).label("cnt"))
        .where(Tender.cpv_code.isnot(None), Tender.created_at >= today_start)
        .group_by(Tender.cpv_code)
        .order_by(desc("cnt"))
        .limit(1)
    )
    top_cat_row = top_cat.first()
    top_category = top_cat_row[0] if top_cat_row else None
    
    # Топ регіон
    top_reg = await db.execute(
        select(Tender.region, func.count(Tender.id).label("cnt"))
        .where(Tender.region.isnot(None), Tender.created_at >= today_start)
        .group_by(Tender.region)
        .order_by(desc("cnt"))
        .limit(1)
    )
    top_reg_row = top_reg.first()
    top_region = top_reg_row[0] if top_reg_row else None
    
    # Підозрілі тендери (за цей же день; якщо немає - топ загалом)
    susp_result = await db.execute(
        select(Tender)
        .where(Tender.risk_score >= settings.high_risk_threshold, Tender.created_at >= today_start)
        .order_by(desc(Tender.risk_score))
        .limit(5)
    )
    susp_list = susp_result.scalars().all()
    if not susp_list:
        susp_result = await db.execute(
            select(Tender)
            .where(Tender.risk_score >= settings.high_risk_threshold)
            .order_by(desc(Tender.risk_score))
            .limit(5)
        )
        susp_list = susp_result.scalars().all()
        # Лічильник узгоджуємо зі списком, що показується
        suspicious = (await db.execute(
            select(func.count(Tender.id)).where(Tender.risk_score >= settings.high_risk_threshold)
        )).scalar() or 0
    suspicious_tenders = [TenderResponse(
        id=t.id, prozorro_id=t.prozorro_id, title=t.title, description=t.description,
        status=t.status, cpv_code=t.cpv_code, region=t.region,
        published_date=t.published_date, end_date=t.end_date, amount=t.amount,
        currency=t.currency, participants_count=t.participants_count,
        buyer_id=t.buyer_id, winner_id=t.winner_id, risk_score=t.risk_score,
        ai_analysis=t.ai_analysis, risk_factors=t.risk_factors,
        created_at=t.created_at, updated_at=t.updated_at,
    ) for t in susp_list]
    
    return DailyReportResponse(
        date=today.isoformat(),
        total_new_tenders=new_count,
        suspicious_count=suspicious,
        highest_risk_score=highest_risk or 0,
        largest_tender_amount=float(largest_amount or 0),
        top_category=top_category,
        top_region=top_region,
        suspicious_tenders=suspicious_tenders,
    )
