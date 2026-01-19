"""Загрузка и отправка медиафайлов в Telegram."""

import asyncio
import logging
import time
from typing import List
from aiogram import Bot
from aiogram.types import Message, InputMediaPhoto, URLInputFile

from services.wb_parser import ProductMedia
from utils.exceptions import NoMediaError
from utils.decorators import log_execution_time

logger = logging.getLogger(__name__)


class MediaDownloader:
    """Загрузка и отправка медиа в Telegram."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @log_execution_time()
    async def send_photos(
        self,
        chat_id: int,
        media: ProductMedia,
        status_msg: Message
    ) -> None:
        """
        Отправка фотографий пользователю с прогрессом.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса

        Raises:
            NoMediaError: Нет фотографий у товара
        """
        if not media.has_photos():
            raise NoMediaError("У этого товара нет фотографий")

        total = len(media.photos)
        logger.info(
            f"📷 Отправка {total} фото в чат {chat_id} "
            f"(product {media.nm_id})"
        )

        total_start = time.perf_counter()

        # Отправка группами по 10 (лимит sendMediaGroup)
        for i in range(0, total, 10):
            batch = media.photos[i:i+10]
            batch_num = i // 10 + 1
            total_batches = (total + 9) // 10

            # Обновление прогресса
            progress = min(i + len(batch), total)
            try:
                await status_msg.edit_text(
                    f"📷 Загружаю фото {progress}/{total}..."
                )
            except Exception as e:
                logger.warning(f"⚠️  Не удалось обновить прогресс: {e}")

            # Создание media group
            media_group = [
                InputMediaPhoto(media=URLInputFile(url))
                for url in batch
            ]

            logger.debug(
                f"📷 Отправка batch {batch_num}/{total_batches}: "
                f"{len(batch)} фото ({i+1}-{i+len(batch)})"
            )

            try:
                batch_start = time.perf_counter()
                await self.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group,
                    request_timeout=120  # Увеличен таймаут для медленных сетей
                )
                batch_time = time.perf_counter() - batch_start

                logger.info(
                    f"✅ Batch {batch_num}/{total_batches} отправлен за {batch_time:.2f}s"
                )

                await asyncio.sleep(0.5)  # Задержка между группами

            except Exception as e:
                logger.error(
                    f"❌ Ошибка отправки batch {batch_num}/{total_batches}: "
                    f"{type(e).__name__}: {e}"
                )
                raise

        # Удаление сообщения о прогрессе
        try:
            await status_msg.delete()
        except Exception:
            pass

        total_time = time.perf_counter() - total_start
        logger.info(
            f"✅ Успешно отправлено {total} фото в чат {chat_id} "
            f"за {total_time:.2f}s (средн. {total_time/total:.2f}s на фото)"
        )

    @log_execution_time()
    async def send_video(
        self,
        chat_id: int,
        media: ProductMedia,
        status_msg: Message
    ) -> None:
        """
        Отправка видео пользователю.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса

        Raises:
            NoMediaError: Нет видео у товара
        """
        if not media.has_video():
            raise NoMediaError("У этого товара нет видео")

        logger.info(
            f"🎥 Отправка видео в чат {chat_id} "
            f"(product {media.nm_id}, URL: {media.video})"
        )

        try:
            await status_msg.edit_text("🎥 Загружаю видео...")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось обновить прогресс: {e}")

        try:
            video_start = time.perf_counter()
            await self.bot.send_video(
                chat_id=chat_id,
                video=URLInputFile(media.video),
                caption=f"Видео: {media.name}",
                request_timeout=120  # Увеличен таймаут для медленных сетей
            )
            video_time = time.perf_counter() - video_start

            await status_msg.delete()
            logger.info(
                f"✅ Видео успешно отправлено в чат {chat_id} за {video_time:.2f}s"
            )

        except Exception as e:
            logger.error(
                f"❌ Ошибка отправки видео: {type(e).__name__}: {e}\n"
                f"URL: {media.video}"
            )
            # Может быть файл слишком большой или недоступен
            try:
                await status_msg.edit_text(
                    "❌ Не удалось загрузить видео. Возможно, файл слишком большой (лимит 20 MB для URL)"
                )
            except Exception:
                pass
            raise

    @log_execution_time()
    async def send_both(
        self,
        chat_id: int,
        media: ProductMedia,
        status_msg: Message
    ) -> None:
        """
        Отправка фото и видео.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса

        Raises:
            NoMediaError: Нет медиафайлов у товара
        """
        if not media.has_photos() and not media.has_video():
            raise NoMediaError("У этого товара нет медиафайлов")

        logger.info(
            f"📦 Отправка всех медиа в чат {chat_id}: "
            f"фото={len(media.photos) if media.has_photos() else 0}, "
            f"видео={'да' if media.has_video() else 'нет'}"
        )

        # Отправка фото
        if media.has_photos():
            await self.send_photos(chat_id, media, status_msg)

            # Если есть видео, создаем новое сообщение для прогресса
            if media.has_video():
                status_msg = await self.bot.send_message(
                    chat_id,
                    "🎥 Загружаю видео..."
                )

        # Отправка видео
        if media.has_video():
            try:
                await self.send_video(chat_id, media, status_msg)
            except Exception as e:
                # Если ошибка только с видео, но фото отправлены - не критично
                logger.warning(
                    f"⚠️  Видео не удалось отправить, но фото отправлены: "
                    f"{type(e).__name__}: {e}"
                )
