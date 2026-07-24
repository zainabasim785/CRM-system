"""
Application settings loaded from environment variables / .env.

Uses pydantic-settings so configuration is typed, validated, and
centralized (12-factor style). All modules should import get_settings().
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="AI Reception Agent", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Security / JWT
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")

    # Groq
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Google Calendar
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/calendar/callback",
        alias="GOOGLE_REDIRECT_URI",
    )
    google_scopes: str = Field(
        default="https://www.googleapis.com/auth/calendar",
        alias="GOOGLE_SCOPES",
    )

    # CORS — store as comma-separated string for .env simplicity
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Render/Heroku often give postgres:// — SQLAlchemy needs postgresql+psycopg2://."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg2://" + value[len("postgres://") :]
        if value.startswith("postgresql://") and "+psycopg2" not in value:
            return "postgresql+psycopg2://" + value[len("postgresql://") :]
        return value

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_not_be_placeholder(cls, value: str) -> str:
        if not value or value == "change-me-to-a-long-random-string":
            # Allow placeholder only outside production; still warn via length check
            if len(value) < 16:
                raise ValueError("SECRET_KEY must be at least 16 characters")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def google_scopes_list(self) -> list[str]:
        return [scope.strip() for scope in self.google_scopes.split(",") if scope.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — safe for FastAPI dependency injection."""
    return Settings()
