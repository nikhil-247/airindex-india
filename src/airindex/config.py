"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for API and data services."""

    app_name: str = "AirIndex India"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+asyncpg://airindex:airindex@localhost:5432/airindex"
    redis_url: str = "redis://localhost:6379/0"

    collection_user_agent: str = "AirIndexIndiaResearchBot/0.1"
    collection_request_timeout_seconds: int = 30
    collection_max_concurrency: int = 2

    secret_key: str = "development-only-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings object."""

    return Settings()
