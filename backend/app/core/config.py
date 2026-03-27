from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SalesMind AI"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/salesmind"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Provider
    AI_PROVIDER: str = "gemini"  # gemini, openai, anthropic, kimi

    # AI APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    KIMI_API_KEY: Optional[str] = None
    KIMI_MODEL: str = "kimi-k2-5"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Email
    EMAIL_BACKEND: str = "console"  # console, resend, smtp
    RESEND_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@localhost"

    class Config:
        env_file = ".env"


settings = Settings()
