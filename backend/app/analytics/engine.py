"""
AI Prozorro Intelligence - Аналітичний движок.
Розраховує статистику по компаніях, замовниках, категоріях та регіонах.
"""

import json
import logging
from datetime import datetime, date, timedelta

from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.core.config import settings
from app.models.tender import Tender
from app.models.company import Company
from app.models.buyer import Buyer
from app.models.analytics import AnalyticsSnapshot

logger = logging.getLogger(__name__)


async def recalculate_company_stats():
    """
    Перерахувати статистику компаній.

    Один bulk UPDATE замість N+1: раніше цикл робив окремий SELECT на
    КОЖНУ компанію (тисячі round-trip запитів на кожен запуск, це і
    "з'їдало" ліміт Network transfer на Neon). Тепер - один запит на
    всю таблицю.
    """
    async with async_session_factory() as session:
        result = await session.execute(text("""
            UPDATE companies c
            SET wins_count = COALESCE(agg.cnt, 0),
                total_amount = COALESCE(agg.total, 0),
                avg_amount = COALESCE(agg.avg_amt, 0)
            FROM (
                SELECT
                    winner_id,
                    COUNT(*) AS cnt,
                    COALESCE(SUM(amount), 0) AS total,
                    COALESCE(AVG(amount), 0) AS avg_amt
                FROM tenders
                WHERE winner_id IS NOT NULL
                GROUP BY winner_id
            ) agg
            WHERE c.id = agg.winner_id
        """))
        # Компанії без жодної перемоги (не потрапили в agg) - обнуляємо
        await session.execute(text("""
            UPDATE companies
            SET wins_count = 0, total_amount = 0, avg_amount = 0
            WHERE id NOT IN (SELECT DISTINCT winner_id FROM tenders WHERE winner_id IS NOT NULL)
        """))
        await session.commit()
        logger.info(f"Статистика компаній оновлена одним запитом (rowcount={result.rowcount})")


async def recalculate_buyer_stats():
    """
    Перерахувати статистику замовників.

    Аналогічно recalculate_company_stats - один bulk UPDATE замість
    циклу з окремим запитом на кожного замовника.
    """
    async with async_session_factory() as session:
        result = await session.execute(text("""
            UPDATE buyers b
            SET tenders_count = COALESCE(agg.cnt, 0),
                total_amount = COALESCE(agg.total, 0),
                avg_participants = COALESCE(agg.avg_p, 0)
            FROM (
                SELECT
                    buyer_id,
                    COUNT(*) AS cnt,
                    COALESCE(SUM(amount), 0) AS total,
                    COALESCE(AVG(participants_count), 0) AS avg_p
                FROM tenders
                WHERE buyer_id IS NOT NULL
                GROUP BY buyer_id
            ) agg
            WHERE b.id = agg.buyer_id
        """))
        await session.execute(text("""
            UPDATE buyers
            SET tenders_count = 0, total_amount = 0, avg_participants = 0
            WHERE id NOT IN (SELECT DISTINCT buyer_id FROM tenders WHERE buyer_id IS NOT NULL)
        """))
        await session.commit()
        logger.info(f"Статистика замовників оновлена одним запитом (rowcount={result.rowcount})")


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
