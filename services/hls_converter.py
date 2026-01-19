"""Конвертация HLS видео в MP4 для Telegram."""

import asyncio
import tempfile
import logging
import time
from pathlib import Path
from typing import Optional

from config.settings import Settings
from utils.exceptions import HLSConversionError, FFmpegNotFoundError

logger = logging.getLogger(__name__)


class HLSConverter:
    """Асинхронная конвертация HLS (m3u8) в MP4 через ffmpeg."""

    def __init__(self):
        self.settings = Settings()
        temp_dir = self.settings.HLS_TEMP_DIR
        self._temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())

    @staticmethod
    def is_hls_url(url: Optional[str]) -> bool:
        """Проверить является ли URL HLS плейлистом."""
        if not url:
            return False
        return url.endswith('.m3u8') or '/hls/' in url.lower()

    @staticmethod
    async def check_ffmpeg_available() -> bool:
        """Проверить доступность ffmpeg в системе."""
        try:
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
            return process.returncode == 0
        except FileNotFoundError:
            return False

    async def convert_hls_to_mp4(
        self,
        hls_url: str,
        nm_id: str = "video"
    ) -> Path:
        """
        Конвертировать HLS поток в MP4 файл.

        Args:
            hls_url: URL HLS плейлиста (m3u8)
            nm_id: Артикул для имени файла

        Returns:
            Path к временному MP4 файлу

        Raises:
            FFmpegNotFoundError: ffmpeg не найден
            HLSConversionError: Ошибка конвертации
        """
        # Проверка ffmpeg
        if not await self.check_ffmpeg_available():
            raise FFmpegNotFoundError(
                "ffmpeg не установлен. Установите: https://ffmpeg.org/download.html"
            )

        # Создание временного файла
        timestamp = int(time.time())
        output_path = self._temp_dir / f"wb_video_{nm_id}_{timestamp}.mp4"

        logger.info(f"🎬 Начинаю конвертацию HLS → MP4: {hls_url}")
        start_time = time.perf_counter()

        # Команда ffmpeg
        cmd = [
            self.settings.FFMPEG_PATH,
            '-i', hls_url,              # Input HLS URL
            '-c', 'copy',               # Без перекодирования
            '-bsf:a', 'aac_adtstoasc',  # Фикс AAC для MP4
            '-y',                       # Перезапись если существует
            str(output_path)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Ожидание с timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.settings.HLS_CONVERT_TIMEOUT
                )
            except asyncio.TimeoutError:
                process.kill()
                self.cleanup_temp_file(output_path)
                raise HLSConversionError(
                    f"Timeout конвертации ({self.settings.HLS_CONVERT_TIMEOUT}s)"
                )

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.cleanup_temp_file(output_path)
                raise HLSConversionError(f"ffmpeg error: {error_msg[:200]}")

            # Проверка что файл создан
            if not output_path.exists():
                raise HLSConversionError("Выходной файл не создан")

            # Проверка размера
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            elapsed = time.perf_counter() - start_time

            logger.info(
                f"✅ Конвертация завершена: {file_size_mb:.1f}MB за {elapsed:.1f}s"
            )

            if file_size_mb > self.settings.HLS_MAX_VIDEO_SIZE_MB:
                logger.warning(
                    f"⚠️ Видео {file_size_mb:.1f}MB превышает лимит "
                    f"{self.settings.HLS_MAX_VIDEO_SIZE_MB}MB"
                )

            return output_path

        except FileNotFoundError:
            raise FFmpegNotFoundError("ffmpeg не найден в PATH")

    def cleanup_temp_file(self, path: Optional[Path]) -> None:
        """Удалить временный файл."""
        if path and path.exists():
            try:
                path.unlink()
                logger.debug(f"🗑️ Удалён временный файл: {path}")
            except OSError as e:
                logger.warning(f"⚠️ Не удалось удалить {path}: {e}")
