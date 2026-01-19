"""Конфигурация бота через переменные окружения."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    BOT_TOKEN: str
    LOG_LEVEL: str = "INFO"
    WB_API_TIMEOUT: int = 10
    WB_RATE_LIMIT_DELAY: float = 0.2
    MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
