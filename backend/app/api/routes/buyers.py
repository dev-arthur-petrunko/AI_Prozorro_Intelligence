"""
AI Prozorro Intelligence - Buyers endpoints.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.buyer import Buyer
from app.models.tender import Tender
from app.schemas import BuyerResponse, BuyerListResponse, BuyerDetailResponse, TenderResponse

router = APIRouter()


@router.get("", response_model=BuyerListResponse)
async def get_buyers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("tenders_count", enum=["tenders_count", "total_amount", "name"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: AsyncSession = Depends(get_db),
):
    """Отримати список замовників."""
    query = select(Buyer)
    count_query = select(func.count(Buyer.id))
    
    if search:
        query = query.where(Buyer.name.ilike(f"%{search}%"))
        count_query = count_query.where(Buyer.name.ilike(f"%{search}%"))
    
    sort_column = getattr(Buyer, sort_by, Buyer.tenders_count)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    buyers = result.scalars().all()
    
    items = [BuyerResponse(
        id=b.id, name=b.name, edrpou=b.edrpou, region=b.region,
        tenders_count=b.tenders_count, total_amount=b.total_amount,
        avg_participants=b.avg_participants,
        created_at=b.created_at, updated_at=b.updated_at,
    ) for b in buyers]
    
    return BuyerListResponse(
        items=items, total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/{buyer_id}", response_model=BuyerDetailResponse)
async def get_buyer(buyer_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати детальну інформацію про замовника."""
    result = await db.execute(select(Buyer).where(Buyer.id == buyer_id))
    buyer = result.scalar_one_or_none()
    
    if not buyer:
        raise HTTPException(status_code=404, detail="Замовника не знайдено")
    
    tenders_result = await db.execute(
        select(Tender).where(Tender.buyer_id == buyer.id)
        .order_by(desc(Tender.created_at)).limit(20)
    )
    recent_tenders = [TenderResponse(
        id=t.id, prozorro_id=t.prozorro_id, title=t.title, description=t.description,
        status=t.status, cpv_code=t.cpv_code, region=t.region,
        published_date=t.published_date, end_date=t.end_date, amount=t.amount,
        currency=t.currency, participants_count=t.participants_count,
        buyer_id=t.buyer_id, winner_id=t.winner_id, risk_score=t.risk_score,
        ai_analysis=t.ai_analysis, risk_factors=t.risk_factors,
        created_at=t.created_at, updated_at=t.updated_at,
    ) for t in tenders_result.scalars().all()]
    
    return BuyerDetailResponse(
        id=buyer.id, name=buyer.name, edrpou=buyer.edrpou, region=buyer.region,
        tenders_count=buyer.tenders_count, total_amount=buyer.total_amount,
        avg_participants=buyer.avg_participants,
        created_at=buyer.created_at, updated_at=buyer.updated_at,
        recent_tenders=recent_tenders,
    )
