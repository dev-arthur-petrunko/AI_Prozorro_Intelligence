"""
AI Prozorro Intelligence - Tenders endpoints.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.tender import Tender
from app.models.buyer import Buyer
from app.models.company import Company
from app.schemas import TenderResponse, TenderListResponse, TenderDetailResponse, BuyerResponse, CompanyResponse

router = APIRouter()


@router.get("", response_model=TenderListResponse)
async def get_tenders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    region: Optional[str] = None,
    cpv_code: Optional[str] = None,
    buyer_id: Optional[int] = None,
    winner_id: Optional[int] = None,
    risk_min: Optional[int] = Query(None, ge=0, le=100),
    risk_max: Optional[int] = Query(None, ge=0, le=100),
    sort_by: str = Query("created_at", enum=["created_at", "amount", "risk_score", "published_date"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Отримати список тендерів з фільтрами та пагінацією."""
    
    query = select(Tender)
    count_query = select(func.count(Tender.id))
    
    # Фільтри
    if status:
        query = query.where(Tender.status == status)
        count_query = count_query.where(Tender.status == status)
    if region:
        query = query.where(Tender.region.ilike(f"%{region}%"))
        count_query = count_query.where(Tender.region.ilike(f"%{region}%"))
    if cpv_code:
        query = query.where(Tender.cpv_code.ilike(f"%{cpv_code}%"))
        count_query = count_query.where(Tender.cpv_code.ilike(f"%{cpv_code}%"))
    if buyer_id:
        query = query.where(Tender.buyer_id == buyer_id)
        count_query = count_query.where(Tender.buyer_id == buyer_id)
    if winner_id:
        query = query.where(Tender.winner_id == winner_id)
        count_query = count_query.where(Tender.winner_id == winner_id)
    if risk_min is not None:
        query = query.where(Tender.risk_score >= risk_min)
        count_query = count_query.where(Tender.risk_score >= risk_min)
    if risk_max is not None:
        query = query.where(Tender.risk_score <= risk_max)
        count_query = count_query.where(Tender.risk_score <= risk_max)
    if search:
        query = query.where(Tender.title.ilike(f"%{search}%"))
        count_query = count_query.where(Tender.title.ilike(f"%{search}%"))
    
    # Сортування
    sort_column = getattr(Tender, sort_by, Tender.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Загальна кількість
    total = (await db.execute(count_query)).scalar() or 0
    
    # Пагінація
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    tenders = result.scalars().all()
    
    items = []
    for tender in tenders:
        items.append(TenderResponse(
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
        ))
    
    return TenderListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/{tender_id}", response_model=TenderDetailResponse)
async def get_tender(tender_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати детальну інформацію про тендер."""
    
    result = await db.execute(select(Tender).where(Tender.id == tender_id))
    tender = result.scalar_one_or_none()
    
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не знайдено")
    
    # Отримати замовника
    buyer_resp = None
    if tender.buyer_id:
        buyer_result = await db.execute(select(Buyer).where(Buyer.id == tender.buyer_id))
        buyer = buyer_result.scalar_one_or_none()
        if buyer:
            buyer_resp = BuyerResponse(
                id=buyer.id, name=buyer.name, edrpou=buyer.edrpou,
                region=buyer.region, tenders_count=buyer.tenders_count,
                total_amount=buyer.total_amount, avg_participants=buyer.avg_participants,
                created_at=buyer.created_at, updated_at=buyer.updated_at,
            )
    
    # Отримати переможця
    winner_resp = None
    if tender.winner_id:
        winner_result = await db.execute(select(Company).where(Company.id == tender.winner_id))
        winner = winner_result.scalar_one_or_none()
        if winner:
            winner_resp = CompanyResponse(
                id=winner.id, name=winner.name, edrpou=winner.edrpou,
                region=winner.region, wins_count=winner.wins_count,
                total_amount=winner.total_amount, avg_amount=winner.avg_amount,
                created_at=winner.created_at, updated_at=winner.updated_at,
            )
    
    return TenderDetailResponse(
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
        buyer=buyer_resp,
        winner=winner_resp,
    )
