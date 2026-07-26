"""
AI Prozorro Intelligence - Модель замовника.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Buyer(Base):
    """Модель замовника (організації-закупівельника)."""

    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    edrpou: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Статистика
    tenders_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    avg_participants: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Метадані
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenders: Mapped[List["Tender"]] = relationship("Tender", back_populates="buyer", lazy="selectin")

    def __repr__(self):
        return f"<Buyer(id={self.id}, name={self.name[:50]}, edrpou={self.edrpou})>"


# Avoid circular import
from app.models.tender import Tender  # noqa: E402, F401
