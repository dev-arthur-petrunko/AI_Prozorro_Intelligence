"""
AI Prozorro Intelligence - Модель аналітичного знімку.
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalyticsSnapshot(Base):
    """Щоденний знімок аналітики."""

    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    
    # KPI
    total_tenders: Mapped[int] = mapped_column(Integer, default=0)
    suspicious_count: Mapped[int] = mapped_column(Integer, default=0)
    total_volume: Mapped[float] = mapped_column(Float, default=0.0)
    new_tenders_today: Mapped[int] = mapped_column(Integer, default=0)
    
    # Топ
    top_category: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    top_region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Розширені дані (JSON)
    data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Метадані
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AnalyticsSnapshot(date={self.snapshot_date}, tenders={self.total_tenders})>"
