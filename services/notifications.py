"""Сервис отправки уведомлений в Telegram канал."""

import logging
from datetime import date
from typing import Dict, Optional

from aiogram import Bot

from config.settings import Settings

logger = logging.getLogger(__name__)


async def send_new_user_notification(
    bot: Bot,
    user_id: int,
    username: Optional[str],
    first_name: Optional[str]
) -> bool:
    """
    Отправить уведомление о новом пользователе в канал аналитики.

    Args:
        bot: Экземпляр aiogram Bot
        user_id: Telegram ID пользователя
        username: Username пользователя (без @)
        first_name: Имя пользователя

    Returns:
        True если уведомление отправлено успешно, False при ошибке
    """
    settings = Settings()

    # Проверяем что аналитика включена и канал настроен
    if not settings.ENABLE_ANALYTICS or not settings.ANALYTICS_CHANNEL_ID:
        logger.debug("Уведомления отключены (ENABLE_ANALYTICS=False или канал не настроен)")
        return False

    try:
        # Формируем сообщение
        user_display = f"@{username}" if username else f"{first_name or 'Без имени'}"
        message = (
            f"🆕 <b>Новый пользователь запустил бота</b>\n\n"
            f"👤 {user_display}\n"
            f"🆔 <code>{user_id}</code>"
        )

        # Отправляем в канал
        await bot.send_message(
            chat_id=settings.ANALYTICS_CHANNEL_ID,
            text=message,
            parse_mode="HTML"
        )

        logger.info(f"✅ Уведомление о новом пользователе отправлено: {user_display} ({user_id})")
        return True

    except Exception as e:
        logger.error(
            f"❌ Ошибка при отправке уведомления о новом пользователе: "
            f"{type(e).__name__}: {e}"
        )
        return False


async def send_daily_digest(
    bot: Bot,
    stats: Dict,
    target_date: date
) -> bool:
    """
    Отправить ежедневный дайджест статистики в канал аналитики.

    Args:
        bot: Экземпляр aiogram Bot
        stats: Словарь со статистикой из AnalyticsService.get_daily_stats()
        target_date: Дата за которую статистика

    Returns:
        True если дайджест отправлен успешно, False при ошибке
    """
    settings = Settings()

    # Проверяем что аналитика включена и канал настроен
    if not settings.ENABLE_ANALYTICS or not settings.ANALYTICS_CHANNEL_ID:
        logger.debug("Дайджест отключен (ENABLE_ANALYTICS=False или канал не настроен)")
        return False

    # Проверяем что статистика получена
    if stats is None:
        logger.warning("Невозможно отправить дайджест - статистика недоступна (БД недоступна)")
        return False

    try:
        # Форматируем дату
        date_str = target_date.strftime("%d.%m.%Y")

        # Формируем сообщение
        message = (
            f"📊 <b>Статистика за {date_str}</b>\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"• Новых: {stats['new_users']}\n"
            f"• Всего: {stats['total_users']}\n"
            f"• Вернулись: {stats['returning_users']} (повторные /start)\n\n"
            f"📦 <b>Активность:</b>\n"
            f"• Запросов артикулов: {stats['article_requests']}\n"
            f"• Фото отправлено: {stats['photos_sent']} ({stats['unique_products']} товаров)\n"
            f"• Видео отправлено: {stats['videos_sent']}\n"
        )

        # Добавляем секцию ошибок только если есть ошибки
        if stats['errors'] > 0:
            message += (
                f"\n⚠️ <b>Ошибки:</b>\n"
                f"• Всего: {stats['errors']}"
            )

        # Отправляем в канал
        await bot.send_message(
            chat_id=settings.ANALYTICS_CHANNEL_ID,
            text=message,
            parse_mode="HTML"
        )

        logger.info(f"✅ Дайджест за {date_str} отправлен")
        return True

    except Exception as e:
        logger.error(
            f"❌ Ошибка при отправке дайджеста: "
            f"{type(e).__name__}: {e}"
        )
        return False
