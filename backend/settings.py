"""
Application Settings - Centralized configuration via Pydantic Settings.

Loads from environment variables and .env files. All core configuration
is defined here; module-specific settings (ML, FHIR, Quality) remain
in their respective modules for now.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        "sqlite+aiosqlite:///./varuna.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field("", alias="REDIS_URL")

    # Slides
    slides_repository_path: str = Field("/Slides", alias="SLIDES_REPOSITORY_PATH")

    # Logging
    log_level: str = Field("info", alias="LOG_LEVEL")

    # CORS
    cors_origins: str = Field("", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins:
            return [o.strip() for o in self.cors_origins.split(",")]
        return [
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost",
        ]

    # Auth
    auth_enabled: bool = Field(False, alias="AUTH_ENABLED")

    # Feature flags
    ml_enabled: bool = Field(True, alias="ML_ENABLED")
    ml_provider: str = Field("slideflow", alias="ML_PROVIDER")
    fhir_enabled: bool = Field(False, alias="FHIR_ENABLED")
    quality_enabled: bool = Field(True, alias="QUALITY_ENABLED")

    # Rate limiting
    rate_limit_default: str = Field("100/minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_tiles: str = Field("500/minute", alias="RATE_LIMIT_TILES")
    rate_limit_ml: str = Field("30/minute", alias="RATE_LIMIT_ML")

    # Trusted proxy CIDRs for X-Forwarded-For validation
    trusted_proxy_cidr: str = Field(
        "172.16.0.0/12,10.0.0.0/8,192.168.0.0/16",
        alias="TRUSTED_PROXY_CIDR",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
