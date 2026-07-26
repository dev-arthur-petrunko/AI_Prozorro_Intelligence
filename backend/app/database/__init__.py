"""
AI Prozorro Intelligence - Сесія бази даних.
Асинхронний движок SQLAlchemy для PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# SSL обов'язковий для Neon PostgreSQL; для SQLite connect_args порожні
_connect_args = {"ssl": True} if settings.database_ssl_required else {}

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовий клас для всіх моделей."""
    pass


async def get_session() -> AsyncSession:
    """Отримати асинхронну сесію бази даних."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Ініціалізація бази даних - створення всіх таблиць."""
    async with engine.begin() as conn:
        from app.models import Base as ModelsBase  # noqa: F401
        await conn.run_sync(ModelsBase.metadata.create_all)
