"""Inline клавиатуры для бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_media_type_keyboard(nm_id: str, video_status: str = "searching") -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа медиа.

    Callback data format: download:{nm_id}:{media_type}

    Args:
        nm_id: Артикул товара
        video_status: Статус видео - "searching", "found", "not_found"

    Returns:
        InlineKeyboardMarkup с кнопками выбора
    """
    builder = InlineKeyboardBuilder()

    # Кнопка "Скачать фото" - всегда
    builder.row(
        InlineKeyboardButton(
            text="📷 Скачать фото",
            callback_data=f"download:{nm_id}:photo"
        )
    )

    # Кнопки с видео - только если видео найдено
    if video_status == "found":
        builder.row(
            InlineKeyboardButton(
                text="🎬 Скачать видео",
                callback_data=f"download:{nm_id}:video"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📦 Скачать всё",
                callback_data=f"download:{nm_id}:both"
            )
        )

    return builder.as_markup()
