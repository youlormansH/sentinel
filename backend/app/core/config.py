from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Sentinel"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="CHANGE_ME_DEV_ONLY_INSECURE_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AES_ENCRYPTION_KEY: str = Field(
        default="CHANGE_ME_DEV_ONLY_32_BYTE_KEY!!"
    )  # must resolve to 32 bytes for AES-256

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"
    SYNC_DATABASE_URL: str = "postgresql://sentinel:sentinel@localhost:5432/sentinel"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # Threat detection thresholds
    BRUTE_FORCE_ATTEMPT_THRESHOLD: int = 10
    BRUTE_FORCE_WINDOW_MINUTES: int = 15
    IMPOSSIBLE_TRAVEL_MAX_KMH: float = 900.0
    API_ABUSE_REQUEST_THRESHOLD: int = 300
    API_ABUSE_WINDOW_MINUTES: int = 5

    # AI Analyst (Anthropic)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-5"

    # Email (stubbed provider; logs to console in dev)
    EMAIL_FROM: str = "no-reply@sentinel.internal"
    FRONTEND_URL: str = "http://localhost:3000"

    # Seed admin (first-run bootstrap only)
    FIRST_ADMIN_EMAIL: str = "admin@sentinel.internal"
    FIRST_ADMIN_PASSWORD: str = "ChangeMe123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
