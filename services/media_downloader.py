"""Загрузка и отправка медиафайлов в Telegram."""

import asyncio
import logging
from typing import List
from aiogram import Bot
from aiogram.types import Message, InputMediaPhoto, URLInputFile

from services.wb_parser import ProductMedia
from utils.exceptions import NoMediaError

logger = logging.getLogger(__name__)


class MediaDownloader:
    """Загрузка и отправка медиа в Telegram."""

    def __init__(self, bot: Bot):
        self.bot = bot

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
        logger.info(f"Sending {total} photos to chat {chat_id}")

        # Отправка группами по 10 (лимит sendMediaGroup)
        for i in range(0, total, 10):
            batch = media.photos[i:i+10]

            # Обновление прогресса
            progress = min(i + len(batch), total)
            try:
                await status_msg.edit_text(
                    f"📷 Загружаю фото {progress}/{total}..."
                )
            except Exception as e:
                logger.warning(f"Could not update progress message: {e}")

            # Создание media group
            media_group = [
                InputMediaPhoto(media=URLInputFile(url))
                for url in batch
            ]

            try:
                await self.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                await asyncio.sleep(0.5)  # Задержка между группами

            except Exception as e:
                logger.error(f"Error sending photos batch {i//10 + 1}: {e}")
                raise

        # Удаление сообщения о прогрессе
        try:
            await status_msg.delete()
        except Exception:
            pass

        logger.info(f"Successfully sent {total} photos to chat {chat_id}")

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

        logger.info(f"Sending video to chat {chat_id}")

        try:
            await status_msg.edit_text("🎥 Загружаю видео...")
        except Exception as e:
            logger.warning(f"Could not update progress message: {e}")

        try:
            await self.bot.send_video(
                chat_id=chat_id,
                video=URLInputFile(media.video),
                caption=f"Видео: {media.name}"
            )
            await status_msg.delete()
            logger.info(f"Successfully sent video to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error sending video: {e}")
            # Может быть файл слишком большой или недоступен
            try:
                await status_msg.edit_text(
                    "❌ Не удалось загрузить видео. Возможно, файл слишком большой (лимит 20 MB для URL)"
                )
            except Exception:
                pass
            raise

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
                logger.warning(f"Video failed but photos sent: {e}")
