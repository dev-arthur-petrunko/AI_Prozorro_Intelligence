"""
AI Prozorro Intelligence - Модель тендеру.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tender(Base):
    """Модель тендеру (закупівлі)."""

    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prozorro_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    cpv_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="UAH")
    
    # Зв'язки
    buyer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("buyers.id"), nullable=True)
    winner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Аукціон
    participants_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # AI аналіз
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_factors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Метадані
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    buyer: Mapped[Optional["Buyer"]] = relationship("Buyer", back_populates="tenders")
    winner: Mapped[Optional["Company"]] = relationship("Company", back_populates="won_tenders")

    __table_args__ = (
        Index("ix_tenders_risk_date", "risk_score", "published_date"),
    )

    def __repr__(self):
        return f"<Tender(id={self.id}, prozorro_id={self.prozorro_id}, title={self.title[:50]})>"


# Avoid circular import
from app.models.buyer import Buyer  # noqa: E402, F401
from app.models.company import Company  # noqa: E402, F401
