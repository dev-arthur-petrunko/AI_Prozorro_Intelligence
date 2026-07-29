"""
AI Prozorro Intelligence - Модель тендеру.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tender(Base):
    """Модель тендеру (закупівлі)."""

    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prozorro_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    # Тип процедури Prozorro (procurementMethodType): reporting = звіт про
    # укладений договір (пряма закупівля), решта - конкурентні процедури
    procurement_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    cpv_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Фінальна ціна активного award (для фактора "відсутність зниження ціни")
    final_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="UAH")
    # Кількість та ціна за одиницю (з items Prozorro; заповнюється лише
    # для тендерів з одним item - інакше суму не можна коректно розділити)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Зв'язки
    buyer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("buyers.id"), nullable=True)
    winner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Аукціон
    participants_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # AI аналіз
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_factors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    # Прапорець "потрібен переаналіз": ставиться, коли у НЕзавершеного тендера
    # змінилися значущі поля (статус, учасники, ціна, переможець)
    analysis_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
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
