"""
AI Prozorro Intelligence - Залежності FastAPI.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_session


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    """Залежність для отримання сесії БД в ендпоінтах."""
    return session
