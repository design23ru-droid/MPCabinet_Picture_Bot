"""Inline клавиатуры для бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_media_type_keyboard(nm_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа медиа.

    Callback data format: download:{nm_id}:{media_type}

    Args:
        nm_id: Артикул товара

    Returns:
        InlineKeyboardMarkup с кнопками выбора
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📷 Скачать фото",
            callback_data=f"download:{nm_id}:photo"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎥 Скачать видео",
            callback_data=f"download:{nm_id}:video"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📷 + 🎥 Скачать всё",
            callback_data=f"download:{nm_id}:both"
        )
    )

    return builder.as_markup()
