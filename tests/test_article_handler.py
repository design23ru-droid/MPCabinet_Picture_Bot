"""Тесты для bot/handlers/article.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.article import handle_article
from utils.exceptions import InvalidArticleError, ProductNotFoundError, WBAPIError


class TestArticleHandler:
    """Тесты для обработчика артикулов."""

    @pytest.mark.asyncio
    async def test_handle_article_success(self, message, product_media):
        """Тест: успешная обработка артикула с фото и видео."""
        message.text = "12345678"

        # Mock WBParser и keyboard
        with patch('bot.handlers.article.WBParser') as MockParser, \
             patch('bot.handlers.article.get_media_type_keyboard') as mock_keyboard:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            # Mock keyboard
            mock_keyboard.return_value = MagicMock()

            await handle_article(message)

        # Проверки
        assert message.answer.called
        status_msg = message.answer.return_value
        assert status_msg.edit_text.called

        # Проверка финального текста
        final_call = status_msg.edit_text.call_args_list[-1]
        # Извлекаем text из kwargs (второй элемент кортежа)
        final_text = final_call[1]['text']
        assert "Товар найден" in final_text
        assert "12345678" in final_text
        assert "Фото:" in final_text
        assert "wildberries.ru/catalog/12345678" in final_text

    @pytest.mark.asyncio
    async def test_handle_article_photos_only(self, message, product_media_photos_only):
        """Тест: товар только с фото."""
        message.text = "12345678"

        with patch('bot.handlers.article.WBParser') as MockParser, \
             patch('bot.handlers.article.get_media_type_keyboard') as mock_keyboard:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media_photos_only)
            MockParser.return_value = mock_parser

            mock_keyboard.return_value = MagicMock()

            await handle_article(message)

        # Проверка что было отправлено
        status_msg = message.answer.return_value
        final_call = status_msg.edit_text.call_args_list[-1]
        # Извлекаем text из kwargs (второй элемент кортежа)
        final_text = final_call[1]['text']
        assert "Товар найден" in final_text
        assert "Фото:" in final_text
        # Видео не должно быть упомянуто если его нет
        assert final_text.count("Видео:") == 0 or "Видео:" not in final_text

    @pytest.mark.asyncio
    async def test_handle_article_no_media(self, message):
        """Тест: товар без медиа."""
        message.text = "12345678"

        # Создаем ProductMedia без фото и видео
        from services.wb_parser import ProductMedia
        empty_media = ProductMedia(
            nm_id="12345678",
            name="Товар без медиа",
            photos=[],
            video=None
        )

        with patch('bot.handlers.article.WBParser') as MockParser:
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=empty_media)
            MockParser.return_value = mock_parser

            await handle_article(message)

        # Проверка что отправлена ошибка
        status_msg = message.answer.return_value
        assert status_msg.edit_text.called
        error_text = status_msg.edit_text.call_args[0][0]
        assert "нет фото" in error_text

    @pytest.mark.asyncio
    async def test_handle_article_invalid_article(self, message):
        """Тест: невалидный артикул."""
        message.text = "invalid"

        with patch('bot.handlers.article.ArticleValidator.extract_article',
                   side_effect=InvalidArticleError("Неверный формат")):
            await handle_article(message)

        # Проверка что было сообщение об ошибке
        assert message.answer.called
        error_text = message.answer.call_args[0][0]
        assert "Неверный формат" in error_text

    @pytest.mark.asyncio
    async def test_handle_article_not_found(self, message):
        """Тест: товар не найден."""
        message.text = "99999999"

        with patch('bot.handlers.article.WBParser') as MockParser:
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(
                side_effect=ProductNotFoundError("Товар не найден")
            )
            MockParser.return_value = mock_parser

            await handle_article(message)

        # Проверка сообщения об ошибке
        assert message.answer.call_count >= 2  # Сначала статус, потом ошибка
        error_call = message.answer.call_args_list[-1]
        error_text = error_call[0][0]
        assert "Товар не найден" in error_text

    @pytest.mark.asyncio
    async def test_handle_article_wb_api_error(self, message):
        """Тест: ошибка WB API."""
        message.text = "12345678"

        with patch('bot.handlers.article.WBParser') as MockParser:
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(
                side_effect=WBAPIError("API Error")
            )
            MockParser.return_value = mock_parser

            await handle_article(message)

        # Проверка сообщения об ошибке API
        error_call = message.answer.call_args_list[-1]
        error_text = error_call[0][0]
        assert "Не удалось получить данные" in error_text

    @pytest.mark.asyncio
    async def test_handle_article_unexpected_error(self, message):
        """Тест: неожиданная ошибка."""
        message.text = "12345678"

        with patch('bot.handlers.article.WBParser') as MockParser:
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            MockParser.return_value = mock_parser

            await handle_article(message)

        # Проверка сообщения об общей ошибке
        error_call = message.answer.call_args_list[-1]
        error_text = error_call[0][0]
        assert "Произошла ошибка" in error_text

    @pytest.mark.asyncio
    async def test_handle_article_url_format(self, message, product_media):
        """Тест: обработка URL вместо артикула."""
        message.text = "https://www.wildberries.ru/catalog/12345678/detail.aspx"

        with patch('bot.handlers.article.WBParser') as MockParser, \
             patch('bot.handlers.article.get_media_type_keyboard') as mock_keyboard:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            mock_keyboard.return_value = MagicMock()

            await handle_article(message)

        # Проверка успешной обработки URL
        status_msg = message.answer.return_value
        assert status_msg.edit_text.called
        final_call = status_msg.edit_text.call_args_list[-1]
        # Извлекаем text из kwargs (второй элемент кортежа)
        final_text = final_call[1]['text']
        assert "Товар найден" in final_text
