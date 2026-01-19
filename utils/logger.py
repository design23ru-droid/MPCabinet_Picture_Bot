"""Настройка логирования для бота."""

import logging
from logging.handlers import RotatingFileHandler
import sys
from config.settings import Settings


def setup_logger() -> None:
    """Настраивает подробное логирование с rotation в файл и консоль."""
    settings = Settings()

    # Детальный формат логов с дополнительными полями
    detailed_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - '
        '%(funcName)s() - %(message)s'
    )

    # Формат для консоли (более компактный)
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Формат времени с миллисекундами
    date_format = '%Y-%m-%d %H:%M:%S,%f'

    # Создание formatters
    detailed_formatter = logging.Formatter(detailed_format, datefmt=date_format)
    console_formatter = logging.Formatter(console_format, datefmt=date_format)

    # Rotation file handler (10 MB макс, 5 backup файлов)
    file_handler = RotatingFileHandler(
        'bot.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Настройка уровней для внешних библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    # В DEBUG режиме показываем больше деталей от библиотек
    if settings.LOG_LEVEL.upper() == 'DEBUG':
        logging.getLogger('aiogram').setLevel(logging.INFO)
        logging.getLogger('aiohttp').setLevel(logging.INFO)
        root_logger.debug("=" * 80)
        root_logger.debug("DEBUG MODE ENABLED - Detailed logging is active")
        root_logger.debug("=" * 80)
