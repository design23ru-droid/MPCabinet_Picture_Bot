"""Тесты для bot/handlers/callbacks.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.callbacks import handle_download_callback
from utils.exceptions import NoMediaError, WBAPIError


class TestCallbacksHandler:
    """Тесты для обработчика callback запросов."""

    @pytest.mark.asyncio
    async def test_handle_download_photos(self, callback_query, bot, product_media):
        """Тест: загрузка только фото."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.WBParser') as MockParser, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            # Mock WBParser
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            # Mock MediaDownloader
            mock_downloader = MagicMock()
            mock_downloader.send_photos = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # Проверки
        assert callback_query.answer.called
        assert callback_query.message.edit_reply_markup.called
        assert mock_downloader.send_photos.called

    @pytest.mark.asyncio
    async def test_handle_download_video(self, callback_query, bot, product_media):
        """Тест: загрузка только видео."""
        callback_query.data = "download:12345678:video"

        with patch('bot.handlers.callbacks.WBParser') as MockParser, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            mock_downloader = MagicMock()
            mock_downloader.send_video = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # Проверки
        assert callback_query.answer.called
        assert mock_downloader.send_video.called

    @pytest.mark.asyncio
    async def test_handle_download_both(self, callback_query, bot, product_media):
        """Тест: загрузка фото и видео."""
        callback_query.data = "download:12345678:both"

        with patch('bot.handlers.callbacks.WBParser') as MockParser, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            mock_downloader = MagicMock()
            mock_downloader.send_both = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # Проверки
        assert callback_query.answer.called
        assert mock_downloader.send_both.called

    @pytest.mark.asyncio
    async def test_handle_download_no_media_error(self, callback_query, bot):
        """Тест: ошибка NoMediaError."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.WBParser') as MockParser, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None

            # Создаем товар без медиа
            from services.wb_parser import ProductMedia
            empty_media = ProductMedia(
                nm_id="12345678",
                name="Без медиа",
                photos=[],
                video=None
            )
            mock_parser.get_product_media = AsyncMock(return_value=empty_media)
            MockParser.return_value = mock_parser

            mock_downloader = MagicMock()
            mock_downloader.send_photos = AsyncMock(
                side_effect=NoMediaError("У этого товара нет фотографий")
            )
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # Проверка что сообщение об ошибке было отправлено
        assert callback_query.message.edit_text.called
        error_text = callback_query.message.edit_text.call_args[0][0]
        assert "нет фотографий" in error_text or "У этого товара" in error_text

    @pytest.mark.asyncio
    async def test_handle_download_wb_api_error(self, callback_query, bot):
        """Тест: ошибка WB API."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.WBParser') as MockParser:
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(
                side_effect=WBAPIError("API Error")
            )
            MockParser.return_value = mock_parser

            await handle_download_callback(callback_query, bot)

        # Проверка сообщения об ошибке
        assert callback_query.message.edit_text.called
        error_text = callback_query.message.edit_text.call_args[0][0]
        assert "Не удалось загрузить медиа" in error_text

    @pytest.mark.asyncio
    async def test_handle_download_unexpected_error(self, callback_query, bot):
        """Тест: неожиданная ошибка."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.WBParser') as MockParser:
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(
                side_effect=RuntimeError("Unexpected")
            )
            MockParser.return_value = mock_parser

            await handle_download_callback(callback_query, bot)

        # Проверка сообщения об ошибке
        assert callback_query.message.edit_text.called
        error_text = callback_query.message.edit_text.call_args[0][0]
        assert "Произошла ошибка" in error_text

    @pytest.mark.asyncio
    async def test_callback_data_parsing(self, callback_query, bot, product_media):
        """Тест: корректный парсинг callback data."""
        callback_query.data = "download:87654321:video"

        with patch('bot.handlers.callbacks.WBParser') as MockParser, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            mock_downloader = MagicMock()
            mock_downloader.send_video = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # Проверка что правильный артикул был передан
        assert mock_parser.get_product_media.called
        call_args = mock_parser.get_product_media.call_args[0][0]
        assert call_args == "87654321"
