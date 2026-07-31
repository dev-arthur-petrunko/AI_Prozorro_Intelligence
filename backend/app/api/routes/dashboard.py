"""
AI Prozorro Intelligence - Dashboard endpoint.
"""

from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.ai.risk_engine import top_by_attention, dedupe_tenders
from app.schemas import (
    DashboardResponse, DashboardKPI, ChartDataPoint, TenderResponse, RiskBucket
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
    """Прибрати візуальні дублі (спільна логіка у risk_engine)."""
    return dedupe_tenders(tenders, limit=limit)


def _top_by_attention(tenders, limit: int):
    """Топ за пріоритетом уваги (спільна логіка у risk_engine)."""
    return top_by_attention(tenders, limit=limit)


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    days: Optional[int] = Query(None, ge=1, le=365, description="Період у днях (7/30/90/180), без значення - за весь час"),
    db: AsyncSession = Depends(get_db),
):
    """Отримати дані для головної сторінки дашборду."""

    # Відсічення за періодом (за датою публікації тендера)
    period_start = None
    if days:
        period_start = datetime.combine(date.today() - timedelta(days=days - 1), datetime.min.time())

    def with_period(query):
        """Додати фільтр періоду до запиту (якщо заданий)."""
        if period_start is not None:
            return query.where(Tender.published_date >= period_start)
        return query

    # KPI
    total_tenders = (await db.execute(
        with_period(select(func.count(Tender.id)))
    )).scalar() or 0
    suspicious = (await db.execute(
        with_period(select(func.count(Tender.id)).where(Tender.risk_score >= settings.high_risk_threshold))
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

    # Економія на торгах: очікувана мінус фінальна ціна по завершених
    # конкурентних тендерах (тільки де фінальна реально нижча)
    not_reporting = (Tender.procurement_method.is_(None)) | (Tender.procurement_method != "reporting")
    savings_total = (await db.execute(
        with_period(
            select(func.coalesce(func.sum(Tender.amount - Tender.final_amount), 0))
            .where(
                Tender.status == "complete",
                Tender.final_amount.isnot(None),
                Tender.final_amount < Tender.amount,
                not_reporting,
            )
        )
    )).scalar() or 0

    # Частка конкурентних тендерів з одним учасником (серед тих, де учасники вже відомі)
    single_row = (await db.execute(
        with_period(
            select(
                func.sum(case((Tender.participants_count == 1, 1), else_=0)),
                func.count(Tender.id),
            )
            .where(Tender.participants_count >= 1, not_reporting)
        )
    )).first()
    single_cnt = int(single_row[0] or 0) if single_row else 0
    single_base = int(single_row[1] or 0) if single_row else 0
    single_participant_pct = round(single_cnt / single_base * 100, 1) if single_base else 0.0

    kpi = DashboardKPI(
        total_tenders=total_tenders,
        suspicious_tenders=suspicious,
        total_companies=total_companies,
        total_buyers=total_buyers,
        today_volume=float(today_volume),
        today_new=today_new,
        savings_total=float(savings_total),
        single_participant_pct=single_participant_pct,
    )

    # Дані графіка рахуємо наживо з БД одним групованим запитом
    # (а не зі снапшоту: інший інстанс зі старим кодом може перезаписувати
    # снапшот без поділу на конкурентні/reporting)
    chart_days = days if days else 30
    chart_start = datetime.combine(date.today() - timedelta(days=chart_days - 1), datetime.min.time())
    is_reporting = case((Tender.procurement_method == "reporting", 1), else_=0)
    is_high_risk = case((Tender.risk_score >= settings.high_risk_threshold, 1), else_=0)
    amount0 = func.coalesce(Tender.amount, 0)
    chart_rows = (await db.execute(
        select(
            func.date(Tender.published_date).label("d"),
            func.sum(1 - is_reporting),                    # конкурентні (шт)
            func.sum(is_reporting),                        # звіти (шт)
            func.sum((1 - is_reporting) * amount0),        # конкурентні (грн)
            func.sum(is_reporting * amount0),              # звіти (грн)
            func.sum(is_high_risk),                        # з високим індексом ризику (шт)
        )
        .where(Tender.published_date >= chart_start)
        .group_by(func.date(Tender.published_date))
    )).all()
    by_date = {str(r[0]): r for r in chart_rows}

    chart_data = []
    for i in range(chart_days):
        d = date.today() - timedelta(days=chart_days - 1 - i)
        r = by_date.get(d.isoformat())
        chart_data.append(ChartDataPoint(
            date=d.isoformat(),
            tenders_count=int(r[1] or 0) if r else 0,
            reports_count=int(r[2] or 0) if r else 0,
            tenders_volume=float(r[3] or 0) if r else 0.0,
            reports_volume=float(r[4] or 0) if r else 0.0,
            high_risk_count=int(r[5] or 0) if r else 0,
            volume=float((r[3] or 0) + (r[4] or 0)) if r else 0.0,
        ))

    # Топ за індексом ризику - ЗАВЕРШЕНІ (complete/unsuccessful/cancelled).
    # Жорсткий фільтр лише один: сума >= 10 тис. грн (мікрозакупівлі - шум).
    # Reporting-звіти (прямі договори) виключаємо: один учасник там - норма
    min_amount = settings.dashboard_suspicious_min_amount
    suspicious_result = await db.execute(
        with_period(
            select(Tender)
            .where(
                Tender.risk_score >= settings.high_risk_threshold,
                Tender.status.in_(["complete", "unsuccessful", "cancelled"]),
                Tender.amount >= min_amount,
                not_reporting,
            )
        )
        .order_by(desc(Tender.risk_score), desc(Tender.amount))
        .limit(40)
    )
    suspicious_completed = _top_by_attention(suspicious_result.scalars().all(), limit=10)

    # Доповнення: завершених з високим індексом може бути мало (після чесного
    # скорингу) - добираємо до 10 позицій каскадом строго за рівнем індексу:
    # немає більше 60 - беремо 55, немає 55 - 50 і так далі (до порогу >= 40)
    if len(suspicious_completed) < 10:
        taken_ids = [t.id for t in suspicious_completed]
        fallback_result = await db.execute(
            with_period(
                select(Tender)
                .where(
                    Tender.risk_score >= settings.dashboard_suspicious_fallback_risk,
                    Tender.risk_score < settings.high_risk_threshold,
                    Tender.status.in_(["complete", "unsuccessful", "cancelled"]),
                    Tender.amount >= min_amount,
                    not_reporting,
                    Tender.id.notin_(taken_ids) if taken_ids else True,
                )
            )
            .order_by(desc(Tender.risk_score), desc(Tender.amount))
            .limit(10 - len(suspicious_completed))
        )
        suspicious_completed.extend(fallback_result.scalars().all())

    suspicious_tenders = [_tender_to_response(t) for t in suspicious_completed]

    # Топ підозрілі АКТИВНІ тендери (ще відкриті: active.*).
    # Поріг ризику нижчий (50), бо активні тендери часто ще не повністю
    # оброблені AI-скорингом і risk_score > 60 давав майже порожній список
    active_result = await db.execute(
        with_period(
            select(Tender)
            .where(
                Tender.risk_score >= settings.dashboard_active_risk_min,
                Tender.status.like("active%"),
                not_reporting,
            )
        )
        .order_by(desc(Tender.risk_score), desc(Tender.amount))
        .limit(40)
    )
    active_suspicious_tenders = [
        _tender_to_response(t)
        for t in _top_by_attention(active_result.scalars().all(), limit=10)
    ]

    # Останні тендери (без візуальних дублів)
    recent_result = await db.execute(
        with_period(select(Tender)).order_by(desc(Tender.created_at)).limit(40)
    )
    recent_tenders = [
        _tender_to_response(t)
        for t in _dedupe_tenders(recent_result.scalars().all(), limit=10)
    ]

    # Розподіл Індексу ризику по зонах шкали (одним запитом)
    dist_row = (await db.execute(
        with_period(
            select(
                func.sum(case((Tender.risk_score <= 30, 1), else_=0)),
                func.sum(case(((Tender.risk_score >= 31) & (Tender.risk_score <= 55), 1), else_=0)),
                func.sum(case(((Tender.risk_score >= 56) & (Tender.risk_score <= 80), 1), else_=0)),
                func.sum(case((Tender.risk_score >= 81, 1), else_=0)),
            )
            .where(Tender.risk_score.isnot(None))
        )
    )).first()
    risk_distribution = [
        RiskBucket(label="0-30", count=int(dist_row[0] or 0) if dist_row else 0),
        RiskBucket(label="31-55", count=int(dist_row[1] or 0) if dist_row else 0),
        RiskBucket(label="56-80", count=int(dist_row[2] or 0) if dist_row else 0),
        RiskBucket(label="81+", count=int(dist_row[3] or 0) if dist_row else 0),
    ]

    # Скоро закриваються: активні конкурентні з дедлайном у найближчі 7 днів
    # (без фільтра періоду публікації: дедлайн важливіший за дату публікації)
    now = datetime.utcnow()
    closing_result = await db.execute(
        select(Tender)
        .where(
            Tender.status.like("active%"),
            Tender.end_date.isnot(None),
            Tender.end_date >= now,
            Tender.end_date <= now + timedelta(days=7),
            Tender.amount >= min_amount,
            not_reporting,
        )
        .order_by(Tender.end_date.asc(), desc(Tender.amount))
        .limit(10)
    )
    closing_soon = [_tender_to_response(t) for t in closing_result.scalars().all()]

    # Час останнього оновлення даних = остання зміна тендера при синхронізації
    last_updated = (await db.execute(
        select(func.max(Tender.updated_at))
    )).scalar()

    return DashboardResponse(
        kpi=kpi,
        chart_data=chart_data,
        suspicious_tenders=suspicious_tenders,
        active_suspicious_tenders=active_suspicious_tenders,
        recent_tenders=recent_tenders,
        risk_distribution=risk_distribution,
        closing_soon=closing_soon,
        last_updated=last_updated,
    )
