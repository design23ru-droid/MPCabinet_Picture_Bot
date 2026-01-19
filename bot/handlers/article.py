"""Обработчик артикулов и ссылок товаров."""

from aiogram import Router
from aiogram.types import Message
import logging

from utils.validators import ArticleValidator
from utils.exceptions import InvalidArticleError, ProductNotFoundError, WBAPIError
from services.wb_parser import WBParser
from bot.keyboards.inline import get_media_type_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message()
async def handle_article(message: Message):
    """
    Обработчик артикулов и ссылок.

    Args:
        message: Сообщение от пользователя
    """
    try:
        # Валидация и извлечение артикула
        nm_id = ArticleValidator.extract_article(message.text)

        logger.info(f"User {message.from_user.id} requested article {nm_id}")

        # Отправка сообщения о поиске
        status_msg = await message.answer(f"🔍 Ищу товар {nm_id}...")

        # Получение данных о товаре
        async with WBParser() as parser:
            media = await parser.get_product_media(nm_id)

        # Проверка наличия медиа
        if not media.has_photos() and not media.has_video():
            await status_msg.edit_text(
                f"❌ У товара {nm_id} нет фото и видео"
            )
            return

        # Формирование текста с информацией
        media_info = []
        if media.has_photos():
            media_info.append(f"📷 Фото: {len(media.photos)} шт.")
        if media.has_video():
            media_info.append("🎥 Видео: есть")

        info_text = (
            f"✅ Товар найден!\n\n"
            f"📦 {media.name}\n"
            f"🔢 Артикул: {nm_id}\n\n"
            f"{chr(10).join(media_info)}\n\n"
            f"Выберите что хотите получить:"
        )

        # Отправка клавиатуры
        await status_msg.edit_text(
            text=info_text,
            reply_markup=get_media_type_keyboard(nm_id)
        )

        logger.info(
            f"Product {nm_id} found: "
            f"photos={len(media.photos)}, video={media.has_video()}"
        )

    except InvalidArticleError as e:
        await message.answer(str(e))

    except ProductNotFoundError:
        await message.answer(
            f"❌ Товар не найден на Wildberries.\n"
            f"Проверьте артикул и попробуйте снова."
        )
        logger.warning(f"Product not found for user input: {message.text}")

    except WBAPIError as e:
        await message.answer(
            "❌ Не удалось получить данные с Wildberries.\n"
            "Попробуйте позже."
        )
        logger.error(f"WB API error for article {message.text}: {e}")

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже."
        )
        logger.exception(f"Unexpected error handling article: {e}")
