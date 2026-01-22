"""Обработчики команд /start и /help."""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    # Логируем нового пользователя
    user = message.from_user
    logger.info(
        f"🆕 Новый пользователь: id={user.id}, "
        f"@{user.username or 'no_username'}, "
        f"{user.first_name or ''} {user.last_name or ''}".strip()
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
