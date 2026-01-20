"""Обработчик артикулов и ссылок товаров."""

from aiogram import Router
from aiogram.types import Message
import logging
import time

from utils.validators import ArticleValidator
from utils.exceptions import InvalidArticleError, ProductNotFoundError, WBAPIError
from services.wb_parser import WBParser
from bot.keyboards.inline import get_media_type_keyboard
from utils.decorators import retry_on_telegram_error

router = Router()
logger = logging.getLogger(__name__)


@router.message()
@retry_on_telegram_error(max_retries=3, delay=1.0)
async def handle_article(message: Message):
    """
    Обработчик артикулов и ссылок.

    Args:
        message: Сообщение от пользователя
    """
    start_time = time.perf_counter()

    user = message.from_user
    user_info = (
        f"id={user.id}, "
        f"username=@{user.username if user.username else 'None'}, "
        f"name={user.first_name or ''} {user.last_name or ''}".strip()
    )

    logger.info(
        f"📨 Получен запрос от пользователя [{user_info}]: "
        f"'{message.text[:50]}{'...' if len(message.text) > 50 else ''}'"
    )

    try:
        # Валидация и извлечение артикула
        nm_id = ArticleValidator.extract_article(message.text)

        logger.info(f"✅ Артикул распознан: {nm_id} (user {user.id})")

        # Отправка сообщения о поиске
        status_msg = await message.answer(f"🔍 Ищу товар {nm_id}...")

        # Получение данных о товаре (только фото, видео ищем позже)
        async with WBParser() as parser:
            media = await parser.get_product_media(nm_id, skip_video=True)

        # Проверка наличия фото
        if not media.has_photos():
            await status_msg.edit_text(f"❌ У товара {nm_id} нет фото")
            elapsed = time.perf_counter() - start_time
            logger.warning(f"⚠️  Товар {nm_id} без фото для user {user.id}, time={elapsed:.2f}s")
            return

        wb_url = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"
        info_text = (
            f"✅ Товар найден!\n\n"
            f"📦 Артикул: {nm_id}\n"
            f"📷 Фото: {len(media.photos)} шт.\n"
            f"🔗 {wb_url}"
        )

        # Отправка клавиатуры
        await status_msg.edit_text(
            text=info_text,
            reply_markup=get_media_type_keyboard(nm_id)
        )

        elapsed = time.perf_counter() - start_time
        logger.info(
            f"✅ Товар {nm_id} найден: photos={len(media.photos)}, "
            f"user={user.id}, time={elapsed:.2f}s"
        )

    except InvalidArticleError as e:
        await message.answer(str(e))
        elapsed = time.perf_counter() - start_time
        logger.warning(
            f"❌ Неверный формат артикула от user {user.id}: '{message.text}', "
            f"time={elapsed:.2f}s"
        )

    except ProductNotFoundError:
        await message.answer(
            f"❌ Товар не найден на Wildberries.\n"
            f"Проверьте артикул и попробуйте снова."
        )
        elapsed = time.perf_counter() - start_time
        logger.warning(
            f"❌ Товар не найден для user {user.id}: '{message.text}', "
            f"time={elapsed:.2f}s"
        )

    except WBAPIError as e:
        await message.answer(
            "❌ Не удалось получить данные с Wildberries.\n"
            "Попробуйте позже."
        )
        elapsed = time.perf_counter() - start_time
        logger.error(
            f"❌ WB API ошибка для user {user.id}, текст '{message.text}': "
            f"{type(e).__name__}: {e}, time={elapsed:.2f}s"
        )

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже."
        )
        elapsed = time.perf_counter() - start_time
        logger.exception(
            f"❌ Неожиданная ошибка для user {user.id}, текст '{message.text}': "
            f"{type(e).__name__}: {e}, time={elapsed:.2f}s"
        )
