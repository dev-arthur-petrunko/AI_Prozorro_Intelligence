"""
AI Prozorro Intelligence - Companies endpoints.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.company import Company
from app.models.tender import Tender
from app.schemas import CompanyResponse, CompanyListResponse, CompanyDetailResponse, TenderResponse

router = APIRouter()


@router.get("", response_model=CompanyListResponse)
async def get_companies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("wins_count", enum=["wins_count", "total_amount", "name"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: AsyncSession = Depends(get_db),
):
    """Отримати список компаній."""
    query = select(Company)
    count_query = select(func.count(Company.id))
    
    if search:
        query = query.where(Company.name.ilike(f"%{search}%"))
        count_query = count_query.where(Company.name.ilike(f"%{search}%"))
    
    sort_column = getattr(Company, sort_by, Company.wins_count)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    companies = result.scalars().all()
    
    items = [CompanyResponse(
        id=c.id, name=c.name, edrpou=c.edrpou, region=c.region,
        wins_count=c.wins_count, total_amount=c.total_amount, avg_amount=c.avg_amount,
        created_at=c.created_at, updated_at=c.updated_at,
    ) for c in companies]
    
    return CompanyListResponse(
        items=items, total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/{company_id}", response_model=CompanyDetailResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати детальну інформацію про компанію."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Компанію не знайдено")
    
    # Останні тендери компанії
    tenders_result = await db.execute(
        select(Tender).where(Tender.winner_id == company.id)
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
    
    return CompanyDetailResponse(
        id=company.id, name=company.name, edrpou=company.edrpou, region=company.region,
        wins_count=company.wins_count, total_amount=company.total_amount, avg_amount=company.avg_amount,
        created_at=company.created_at, updated_at=company.updated_at,
        recent_tenders=recent_tenders,
    )
