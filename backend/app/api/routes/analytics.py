"""
AI Prozorro Intelligence - Analytics endpoints.
"""

from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.analytics.cpv_catalog import cpv_name
from app.schemas import (
    AnalyticsResponse, CategoryStat, RegionStat,
    CompanyResponse, BuyerResponse,
)

router = APIRouter()

# Знеособлені постачальники Prozorro (оборонні закупівлі приховують переможця
# під плейсхолдером "Оборонний постачальник" з фіктивним ЄДРПОУ) -
# це агрегат різних реальних компаній, тому в топах він не показується
ANONYMIZED_EDRPOUS = ("88888888", "00000000")


def _exclude_anonymized(query):
    """Виключити знеособлених постачальників з рейтингу компаній."""
    return query.where(
        or_(Company.edrpou.is_(None), Company.edrpou.notin_(ANONYMIZED_EDRPOUS))
    )


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    days: Optional[int] = Query(None, ge=1, le=365, description="Період у днях (7/30/90), без значення - за весь час"),
    db: AsyncSession = Depends(get_db),
):
    """Отримати аналітику по категоріях, регіонах, компаніях та замовниках."""

    # Відсічення за періодом (за датою публікації тендера)
    period_start = None
    if days:
        period_start = datetime.combine(date.today() - timedelta(days=days - 1), datetime.min.time())

    def with_period(query):
        """Додати фільтр періоду до запиту (якщо заданий)."""
        if period_start is not None:
            return query.where(Tender.published_date >= period_start)
        return query

    # Категорії (CPV) з розшифровкою назви за ДК 021:2015
    cat_result = await db.execute(
        with_period(
            select(
                Tender.cpv_code,
                func.count(Tender.id).label("cnt"),
                func.coalesce(func.sum(Tender.amount), 0).label("total"),
            )
            .where(Tender.cpv_code.isnot(None))
        )
        .group_by(Tender.cpv_code)
        .order_by(desc("cnt"))
        .limit(20)
    )
    categories = [
        CategoryStat(
            cpv_code=row[0],
            name=cpv_name(row[0]),
            tenders_count=row[1],
            total_amount=float(row[2]),
        )
        for row in cat_result.all()
    ]
    
    # Регіони (без ліміту - показуємо всі області України;
    # відсіюємо записи з порожньою назвою регіону).
    # total_amount = оголошена очікувана вартість; contracted_amount =
    # фактично законтрактована ціна переможців (final_amount)
    reg_result = await db.execute(
        with_period(
            select(
                Tender.region,
                func.count(Tender.id).label("cnt"),
                func.coalesce(func.sum(Tender.amount), 0).label("total"),
                func.coalesce(func.sum(Tender.final_amount), 0).label("contracted"),
            )
            .where(Tender.region.isnot(None), Tender.region != "")
        )
        .group_by(Tender.region)
        .order_by(desc("cnt"))
    )
    regions = [
        RegionStat(
            region=row[0],
            tenders_count=row[1],
            total_amount=float(row[2]),
            contracted_amount=float(row[3]),
        )
        for row in reg_result.all()
    ]
    
    # Топ компанії та замовники: без періоду - з передрахованої статистики,
    # з періодом - агрегація по тендерах за вибраний час
    if period_start is None:
        companies_result = await db.execute(
            _exclude_anonymized(
                select(Company).order_by(desc(Company.wins_count))
            ).limit(10)
        )
        top_companies = [CompanyResponse(
            id=c.id, name=c.name, edrpou=c.edrpou, region=c.region,
            wins_count=c.wins_count, total_amount=c.total_amount, avg_amount=c.avg_amount,
            created_at=c.created_at, updated_at=c.updated_at,
        ) for c in companies_result.scalars().all()]

        buyers_result = await db.execute(
            select(Buyer).order_by(desc(Buyer.tenders_count)).limit(10)
        )
        top_buyers = [BuyerResponse(
            id=b.id, name=b.name, edrpou=b.edrpou, region=b.region,
            tenders_count=b.tenders_count, total_amount=b.total_amount,
            avg_participants=b.avg_participants,
            created_at=b.created_at, updated_at=b.updated_at,
        ) for b in buyers_result.scalars().all()]
    else:
        comp_agg = await db.execute(
            _exclude_anonymized(
                with_period(
                    select(
                        Company,
                        func.count(Tender.id).label("wins"),
                        func.coalesce(func.sum(Tender.amount), 0).label("total"),
                        func.coalesce(func.avg(Tender.amount), 0).label("avg"),
                    )
                    .join(Tender, Tender.winner_id == Company.id)
                )
            )
            .group_by(Company.id)
            .order_by(desc("wins"))
            .limit(10)
        )
        top_companies = [CompanyResponse(
            id=c.id, name=c.name, edrpou=c.edrpou, region=c.region,
            wins_count=row_wins, total_amount=float(row_total), avg_amount=float(row_avg),
            created_at=c.created_at, updated_at=c.updated_at,
        ) for c, row_wins, row_total, row_avg in comp_agg.all()]

        buyer_agg = await db.execute(
            with_period(
                select(
                    Buyer,
                    func.count(Tender.id).label("cnt"),
                    func.coalesce(func.sum(Tender.amount), 0).label("total"),
                    func.coalesce(func.avg(Tender.participants_count), 0).label("avg_p"),
                )
                .join(Tender, Tender.buyer_id == Buyer.id)
            )
            .group_by(Buyer.id)
            .order_by(desc("cnt"))
            .limit(10)
        )
        top_buyers = [BuyerResponse(
            id=b.id, name=b.name, edrpou=b.edrpou, region=b.region,
            tenders_count=row_cnt, total_amount=float(row_total),
            avg_participants=float(row_avg_p),
            created_at=b.created_at, updated_at=b.updated_at,
        ) for b, row_cnt, row_total, row_avg_p in buyer_agg.all()]

    # Час останнього оновлення даних
    last_updated = (await db.execute(
        select(func.max(Tender.updated_at))
    )).scalar()

    return AnalyticsResponse(
        categories=categories,
        regions=regions,
        top_companies=top_companies,
        top_buyers=top_buyers,
        price_dynamics=[],
        last_updated=last_updated,
    )
