"""Тесты для HLS конвертера."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from services.hls_converter import HLSConverter
from utils.exceptions import HLSConversionError, FFmpegNotFoundError


class TestIsHlsUrl:
    """Тесты для is_hls_url()."""

    def test_is_hls_url_m3u8_extension(self):
        """URL с расширением .m3u8 определяется как HLS."""
        url = "https://videonme-basket-01.wbbasket.ru/vol3/part40444/404448483/hls/1440p/index.m3u8"
        assert HLSConverter.is_hls_url(url) is True

    def test_is_hls_url_hls_in_path(self):
        """URL с /hls/ в пути определяется как HLS."""
        url = "https://example.com/hls/video/stream"
        assert HLSConverter.is_hls_url(url) is True

    def test_is_hls_url_mp4(self):
        """URL с MP4 не определяется как HLS."""
        url = "https://video.wildberries.ru/12345678/12345678.mp4"
        assert HLSConverter.is_hls_url(url) is False

    def test_is_hls_url_empty(self):
        """Пустой URL не определяется как HLS."""
        assert HLSConverter.is_hls_url("") is False

    def test_is_hls_url_none(self):
        """None не определяется как HLS."""
        assert HLSConverter.is_hls_url(None) is False

    def test_is_hls_url_case_insensitive(self):
        """Проверка /HLS/ в любом регистре."""
        url = "https://example.com/HLS/video/stream"
        assert HLSConverter.is_hls_url(url) is True


class TestCheckFfmpegAvailable:
    """Тесты для check_ffmpeg_available()."""

    @pytest.mark.asyncio
    async def test_ffmpeg_available(self):
        """ffmpeg доступен - возвращает True."""
        with patch('asyncio.create_subprocess_exec') as mock:
            process = AsyncMock()
            process.returncode = 0
            process.wait = AsyncMock()
            mock.return_value = process

            result = await HLSConverter.check_ffmpeg_available()
            assert result is True

    @pytest.mark.asyncio
    async def test_ffmpeg_not_found(self):
        """ffmpeg не найден - возвращает False."""
        with patch('asyncio.create_subprocess_exec') as mock:
            mock.side_effect = FileNotFoundError()

            result = await HLSConverter.check_ffmpeg_available()
            assert result is False

    @pytest.mark.asyncio
    async def test_ffmpeg_error_returncode(self):
        """ffmpeg вернул ошибку - возвращает False."""
        with patch('asyncio.create_subprocess_exec') as mock:
            process = AsyncMock()
            process.returncode = 1
            process.wait = AsyncMock()
            mock.return_value = process

            result = await HLSConverter.check_ffmpeg_available()
            assert result is False


class TestConvertHlsToMp4:
    """Тесты для convert_hls_to_mp4()."""

    @pytest.mark.asyncio
    async def test_convert_ffmpeg_not_found(self):
        """Ошибка если ffmpeg не установлен."""
        converter = HLSConverter()

        with patch.object(
            HLSConverter, 'check_ffmpeg_available',
            new_callable=AsyncMock,
            return_value=False
        ):
            with pytest.raises(FFmpegNotFoundError):
                await converter.convert_hls_to_mp4(
                    "https://example.com/index.m3u8"
                )

    @pytest.mark.asyncio
    async def test_convert_timeout(self):
        """Timeout при долгой конвертации."""
        converter = HLSConverter()
        converter.settings.HLS_CONVERT_TIMEOUT = 0.001  # 1ms для теста

        with patch.object(
            HLSConverter, 'check_ffmpeg_available',
            new_callable=AsyncMock,
            return_value=True
        ):
            with patch('asyncio.create_subprocess_exec') as mock:
                process = AsyncMock()

                # Имитируем долгий процесс через медленный readline
                async def slow_readline():
                    await asyncio.sleep(10)
                    return b''

                process.stdout = AsyncMock()
                process.stdout.readline = slow_readline

                process.stderr = AsyncMock()
                process.stderr.read = AsyncMock(return_value=b'')

                async def slow_wait():
                    await asyncio.sleep(10)
                    return 0

                process.wait = slow_wait
                process.kill = MagicMock()
                mock.return_value = process

                with pytest.raises(HLSConversionError, match="Timeout"):
                    await converter.convert_hls_to_mp4(
                        "https://example.com/index.m3u8"
                    )

    @pytest.mark.asyncio
    async def test_convert_ffmpeg_error(self):
        """Ошибка ffmpeg при конвертации."""
        converter = HLSConverter()

        with patch.object(
            HLSConverter, 'check_ffmpeg_available',
            new_callable=AsyncMock,
            return_value=True
        ):
            with patch('asyncio.create_subprocess_exec') as mock:
                process = AsyncMock()
                process.returncode = 1

                # Мокаем stdout.readline для чтения прогресса
                process.stdout = AsyncMock()
                process.stdout.readline = AsyncMock(return_value=b'')  # Сразу конец

                # Мокаем stderr.read для чтения ошибок
                process.stderr = AsyncMock()
                process.stderr.read = AsyncMock(return_value=b'Error: Invalid input')

                # Мокаем wait
                process.wait = AsyncMock(return_value=1)

                mock.return_value = process

                with pytest.raises(HLSConversionError, match="ffmpeg error"):
                    await converter.convert_hls_to_mp4(
                        "https://example.com/index.m3u8"
                    )

    @pytest.mark.asyncio
    async def test_convert_success(self, tmp_path):
        """Успешная конвертация."""
        converter = HLSConverter()
        converter._temp_dir = tmp_path

        # Создаём фейковый выходной файл
        fake_output = tmp_path / "wb_video_12345_123.mp4"
        fake_output.write_bytes(b'fake video content')

        with patch.object(
            HLSConverter, 'check_ffmpeg_available',
            new_callable=AsyncMock,
            return_value=True
        ):
            with patch('asyncio.create_subprocess_exec') as mock:
                process = AsyncMock()
                process.returncode = 0

                # Мокаем stdout.readline для чтения прогресса
                process.stdout = AsyncMock()
                process.stdout.readline = AsyncMock(return_value=b'')  # Сразу конец

                # Мокаем stderr.read для чтения ошибок
                process.stderr = AsyncMock()
                process.stderr.read = AsyncMock(return_value=b'')

                # Мокаем wait
                process.wait = AsyncMock(return_value=0)

                mock.return_value = process

                # Патчим генерацию имени файла
                with patch('time.time', return_value=123):
                    result = await converter.convert_hls_to_mp4(
                        "https://example.com/index.m3u8",
                        nm_id="12345"
                    )

                assert result.suffix == '.mp4'
                assert '12345' in result.name


class TestCleanupTempFile:
    """Тесты для cleanup_temp_file()."""

    def test_cleanup_existing_file(self, tmp_path):
        """Удаление существующего временного файла."""
        converter = HLSConverter()
        temp_file = tmp_path / "test_video.mp4"
        temp_file.write_text("test content")

        assert temp_file.exists()
        converter.cleanup_temp_file(temp_file)
        assert not temp_file.exists()

    def test_cleanup_nonexistent_file(self):
        """Удаление несуществующего файла - без ошибки."""
        converter = HLSConverter()
        # Не должно быть исключения
        converter.cleanup_temp_file(Path("/nonexistent/file.mp4"))

    def test_cleanup_none(self):
        """cleanup_temp_file(None) - без ошибки."""
        converter = HLSConverter()
        # Не должно быть исключения
        converter.cleanup_temp_file(None)
