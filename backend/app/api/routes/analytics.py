"""
AI Prozorro Intelligence - Analytics endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.schemas import (
    AnalyticsResponse, CategoryStat, RegionStat,
    CompanyResponse, BuyerResponse, ChartDataPoint,
)

router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Отримати аналітику по категоріях, регіонах, компаніях та замовниках."""
    
    # Категорії (CPV)
    cat_result = await db.execute(
        select(
            Tender.cpv_code,
            func.count(Tender.id).label("cnt"),
            func.coalesce(func.sum(Tender.amount), 0).label("total"),
        )
        .where(Tender.cpv_code.isnot(None))
        .group_by(Tender.cpv_code)
        .order_by(desc("cnt"))
        .limit(20)
    )
    categories = [
        CategoryStat(cpv_code=row[0], tenders_count=row[1], total_amount=float(row[2]))
        for row in cat_result.all()
    ]
    
    # Регіони
    reg_result = await db.execute(
        select(
            Tender.region,
            func.count(Tender.id).label("cnt"),
            func.coalesce(func.sum(Tender.amount), 0).label("total"),
        )
        .where(Tender.region.isnot(None))
        .group_by(Tender.region)
        .order_by(desc("cnt"))
        .limit(20)
    )
    regions = [
        RegionStat(region=row[0], tenders_count=row[1], total_amount=float(row[2]))
        for row in reg_result.all()
    ]
    
    # Топ компанії
    companies_result = await db.execute(
        select(Company).order_by(desc(Company.wins_count)).limit(10)
    )
    top_companies = [CompanyResponse(
        id=c.id, name=c.name, edrpou=c.edrpou, region=c.region,
        wins_count=c.wins_count, total_amount=c.total_amount, avg_amount=c.avg_amount,
        created_at=c.created_at, updated_at=c.updated_at,
    ) for c in companies_result.scalars().all()]
    
    # Топ замовники
    buyers_result = await db.execute(
        select(Buyer).order_by(desc(Buyer.tenders_count)).limit(10)
    )
    top_buyers = [BuyerResponse(
        id=b.id, name=b.name, edrpou=b.edrpou, region=b.region,
        tenders_count=b.tenders_count, total_amount=b.total_amount,
        avg_participants=b.avg_participants,
        created_at=b.created_at, updated_at=b.updated_at,
    ) for b in buyers_result.scalars().all()]
    
    return AnalyticsResponse(
        categories=categories,
        regions=regions,
        top_companies=top_companies,
        top_buyers=top_buyers,
        price_dynamics=[],
    )
