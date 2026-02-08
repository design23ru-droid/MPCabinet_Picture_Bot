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

    # Сжатие видео
    VIDEO_CRF: int = 28  # Качество сжатия (18=отличное, 23=хорошее, 28=приемлемое)
    VIDEO_PRESET: str = "fast"  # Скорость кодирования (ultrafast, fast, medium, slow)

    # Rate limiting (защита от спама)
    RATE_LIMIT_SECONDS: float = 3.0  # Минимальный интервал между запросами пользователя

    # Local Telegram Bot API Server
    TELEGRAM_API_BASE_URL: Optional[str] = None  # http://telegram-bot-api:8081
    TELEGRAM_API_LOCAL: bool = False  # True для Local Bot API (лимит 2GB вместо 50MB)

    # Database (PostgreSQL)
    DATABASE_URL: Optional[str] = None  # postgresql://user:pass@host:5432/db

    # Analytics and notifications
    ANALYTICS_CHANNEL_ID: Optional[int] = -1003238492068  # Канал для уведомлений
    ENABLE_ANALYTICS: bool = True  # Включить/выключить аналитику

    # API Gateway (микросервисы)
    USE_GATEWAY: bool = False  # True = микросервисы, False = локальная БД
    GATEWAY_URL: str = "http://api-gateway:8000"  # URL API Gateway
    GATEWAY_API_KEY: Optional[str] = None  # API ключ (если требуется)
    GATEWAY_TIMEOUT: int = 10  # Таймаут запросов к Gateway

    # WB Media Service (микросервис поиска медиа)
    USE_WB_MEDIA_SERVICE: bool = False  # True = wb-media-service, False = локальный WBParser
    WB_MEDIA_SERVICE_URL: str = "http://wb-media-service:8013"  # URL сервиса
    WB_MEDIA_SERVICE_TIMEOUT: int = 40  # 30 сек video search + 10 сек запас

    # Analytics Service (микросервис аналитики)
    USE_ANALYTICS_SERVICE: bool = False  # True = analytics-service, False = локальная БД
    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8003"  # URL сервиса
    ANALYTICS_SERVICE_TIMEOUT: int = 10  # Таймаут запросов к analytics-service

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Получить singleton экземпляр настроек."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
