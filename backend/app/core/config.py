"""
AI Prozorro Intelligence - Конфігурація додатку.
Завантажує налаштування з .env файлу.
"""

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings
from typing import List

# Шлях до кореневого .env (../../.env відносно цього файлу)
ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"
LOCAL_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Головні налаштування додатку."""

    # Додаток
    app_name: str = "AI Prozorro Intelligence"
    app_version: str = "1.4.6"
    app_env: str = "development"
    debug: bool = True

    # База даних
    database_url: str = "sqlite+aiosqlite:///./prozorro.db"
    database_url_sync: str = "sqlite:///./prozorro.db"

    # Groq AI
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    # Ліміти Groq API (безкоштовний тариф: 30 запитів/хв, 1000 запитів/день)
    # Тримаємо запас, бо ретраї при 429 теж рахуються
    groq_max_requests_per_minute: int = 28
    groq_max_requests_per_day: int = 950
    # Пауза між запитами до Groq: реальне вузьке місце безкоштовного тарифу -
    # ліміт токенів за хвилину (TPM ~12K для llama-3.3-70b), один аналіз ~3K
    # токенів => стійкий темп ~4 запити/хв
    groq_request_pause_seconds: float = 15.0
    # Ліміт фази скорингу (Risk Engine, без Groq) за один запуск
    ai_scoring_batch_limit: int = 500

    # n8n
    n8n_webhook_url: str = ""

    # Поріг "високого" Індексу ризику (AI): шкала 0-30 низький /
    # 31-55 середній / 56-80 високий / 81+ критичний
    high_risk_threshold: int = 56
    # Дашборд: мінімальна сума для блоку "Топ за індексом ризику".
    # Мікрозакупівлі до 10 тис. грн - шум для антикорупційного аналізу
    dashboard_suspicious_min_amount: float = 10_000
    # Якщо тендерів з високим індексом немає - показуємо кандидатів з risk >= 40
    dashboard_suspicious_fallback_risk: int = 40
    # Поріг ризику для блоку активних підозрілих (нижчий за високий,
    # бо активні тендери ще не завжди повністю оброблені AI-скорингом)
    dashboard_active_risk_min: int = 50

    # Telegram
    #telegram_bot_token: str = ""
    #telegram_channel_id: str = ""

    # Prozorro API
    prozorro_api_url: str = "https://public.api.openprocurement.org"
    prozorro_api_version: str = "2.5"

    # Синхронізація
    initial_import_days: int = 30
    # Вікно збереження даних ~6 місяців: історія переможців/замовників
    # для AI-аналізу охоплює півроку
    data_retention_days: int = 180
    sync_interval_minutes: int = 10

    # Сервер
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]

    @property
    def async_database_url(self) -> str:
        """
        Нормалізований URL для асинхронного движка.
        Neon/Render дають postgres://...?sslmode=require - конвертуємо
        під asyncpg (він не розуміє sslmode/channel_binding у query).
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        if "+asyncpg" in url:
            parts = urlsplit(url)
            query = {
                k: v for k, v in parse_qsl(parts.query)
                if k not in ("sslmode", "channel_binding")
            }
            url = urlunsplit(parts._replace(query=urlencode(query)))
        return url

    @property
    def database_ssl_required(self) -> bool:
        """Чи вимагає база SSL (Neon - завжди так)."""
        url = self.database_url
        return "sslmode=require" in url or ".neon.tech" in url

    class Config:
        env_file = (str(ROOT_ENV), str(LOCAL_ENV))
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
