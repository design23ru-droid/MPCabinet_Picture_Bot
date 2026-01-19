"""Обработчик callback от inline кнопок."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
import logging
import time

from services.wb_parser import WBParser
from services.media_downloader import MediaDownloader
from utils.exceptions import NoMediaError, WBAPIError
from utils.decorators import retry_on_telegram_error

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("download:"))
@retry_on_telegram_error(max_retries=3, delay=1.0)
async def handle_download_callback(callback: CallbackQuery, bot: Bot):
    """
    Обработчик callback для загрузки медиа.

    Callback data format: download:{nm_id}:{media_type}

    Args:
        callback: Callback query от пользователя
        bot: Bot instance
    """
    start_time = time.perf_counter()

    user = callback.from_user
    user_info = (
        f"id={user.id}, "
        f"username=@{user.username if user.username else 'None'}, "
        f"name={user.first_name or ''} {user.last_name or ''}".strip()
    )

    await callback.answer()

    try:
        # Парсинг callback data
        _, nm_id, media_type = callback.data.split(":")

        logger.info(
            f"🎯 Callback от пользователя [{user_info}]: "
            f"товар={nm_id}, тип={media_type}"
        )

        # Удаление клавиатуры и обновление сообщения
        await callback.message.edit_reply_markup(reply_markup=None)
        status_msg = await callback.message.edit_text("⏳ Загружаю...")

        # Получение данных товара (ленивый поиск)
        async with WBParser() as parser:
            if media_type == "photo":
                media = await parser.get_product_media(nm_id, skip_video=True)
            elif media_type == "video":
                media = await parser.get_product_media(nm_id, skip_photos=True)
            else:  # both
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

        elapsed = time.perf_counter() - start_time
        logger.info(
            f"✅ Успешно отправлено {media_type} для товара {nm_id} "
            f"пользователю {user.id}, time={elapsed:.2f}s"
        )

    except NoMediaError as e:
        await callback.message.edit_text(f"❌ {str(e)}")
        elapsed = time.perf_counter() - start_time
        logger.warning(
            f"⚠️  Нет медиа для товара {nm_id}, user {user.id}: "
            f"{e}, time={elapsed:.2f}s"
        )

    except WBAPIError as e:
        await callback.message.edit_text(
            "❌ Не удалось загрузить медиа. Попробуйте позже."
        )
        elapsed = time.perf_counter() - start_time
        logger.error(
            f"❌ WB API ошибка для товара {nm_id}, user {user.id}: "
            f"{type(e).__name__}: {e}, time={elapsed:.2f}s"
        )

    except Exception as e:
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке."
        )
        elapsed = time.perf_counter() - start_time
        logger.exception(
            f"❌ Ошибка загрузки для товара {nm_id}, user {user.id}: "
            f"{type(e).__name__}: {e}, time={elapsed:.2f}s"
        )
