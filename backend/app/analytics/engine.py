"""
AI Prozorro Intelligence - Аналітичний движок.
Розраховує статистику по компаніях, замовниках, категоріях та регіонах.
"""

import json
import logging
from datetime import datetime, date, timedelta

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.core.config import settings
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.models.analytics import AnalyticsSnapshot

logger = logging.getLogger(__name__)


async def recalculate_company_stats():
    """Перерахувати статистику компаній."""
    async with async_session_factory() as session:
        companies = (await session.execute(select(Company))).scalars().all()
        
        for company in companies:
            result = await session.execute(
                select(
                    func.count(Tender.id),
                    func.coalesce(func.sum(Tender.amount), 0),
                    func.coalesce(func.avg(Tender.amount), 0),
                ).where(Tender.winner_id == company.id)
            )
            row = result.one()
            company.wins_count = row[0]
            company.total_amount = float(row[1])
            company.avg_amount = float(row[2])
        
        await session.commit()
        logger.info(f"Статистика оновлена для {len(companies)} компаній")


async def recalculate_buyer_stats():
    """Перерахувати статистику замовників."""
    async with async_session_factory() as session:
        buyers = (await session.execute(select(Buyer))).scalars().all()
        
        for buyer in buyers:
            result = await session.execute(
                select(
                    func.count(Tender.id),
                    func.coalesce(func.sum(Tender.amount), 0),
                    func.coalesce(func.avg(Tender.participants_count), 0),
                ).where(Tender.buyer_id == buyer.id)
            )
            row = result.one()
            buyer.tenders_count = row[0]
            buyer.total_amount = float(row[1])
            buyer.avg_participants = float(row[2])
        
        await session.commit()
        logger.info(f"Статистика оновлена для {len(buyers)} замовників")


async def generate_analytics_snapshot():
    """Створити щоденний знімок аналітики."""
    async with async_session_factory() as session:
        today = date.today()
        
        # Перевірити чи знімок вже існує
        existing = await session.execute(
            select(AnalyticsSnapshot).where(AnalyticsSnapshot.snapshot_date == today)
        )
        snapshot = existing.scalar_one_or_none()
        
        # Загальна кількість тендерів
        total = (await session.execute(select(func.count(Tender.id)))).scalar() or 0
        
        # Підозрілі (високий Індекс ризику)
        suspicious = (await session.execute(
            select(func.count(Tender.id)).where(Tender.risk_score >= settings.high_risk_threshold)
        )).scalar() or 0
        
        # Загальний обсяг
        volume = (await session.execute(
            select(func.coalesce(func.sum(Tender.amount), 0))
        )).scalar() or 0
        
        # Нові за сьогодні
        today_start = datetime.combine(today, datetime.min.time())
        new_today = (await session.execute(
            select(func.count(Tender.id)).where(Tender.created_at >= today_start)
        )).scalar() or 0
        
        # Топ категорія
        top_cat_result = await session.execute(
            select(Tender.cpv_code, func.count(Tender.id).label("cnt"))
            .where(Tender.cpv_code.isnot(None))
            .group_by(Tender.cpv_code)
            .order_by(desc("cnt"))
            .limit(1)
        )
        top_cat_row = top_cat_result.first()
        top_category = top_cat_row[0] if top_cat_row else None
        
        # Топ регіон
        top_reg_result = await session.execute(
            select(Tender.region, func.count(Tender.id).label("cnt"))
            .where(Tender.region.isnot(None))
            .group_by(Tender.region)
            .order_by(desc("cnt"))
            .limit(1)
        )
        top_reg_row = top_reg_result.first()
        top_region = top_reg_row[0] if top_reg_row else None
        
        # Дані для графіків (останні 30 днів).
        # Конкурентні процедури та reporting-звіти (прямі договори, публікуються
        # пост-фактум зі статусом complete) рахуємо окремо, інакше пачки звітів
        # спотворюють графік динаміки закупівель
        chart_data = []
        for i in range(30):
            d = today - timedelta(days=29 - i)
            day_start = datetime.combine(d, datetime.min.time())
            day_end = datetime.combine(d, datetime.max.time())
            
            day_count = (await session.execute(
                select(func.count(Tender.id)).where(
                    Tender.published_date.between(day_start, day_end),
                    (Tender.procurement_method.is_(None)) | (Tender.procurement_method != "reporting"),
                )
            )).scalar() or 0
            
            day_reports = (await session.execute(
                select(func.count(Tender.id)).where(
                    Tender.published_date.between(day_start, day_end),
                    Tender.procurement_method == "reporting",
                )
            )).scalar() or 0
            
            day_volume = (await session.execute(
                select(func.coalesce(func.sum(Tender.amount), 0)).where(
                    Tender.published_date.between(day_start, day_end)
                )
            )).scalar() or 0
            
            chart_data.append({
                "date": d.isoformat(),
                "tenders_count": day_count,
                "reports_count": day_reports,
                "volume": float(day_volume),
            })
        
        if snapshot:
            snapshot.total_tenders = total
            snapshot.suspicious_count = suspicious
            snapshot.total_volume = float(volume)
            snapshot.new_tenders_today = new_today
            snapshot.top_category = top_category
            snapshot.top_region = top_region
            snapshot.data_json = json.dumps(chart_data)
        else:
            snapshot = AnalyticsSnapshot(
                snapshot_date=today,
                total_tenders=total,
                suspicious_count=suspicious,
                total_volume=float(volume),
                new_tenders_today=new_today,
                top_category=top_category,
                top_region=top_region,
                data_json=json.dumps(chart_data),
            )
            session.add(snapshot)
        
        await session.commit()
        logger.info(f"Аналітичний знімок створено: {today}")


async def recalculate_all():
    """Повний перерахунок аналітики."""
    logger.info("Запуск повного перерахунку аналітики...")
    await recalculate_company_stats()
    await recalculate_buyer_stats()
    await generate_analytics_snapshot()
    logger.info("Перерахунок аналітики завершено")
