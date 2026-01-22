"""Сервис формирования и отправки ежедневной статистики."""

import logging
from datetime import date, timedelta
from typing import Optional

from aiogram import Bot

from services.analytics import AnalyticsService
from services.notifications import send_daily_digest

logger = logging.getLogger(__name__)


async def send_daily_digest_job(bot: Bot, target_date: Optional[date] = None) -> bool:
    """
    Отправка ежедневного дайджеста статистики.

    Args:
        bot: Экземпляр aiogram Bot
        target_date: Дата за которую отправить статистику (по умолчанию - вчера)

    Returns:
        True если дайджест отправлен успешно, False при ошибке
    """
    if target_date is None:
        # По умолчанию - статистика за вчерашний день
        target_date = date.today() - timedelta(days=1)

    logger.info(f"📊 Начинаем формирование дайджеста за {target_date.strftime('%d.%m.%Y')}")

    try:
        # Получение статистики
        analytics = AnalyticsService()
        stats = await analytics.get_daily_stats(target_date)

        if stats is None:
            logger.warning("БД недоступна - дайджест не может быть отправлен")
            return False

        # Отправка дайджеста
        success = await send_daily_digest(bot, stats, target_date)

        if success:
            logger.info(f"✅ Дайджест за {target_date.strftime('%d.%m.%Y')} успешно отправлен")
        else:
            logger.warning(f"⚠️  Не удалось отправить дайджест за {target_date.strftime('%d.%m.%Y')}")

        return success

    except Exception as e:
        logger.exception(
            f"❌ Ошибка при формировании дайджеста за {target_date.strftime('%d.%m.%Y')}: "
            f"{type(e).__name__}: {e}"
        )
        return False
