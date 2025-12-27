"""Pydantic-based application settings for Pocket Portals.

This module provides centralized configuration management using pydantic-settings,
supporting environment variables and .env file loading.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables.
    Supports .env file loading for local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""

    # Application Settings
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    crew_verbose: bool = True

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 86400  # 24 hours in seconds

    # Session Backend Configuration
    session_backend: Literal["memory", "redis"] = "redis"

    @property
    def is_redis_enabled(self) -> bool:
        """Check if Redis backend is enabled."""
        return self.session_backend == "redis"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns a cached Settings instance for efficient repeated access.
    The cache is cleared when the application restarts.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()


# Convenience export for direct access
settings = get_settings()
