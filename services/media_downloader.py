"""Загрузка и отправка медиафайлов в Telegram."""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Optional, Callable, Awaitable
from aiogram import Bot
from aiogram.types import Message, InputMediaPhoto, URLInputFile, FSInputFile

from services.wb_parser import ProductMedia
from services.hls_converter import HLSConverter
from utils.exceptions import NoMediaError, HLSConversionError, FFmpegNotFoundError
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
        status_msg: Message,
        on_success: Optional[Callable[[int], Awaitable[None]]] = None
    ) -> None:
        """
        Отправка фотографий пользователю с прогрессом.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса
            on_success: Опциональный callback, вызывается после успешной отправки с количеством фото

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

        # Вызов callback после успешной отправки
        if on_success:
            try:
                await on_success(total)
            except Exception as e:
                logger.warning(
                    f"⚠️  Ошибка в callback после отправки фото: "
                    f"{type(e).__name__}: {e}"
                )

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
        status_msg: Message,
        on_success: Optional[Callable[[], Awaitable[None]]] = None
    ) -> None:
        """
        Отправка видео пользователю.

        Если видео в HLS формате (m3u8), конвертирует в MP4 через ffmpeg.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса
            on_success: Опциональный callback, вызывается после успешной отправки видео

        Raises:
            NoMediaError: Нет видео у товара
            HLSConversionError: Ошибка конвертации HLS
            FFmpegNotFoundError: ffmpeg не установлен
        """
        if not media.has_video():
            raise NoMediaError("У этого товара нет видео")

        logger.info(
            f"🎥 Отправка видео в чат {chat_id} "
            f"(product {media.nm_id}, URL: {media.video})"
        )

        # Определяем тип видео
        is_hls = HLSConverter.is_hls_url(media.video)
        temp_path: Optional[Path] = None
        converter: Optional[HLSConverter] = None

        try:
            if is_hls:
                # HLS требует конвертации с прогрессом
                last_progress = [0]  # Используем список для изменения в замыкании

                async def update_progress(percent: int):
                    if percent > last_progress[0]:
                        last_progress[0] = percent
                        try:
                            await status_msg.edit_text(f"⬇️ Скачивание: {percent}%")
                        except Exception:
                            pass

                try:
                    await status_msg.edit_text("⬇️ Скачивание: 0%")
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось обновить прогресс: {e}")

                converter = HLSConverter()
                temp_path = await converter.download_hls_fast(
                    media.video,
                    nm_id=media.nm_id,
                    progress_callback=update_progress
                )
                video_input = FSInputFile(temp_path)

            else:
                # Прямой MP4 URL
                try:
                    await status_msg.edit_text("⬇️ Скачивание...")
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось обновить прогресс: {e}")
                video_input = URLInputFile(media.video)

            # Анимированный спиннер для отправки
            spinner_frames = ["◐", "◓", "◑", "◒"]
            spinner_running = [True]  # Флаг для остановки

            async def animate_spinner():
                frame_idx = 0
                while spinner_running[0]:
                    try:
                        await status_msg.edit_text(
                            f"📤 Отправка в Telegram {spinner_frames[frame_idx]}"
                        )
                    except Exception:
                        pass
                    frame_idx = (frame_idx + 1) % len(spinner_frames)
                    await asyncio.sleep(0.8)

            # Запускаем анимацию
            spinner_task = asyncio.create_task(animate_spinner())

            video_start = time.perf_counter()
            try:
                await self.bot.send_video(
                    chat_id=chat_id,
                    video=video_input,
                    caption=f"Видео: {media.name}",
                    request_timeout=120  # Увеличен таймаут для медленных сетей
                )
            finally:
                # Останавливаем анимацию
                spinner_running[0] = False
                spinner_task.cancel()
                try:
                    await spinner_task
                except asyncio.CancelledError:
                    pass

            video_time = time.perf_counter() - video_start

            # Вызов callback после успешной отправки
            if on_success:
                try:
                    await on_success()
                except Exception as e:
                    logger.warning(
                        f"⚠️  Ошибка в callback после отправки видео: "
                        f"{type(e).__name__}: {e}"
                    )

            # Удаляем сообщение о прогрессе
            try:
                await status_msg.delete()
            except Exception:
                pass
            logger.info(
                f"✅ Видео успешно отправлено в чат {chat_id} за {video_time:.2f}s"
            )

        except FFmpegNotFoundError:
            logger.error("❌ ffmpeg не установлен")
            try:
                await status_msg.edit_text(
                    "❌ Сервер не поддерживает HLS видео (ffmpeg не установлен)"
                )
            except Exception:
                pass
            raise

        except HLSConversionError as e:
            logger.error(f"❌ Ошибка конвертации HLS: {e}")
            try:
                await status_msg.edit_text(f"❌ Ошибка конвертации видео: {e}")
            except Exception:
                pass
            raise

        except Exception as e:
            logger.error(
                f"❌ Ошибка отправки видео: {type(e).__name__}: {e}\n"
                f"URL: {media.video}"
            )
            try:
                await status_msg.edit_text(
                    "❌ Не удалось загрузить видео. Возможно, файл слишком большой (лимит 50 MB)"
                )
            except Exception:
                pass
            raise

        finally:
            # Очистка временного файла
            if temp_path and converter:
                converter.cleanup_temp_file(temp_path)

    @log_execution_time()
    async def send_video_as_document(
        self,
        chat_id: int,
        media: ProductMedia,
        status_msg: Message
    ) -> None:
        """
        Отправка видео как документа (без превью, оригинальное качество).

        Быстрее чем send_video, так как не сжимает видео.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса

        Raises:
            NoMediaError: Нет видео у товара
            HLSConversionError: Ошибка скачивания HLS
            FFmpegNotFoundError: ffmpeg не установлен
        """
        if not media.has_video():
            raise NoMediaError("У этого товара нет видео")

        logger.info(
            f"📄 Отправка видео как документа в чат {chat_id} "
            f"(product {media.nm_id}, URL: {media.video})"
        )

        is_hls = HLSConverter.is_hls_url(media.video)
        temp_path: Optional[Path] = None
        converter: Optional[HLSConverter] = None

        try:
            if is_hls:
                last_progress = [0]

                async def update_progress(percent: int):
                    if percent > last_progress[0]:
                        last_progress[0] = percent
                        try:
                            await status_msg.edit_text(f"⬇️ Скачивание: {percent}%")
                        except Exception:
                            pass

                try:
                    await status_msg.edit_text("⬇️ Скачивание: 0%")
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось обновить прогресс: {e}")

                converter = HLSConverter()
                # Используем быстрое скачивание без сжатия
                temp_path = await converter.download_hls_fast(
                    media.video,
                    nm_id=media.nm_id,
                    progress_callback=update_progress
                )
                file_input = FSInputFile(
                    temp_path,
                    filename=f"video_{media.nm_id}.mp4"
                )
            else:
                try:
                    await status_msg.edit_text("⬇️ Скачивание...")
                except Exception as e:
                    logger.warning(f"⚠️  Не удалось обновить прогресс: {e}")
                file_input = URLInputFile(
                    media.video,
                    filename=f"video_{media.nm_id}.mp4"
                )

            # Спиннер для отправки
            spinner_frames = ["◐", "◓", "◑", "◒"]
            spinner_running = [True]

            async def animate_spinner():
                frame_idx = 0
                while spinner_running[0]:
                    try:
                        await status_msg.edit_text(
                            f"📤 Отправка в Telegram {spinner_frames[frame_idx]}"
                        )
                    except Exception:
                        pass
                    frame_idx = (frame_idx + 1) % len(spinner_frames)
                    await asyncio.sleep(0.8)

            spinner_task = asyncio.create_task(animate_spinner())

            send_start = time.perf_counter()
            try:
                await self.bot.send_document(
                    chat_id=chat_id,
                    document=file_input,
                    caption=f"📄 Видео: {media.name}",
                    request_timeout=180  # Больше таймаут для больших файлов
                )
            finally:
                spinner_running[0] = False
                spinner_task.cancel()
                try:
                    await spinner_task
                except asyncio.CancelledError:
                    pass

            send_time = time.perf_counter() - send_start

            try:
                await status_msg.delete()
            except Exception:
                pass

            logger.info(
                f"✅ Видео как документ отправлено в чат {chat_id} за {send_time:.2f}s"
            )

        except FFmpegNotFoundError:
            logger.error("❌ ffmpeg не установлен")
            try:
                await status_msg.edit_text(
                    "❌ Сервер не поддерживает HLS видео (ffmpeg не установлен)"
                )
            except Exception:
                pass
            raise

        except HLSConversionError as e:
            logger.error(f"❌ Ошибка скачивания HLS: {e}")
            try:
                await status_msg.edit_text(f"❌ Ошибка скачивания видео: {e}")
            except Exception:
                pass
            raise

        except Exception as e:
            logger.error(
                f"❌ Ошибка отправки документа: {type(e).__name__}: {e}\n"
                f"URL: {media.video}"
            )
            try:
                await status_msg.edit_text(
                    "❌ Не удалось загрузить видео. Возможно, файл слишком большой"
                )
            except Exception:
                pass
            raise

        finally:
            if temp_path and converter:
                converter.cleanup_temp_file(temp_path)

    @log_execution_time()
    async def send_both(
        self,
        chat_id: int,
        media: ProductMedia,
        status_msg: Message,
        on_photos_success: Optional[Callable[[int], Awaitable[None]]] = None,
        on_video_success: Optional[Callable[[], Awaitable[None]]] = None
    ) -> None:
        """
        Отправка фото и видео.

        Args:
            chat_id: ID чата
            media: Медиа товара
            status_msg: Сообщение для обновления прогресса
            on_photos_success: Опциональный callback после успешной отправки фото
            on_video_success: Опциональный callback после успешной отправки видео

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
            await self.send_photos(chat_id, media, status_msg, on_success=on_photos_success)

            # Если есть видео, создаем новое сообщение для прогресса
            if media.has_video():
                status_msg = await self.bot.send_message(
                    chat_id,
                    "🎥 Загружаю видео..."
                )

        # Отправка видео
        if media.has_video():
            try:
                await self.send_video(chat_id, media, status_msg, on_success=on_video_success)
            except Exception as e:
                # Если ошибка только с видео, но фото отправлены - не критично
                logger.warning(
                    f"⚠️  Видео не удалось отправить, но фото отправлены: "
                    f"{type(e).__name__}: {e}"
                )
