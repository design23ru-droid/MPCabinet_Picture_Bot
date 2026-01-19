"""Обработчик callback от inline кнопок."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
import logging

from services.wb_parser import WBParser
from services.media_downloader import MediaDownloader
from utils.exceptions import NoMediaError, WBAPIError

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("download:"))
async def handle_download_callback(callback: CallbackQuery, bot: Bot):
    """
    Обработчик callback для загрузки медиа.

    Callback data format: download:{nm_id}:{media_type}

    Args:
        callback: Callback query от пользователя
        bot: Bot instance
    """
    await callback.answer()

    try:
        # Парсинг callback data
        _, nm_id, media_type = callback.data.split(":")

        logger.info(
            f"User {callback.from_user.id} selected {media_type} "
            f"for product {nm_id}"
        )

        # Удаление клавиатуры и обновление сообщения
        await callback.message.edit_reply_markup(reply_markup=None)
        status_msg = await callback.message.edit_text("⏳ Загружаю...")

        # Получение данных товара
        async with WBParser() as parser:
            media = await parser.get_product_media(nm_id)

        # Загрузка и отправка медиа
        downloader = MediaDownloader(bot)

        if media_type == "photo":
            await downloader.send_photos(
                callback.message.chat.id,
                media,
                status_msg
            )
        elif media_type == "video":
            await downloader.send_video(
                callback.message.chat.id,
                media,
                status_msg
            )
        elif media_type == "both":
            await downloader.send_both(
                callback.message.chat.id,
                media,
                status_msg
            )

        # Сообщение об успехе (если status_msg не был удален)
        try:
            await callback.message.edit_text("✅ Готово!")
        except Exception:
            # Сообщение уже удалено в send_photos/send_video
            pass

        logger.info(
            f"Successfully sent {media_type} for product {nm_id} "
            f"to user {callback.from_user.id}"
        )

    except NoMediaError as e:
        await callback.message.edit_text(f"❌ {str(e)}")
        logger.warning(f"No media error for {nm_id}: {e}")

    except WBAPIError as e:
        await callback.message.edit_text(
            "❌ Не удалось загрузить медиа. Попробуйте позже."
        )
        logger.error(f"WB API error for {nm_id}: {e}")

    except Exception as e:
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке."
        )
        logger.exception(f"Download error for {nm_id}: {e}")
