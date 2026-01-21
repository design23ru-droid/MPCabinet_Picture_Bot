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

    @staticmethod
    async def get_duration(url: str) -> float:
        """Получить длительность видео через ffprobe."""
        try:
            process = await asyncio.create_subprocess_exec(
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=15)
            duration = float(stdout.decode().strip())
            return duration
        except Exception:
            return 0.0  # Неизвестная длительность

    async def convert_hls_to_mp4(
        self,
        hls_url: str,
        nm_id: str = "video",
        progress_callback: callable = None
    ) -> Path:
        """
        Конвертировать HLS поток в MP4 файл.

        Args:
            hls_url: URL HLS плейлиста (m3u8)
            nm_id: Артикул для имени файла
            progress_callback: async callback(percent: int) для обновления прогресса

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

        # Получаем длительность для расчёта прогресса
        duration = await self.get_duration(hls_url) if progress_callback else 0
        logger.debug(f"Video duration: {duration:.1f}s")

        # Команда ffmpeg с сжатием и прогрессом
        cmd = [
            self.settings.FFMPEG_PATH,
            '-i', hls_url,                          # Input HLS URL
            '-c:v', 'libx264',                      # Видео кодек H.264
            '-crf', str(self.settings.VIDEO_CRF),  # Качество (28 = ~50% размера)
            '-preset', self.settings.VIDEO_PRESET, # Скорость кодирования
            '-c:a', 'aac',                          # Аудио кодек AAC
            '-b:a', '128k',                         # Битрейт аудио
            '-y',                                   # Перезапись если существует
            '-progress', 'pipe:1',                  # Прогресс в stdout
            str(output_path)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Асинхронное чтение прогресса
            last_percent = 0
            stderr_data = b""

            async def read_progress():
                nonlocal last_percent
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode().strip()
                    if line_str.startswith('out_time_us=') and duration > 0:
                        try:
                            out_time_us = int(line_str.split('=')[1])
                            out_time_s = out_time_us / 1_000_000
                            # Прогресс 0-80% для конвертации
                            percent = min(int((out_time_s / duration) * 80), 80)
                            if percent > last_percent and percent % 10 == 0:
                                last_percent = percent
                                if progress_callback:
                                    await progress_callback(percent)
                        except (ValueError, ZeroDivisionError):
                            pass

            async def read_stderr():
                nonlocal stderr_data
                stderr_data = await process.stderr.read()

            # Запускаем чтение и ждём завершения
            try:
                await asyncio.wait_for(
                    asyncio.gather(read_progress(), read_stderr(), process.wait()),
                    timeout=self.settings.HLS_CONVERT_TIMEOUT
                )
            except asyncio.TimeoutError:
                process.kill()
                self.cleanup_temp_file(output_path)
                raise HLSConversionError(
                    f"Timeout конвертации ({self.settings.HLS_CONVERT_TIMEOUT}s)"
                )

            if process.returncode != 0:
                error_msg = stderr_data.decode() if stderr_data else "Unknown error"
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
