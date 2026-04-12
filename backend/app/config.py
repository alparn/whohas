from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+psycopg://lumen:lumen@localhost:5432/lumen"
    SYNC_INTERVAL_MINUTES: int = 15
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str

    @property
    def async_database_url(self) -> str:
        """Return an async-compatible URL for psycopg async driver."""
        return self.DATABASE_URL.replace("postgresql+psycopg", "postgresql", 1)


settings = Settings()  # type: ignore[call-arg]
