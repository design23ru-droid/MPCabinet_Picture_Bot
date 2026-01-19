"""Конфигурация бота через переменные окружения."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    BOT_TOKEN: str
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    WB_API_TIMEOUT: int = 10
    WB_RATE_LIMIT_DELAY: float = 0.2
    MAX_RETRIES: int = 3

    # Дополнительные опции для DEBUG режима
    DEBUG_HTTP_REQUESTS: bool = False  # Логировать все HTTP запросы (только в DEBUG)
    DEBUG_MEASURE_TIME: bool = False  # Измерять время всех операций (только в DEBUG)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
