"""Конфигурация бота через переменные окружения."""

from typing import Optional
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

    # HLS конвертация
    FFMPEG_PATH: str = "ffmpeg"  # Путь к ffmpeg (или "ffmpeg" если в PATH)
    HLS_CONVERT_TIMEOUT: int = 300  # 5 минут макс на конвертацию
    HLS_TEMP_DIR: Optional[str] = None  # None = системная temp
    HLS_MAX_VIDEO_SIZE_MB: int = 50  # Лимит Telegram для локальных файлов

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
