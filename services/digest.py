"""Сервис формирования и отправки ежедневной статистики."""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pytz
from aiogram import Bot

from config.settings import get_settings
from services.analytics import AnalyticsService
from services.notifications import send_daily_digest

logger = logging.getLogger(__name__)


async def _get_stats_via_service(target_date: date):
    """Получить статистику через analytics-service.

    Конвертирует DailyStats из analytics-service в dict формат,
    ожидаемый send_daily_digest (new_users, total_users, article_requests, ...).
    """
    from analytics_client import AnalyticsClient

    settings = get_settings()
    async with AnalyticsClient(
        base_url=settings.ANALYTICS_SERVICE_URL,
        timeout=float(settings.ANALYTICS_SERVICE_TIMEOUT),
    ) as client:
        daily = await client.stats.get_daily(target_date.strftime("%Y-%m-%d"))
        users_count = await client.stats.get_users_count()

    event_stats = daily.stats
    return {
        "new_users": event_stats.get("user.started", 0),
        "total_users": users_count.count,
        "returning_users": 0,
        "article_requests": event_stats.get("article_request", 0),
        "photos_sent": event_stats.get("photo_sent", 0),
        "unique_products": 0,
        "videos_sent": event_stats.get("video_sent", 0),
        "errors": event_stats.get("error", 0),
    }


async def send_daily_digest_job(bot: Bot, target_date: Optional[date] = None) -> bool:
    """
    Отправка ежедневного дайджеста статистики.

    При USE_ANALYTICS_SERVICE=True: получает данные из analytics-service.
    При USE_ANALYTICS_SERVICE=False: получает данные из локальной БД.
    При ошибке analytics-service: fallback на локальную БД.

    Args:
        bot: Экземпляр aiogram Bot
        target_date: Дата за которую отправить статистику (по умолчанию - вчера)

    Returns:
        True если дайджест отправлен успешно, False при ошибке
    """
    if target_date is None:
        # По умолчанию - статистика за вчерашний день (по московскому времени)
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        target_date = now_msk.date() - timedelta(days=1)

    logger.info(f"Начинаем формирование дайджеста за {target_date.strftime('%d.%m.%Y')}")

    try:
        settings = get_settings()
        stats = None

        if settings.USE_ANALYTICS_SERVICE:
            try:
                stats = await _get_stats_via_service(target_date)
                logger.info(
                    f"Статистика получена из analytics-service за {target_date}"
                )
            except Exception as e:
                logger.warning(
                    f"analytics-service ошибка: {e}. Fallback на локальную БД."
                )

        # Fallback на локальную БД или USE_ANALYTICS_SERVICE=False
        if stats is None:
            analytics = AnalyticsService()
            stats = await analytics.get_daily_stats(target_date)

        if stats is None:
            logger.warning("БД недоступна - дайджест не может быть отправлен")
            return False

        # Отправка дайджеста
        success = await send_daily_digest(bot, stats, target_date)

        if success:
            logger.info(f"Дайджест за {target_date.strftime('%d.%m.%Y')} успешно отправлен")
        else:
            logger.warning(f"Не удалось отправить дайджест за {target_date.strftime('%d.%m.%Y')}")

        return success

    except Exception as e:
        logger.exception(
            f"Ошибка при формировании дайджеста за {target_date.strftime('%d.%m.%Y')}: "
            f"{type(e).__name__}: {e}"
        )
        return False