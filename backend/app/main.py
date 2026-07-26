"""
AI Prozorro Intelligence - Головний модуль FastAPI.
Точка входу для додатку.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Життєвий цикл додатку: ініціалізація та завершення."""
    logger.info("🚀 Запуск AI Prozorro Intelligence...")

    # Ініціалізація бази даних
    await init_db()
    logger.info("✅ База даних ініціалізована")

    # Запуск планувальника
    from app.scheduler.jobs import start_scheduler
    start_scheduler()
    logger.info("✅ Планувальник запущений")

    yield

    # Зупинка планувальника
    from app.scheduler.jobs import stop_scheduler
    stop_scheduler()
    logger.info("🛑 Додаток зупинено")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-платформа для аналізу державних закупівель України",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення маршрутів
from app.api.routes import dashboard, tenders, companies, buyers, analytics, reports, health  # noqa: E402

app.include_router(health.router, tags=["Health"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(tenders.router, prefix="/tenders", tags=["Tenders"])
app.include_router(companies.router, prefix="/companies", tags=["Companies"])
app.include_router(buyers.router, prefix="/buyers", tags=["Buyers"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/daily-report", tags=["Reports"])


# Логування
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
    )
