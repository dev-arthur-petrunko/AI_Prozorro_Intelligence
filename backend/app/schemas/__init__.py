"""
AI Prozorro Intelligence - Pydantic схеми для API.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# === Tender Schemas ===

class TenderBase(BaseModel):
    """Базова схема тендеру."""
    prozorro_id: str
    title: str
    description: Optional[str] = None
    status: str = "active"
    cpv_code: Optional[str] = None
    region: Optional[str] = None
    published_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    amount: Optional[float] = None
    currency: str = "UAH"
    participants_count: int = 0


class TenderResponse(TenderBase):
    """Схема відповіді тендеру."""
    id: int
    buyer_id: Optional[int] = None
    winner_id: Optional[int] = None
    risk_score: Optional[int] = None
    ai_analysis: Optional[str] = None
    risk_factors: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    buyer_name: Optional[str] = None
    winner_name: Optional[str] = None

    class Config:
        from_attributes = True


class TenderListResponse(BaseModel):
    """Список тендерів з пагінацією."""
    items: List[TenderResponse]
    total: int
    page: int
    per_page: int
    pages: int


class TenderDetailResponse(TenderResponse):
    """Детальна інформація про тендер."""
    buyer: Optional["BuyerResponse"] = None
    winner: Optional["CompanyResponse"] = None


# === Company Schemas ===

class CompanyBase(BaseModel):
    """Базова схема компанії."""
    name: str
    edrpou: Optional[str] = None
    region: Optional[str] = None


class CompanyResponse(CompanyBase):
    """Схема відповіді компанії."""
    id: int
    wins_count: int = 0
    total_amount: float = 0.0
    avg_amount: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Список компаній з пагінацією."""
    items: List[CompanyResponse]
    total: int
    page: int
    per_page: int
    pages: int


class CompanyDetailResponse(CompanyResponse):
    """Детальна інформація про компанію."""
    recent_tenders: List[TenderResponse] = []


# === Buyer Schemas ===

class BuyerBase(BaseModel):
    """Базова схема замовника."""
    name: str
    edrpou: Optional[str] = None
    region: Optional[str] = None


class BuyerResponse(BuyerBase):
    """Схема відповіді замовника."""
    id: int
    tenders_count: int = 0
    total_amount: float = 0.0
    avg_participants: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuyerListResponse(BaseModel):
    """Список замовників з пагінацією."""
    items: List[BuyerResponse]
    total: int
    page: int
    per_page: int
    pages: int


class BuyerDetailResponse(BuyerResponse):
    """Детальна інформація про замовника."""
    recent_tenders: List[TenderResponse] = []


# === Dashboard Schemas ===

class DashboardKPI(BaseModel):
    """KPI для головної сторінки."""
    total_tenders: int = 0
    suspicious_tenders: int = 0
    total_companies: int = 0
    total_buyers: int = 0
    today_volume: float = 0.0
    today_new: int = 0


class ChartDataPoint(BaseModel):
    """Точка даних для графіка."""
    date: str
    # Конкурентні процедури (без reporting-звітів)
    tenders_count: int = 0
    # Звіти про укладені договори (procurementMethodType=reporting)
    reports_count: int = 0
    # Обсяги в грн по кожній серії
    tenders_volume: float = 0.0
    reports_volume: float = 0.0
    # Тендери з високим індексом ризику (risk_score >= 61)
    high_risk_count: int = 0
    volume: float = 0.0
    new_tenders: int = 0


class DashboardResponse(BaseModel):
    """Повна відповідь дашборду."""
    kpi: DashboardKPI
    chart_data: List[ChartDataPoint] = []
    suspicious_tenders: List[TenderResponse] = []
    active_suspicious_tenders: List[TenderResponse] = []
    recent_tenders: List[TenderResponse] = []
    # Час останнього оновлення даних (остання синхронізація з Prozorro)
    last_updated: Optional[datetime] = None


# === Analytics Schemas ===

class CategoryStat(BaseModel):
    """Статистика по категорії."""
    cpv_code: str
    name: Optional[str] = None
    tenders_count: int = 0
    total_amount: float = 0.0


class RegionStat(BaseModel):
    """Статистика по регіону."""
    region: str
    tenders_count: int = 0
    total_amount: float = 0.0


class AnalyticsResponse(BaseModel):
    """Відповідь аналітики."""
    categories: List[CategoryStat] = []
    regions: List[RegionStat] = []
    top_companies: List[CompanyResponse] = []
    top_buyers: List[BuyerResponse] = []
    price_dynamics: List[ChartDataPoint] = []
    # Час останнього оновлення даних
    last_updated: Optional[datetime] = None


# === Daily Report ===

class DailyReportResponse(BaseModel):
    """Щоденний звіт."""
    date: str
    total_new_tenders: int = 0
    suspicious_count: int = 0
    highest_risk_score: int = 0
    largest_tender_amount: float = 0.0
    top_category: Optional[str] = None
    top_region: Optional[str] = None
    suspicious_tenders: List[TenderResponse] = []


# === Health ===

class HealthResponse(BaseModel):
    """Статус здоров'я системи."""
    status: str = "ok"
    version: str
    database: str = "connected"
    tenders_count: int = 0
    last_sync: Optional[str] = None


# Resolve forward references
TenderDetailResponse.model_rebuild()
CompanyDetailResponse.model_rebuild()
BuyerDetailResponse.model_rebuild()
