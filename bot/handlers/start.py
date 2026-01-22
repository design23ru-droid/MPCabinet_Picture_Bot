"""Обработчики команд /start и /help."""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.analytics import AnalyticsService
from services.notifications import send_new_user_notification

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    user = message.from_user

    # Логируем пользователя
    logger.info(
        f"🆕 Пользователь: id={user.id}, "
        f"@{user.username or 'no_username'}, "
        f"{user.first_name or ''} {user.last_name or ''}".strip()
    )

    # Трекинг в аналитике
    analytics = AnalyticsService()
    is_new_user = await analytics.track_user_start(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Отправка уведомления о новом пользователе в канал
    if is_new_user:
        await send_new_user_notification(
            bot=message.bot,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

    # Сообщение 1: О проекте MPCabinet
    await message.answer(
        "ℹ️ Этот бот — часть <b>экосистемы MPCabinet:</b> набора Telegram-ботов для удобной ежедневной работы менеджера на Wildberries.\n\n"
        "👉 <b>Присоединяйся</b> к сообществу — https://t.me/+R0Px1RRDjnQwZjQy",
        parse_mode="HTML"
    )

    # Сообщение 2: Инструкция по использованию
    await message.answer(
        "⬇️ <b>Чтобы скачать</b> фото или видео, просто <b>отправь в чат:</b>\n"
        "• артикул\n"
        "• или ссылку на товар",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    await message.answer(
        "ℹ️ Как пользоваться:\n\n"
        "1️⃣ Отправьте артикул или ссылку на товар WB\n"
        "2️⃣ Выберите что хотите получить (фото/видео/всё)\n"
        "3️⃣ Получите файлы\n\n"
        "Примеры:\n"
        "• 12345678\n"
        "• https://www.wildberries.ru/catalog/12345678/detail.aspx\n\n"
        "Бот полностью бесплатный и работает с публичными данными Wildberries."
    )
