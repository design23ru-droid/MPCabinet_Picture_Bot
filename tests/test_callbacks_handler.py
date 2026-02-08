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

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_downloader = MagicMock()
            mock_downloader.send_photos = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert callback_query.answer.called
        assert callback_query.message.edit_reply_markup.called
        assert mock_downloader.send_photos.called

    @pytest.mark.asyncio
    async def test_handle_download_video(self, callback_query, bot, product_media):
        """Тест: загрузка только видео."""
        callback_query.data = "download:12345678:video"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_downloader = MagicMock()
            mock_downloader.send_video = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert callback_query.answer.called
        assert mock_downloader.send_video.called

    @pytest.mark.asyncio
    async def test_handle_download_both(self, callback_query, bot, product_media):
        """Тест: загрузка фото и видео."""
        callback_query.data = "download:12345678:both"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_downloader = MagicMock()
            mock_downloader.send_both = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert callback_query.answer.called
        assert mock_downloader.send_both.called

    @pytest.mark.asyncio
    async def test_handle_download_no_media_error(self, callback_query, bot):
        """Тест: ошибка NoMediaError."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            from services.wb_parser import ProductMedia
            empty_media = ProductMedia(
                nm_id="12345678",
                name="Без медиа",
                photos=[],
                video=None
            )
            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=empty_media)
            mock_get_client.return_value = mock_client

            mock_downloader = MagicMock()
            mock_downloader.send_photos = AsyncMock(
                side_effect=NoMediaError("У этого товара нет фотографий")
            )
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert callback_query.message.edit_text.called
        error_text = callback_query.message.edit_text.call_args[0][0]
        assert "нет фотографий" in error_text or "У этого товара" in error_text

    @pytest.mark.asyncio
    async def test_handle_download_wb_api_error(self, callback_query, bot):
        """Тест: ошибка WB API."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(
                side_effect=WBAPIError("API Error")
            )
            mock_get_client.return_value = mock_client

            await handle_download_callback(callback_query, bot)

        assert callback_query.message.edit_text.called
        error_text = callback_query.message.edit_text.call_args[0][0]
        assert "Не удалось загрузить медиа" in error_text

    @pytest.mark.asyncio
    async def test_handle_download_unexpected_error(self, callback_query, bot):
        """Тест: неожиданная ошибка."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(
                side_effect=RuntimeError("Unexpected")
            )
            mock_get_client.return_value = mock_client

            await handle_download_callback(callback_query, bot)

        assert callback_query.message.edit_text.called
        error_text = callback_query.message.edit_text.call_args[0][0]
        assert "Произошла ошибка" in error_text

    @pytest.mark.asyncio
    async def test_callback_data_parsing(self, callback_query, bot, product_media):
        """Тест: корректный парсинг callback data."""
        callback_query.data = "download:87654321:video"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_downloader = MagicMock()
            mock_downloader.send_video = AsyncMock()
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # Проверка что правильный артикул был передан
        assert mock_client.get_product_media.called
        call_args = mock_client.get_product_media.call_args
        assert call_args[0][0] == "87654321"

    @pytest.mark.asyncio
    async def test_handle_download_photos_tracks_analytics(self, callback_query, bot, product_media):
        """Тест: отправка фото вызывает track_event через GatewayAdapter."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader, \
             patch('bot.handlers.callbacks.get_gateway_adapter') as mock_get_gateway:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_gateway = AsyncMock()
            mock_gateway.track_event = AsyncMock()
            mock_get_gateway.return_value = mock_gateway

            async def mock_send_photos(chat_id, media, status_msg, on_success=None):
                if on_success:
                    await on_success(len(media.photos))

            mock_downloader = MagicMock()
            mock_downloader.send_photos = AsyncMock(side_effect=mock_send_photos)
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert mock_gateway.track_event.called
        call_args = mock_gateway.track_event.call_args
        assert call_args[0][0] == callback_query.from_user.id
        assert call_args[0][1] == "photo_sent"

    @pytest.mark.asyncio
    async def test_handle_download_video_tracks_analytics(self, callback_query, bot, product_media):
        """Тест: отправка видео вызывает track_event через GatewayAdapter."""
        callback_query.data = "download:12345678:video"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader, \
             patch('bot.handlers.callbacks.get_gateway_adapter') as mock_get_gateway:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_gateway = AsyncMock()
            mock_gateway.track_event = AsyncMock()
            mock_get_gateway.return_value = mock_gateway

            async def mock_send_video(chat_id, media, status_msg, on_success=None):
                if on_success:
                    await on_success()

            mock_downloader = MagicMock()
            mock_downloader.send_video = AsyncMock(side_effect=mock_send_video)
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert mock_gateway.track_event.called
        call_args = mock_gateway.track_event.call_args
        assert call_args[0][0] == callback_query.from_user.id
        assert call_args[0][1] == "video_sent"

    @pytest.mark.asyncio
    async def test_handle_download_both_tracks_analytics(self, callback_query, bot, product_media):
        """Тест: отправка both вызывает оба track_event."""
        callback_query.data = "download:12345678:both"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader, \
             patch('bot.handlers.callbacks.get_gateway_adapter') as mock_get_gateway:

            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=product_media)
            mock_get_client.return_value = mock_client

            mock_gateway = AsyncMock()
            mock_gateway.track_event = AsyncMock()
            mock_get_gateway.return_value = mock_gateway

            async def mock_send_both(chat_id, media, status_msg, on_photos_success=None, on_video_success=None):
                if on_photos_success:
                    await on_photos_success(len(media.photos))
                if on_video_success:
                    await on_video_success()

            mock_downloader = MagicMock()
            mock_downloader.send_both = AsyncMock(side_effect=mock_send_both)
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        assert mock_gateway.track_event.call_count >= 2
        call_types = [c[0][1] for c in mock_gateway.track_event.call_args_list]
        assert "photo_sent" in call_types
        assert "video_sent" in call_types

    @pytest.mark.asyncio
    async def test_handle_download_error_no_analytics(self, callback_query, bot):
        """Тест: при ошибке отправки аналитика не вызывается."""
        callback_query.data = "download:12345678:photo"

        with patch('bot.handlers.callbacks.get_wb_media_client') as mock_get_client, \
             patch('bot.handlers.callbacks.MediaDownloader') as MockDownloader, \
             patch('bot.handlers.callbacks.get_gateway_adapter') as mock_get_gateway:

            from services.wb_parser import ProductMedia
            empty_media = ProductMedia(
                nm_id="12345678",
                name="Без медиа",
                photos=[],
                video=None
            )
            mock_client = AsyncMock()
            mock_client.get_product_media = AsyncMock(return_value=empty_media)
            mock_get_client.return_value = mock_client

            mock_gateway = AsyncMock()
            mock_gateway.track_event = AsyncMock()
            mock_get_gateway.return_value = mock_gateway

            mock_downloader = MagicMock()
            mock_downloader.send_photos = AsyncMock(
                side_effect=NoMediaError("У этого товара нет фотографий")
            )
            MockDownloader.return_value = mock_downloader

            await handle_download_callback(callback_query, bot)

        # track_event НЕ должен вызываться для photo_sent/video_sent
        for call in mock_gateway.track_event.call_args_list:
            assert call[0][1] not in ("photo_sent", "video_sent")