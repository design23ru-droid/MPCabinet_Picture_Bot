"""Тесты для services/media_downloader.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.media_downloader import MediaDownloader
from utils.exceptions import NoMediaError


class TestMediaDownloader:
    """Тесты для MediaDownloader."""

    @pytest.mark.asyncio
    async def test_send_photos_success(self, bot, product_media, message):
        """Тест: успешная отправка фотографий."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789
        status_msg = message

        await downloader.send_photos(chat_id, product_media, status_msg)

        # Проверка что send_media_group был вызван
        assert bot.send_media_group.called
        # 3 фото в product_media - должна быть 1 группа
        assert bot.send_media_group.call_count == 1

        # Проверка что прогресс обновлялся
        assert status_msg.edit_text.called

        # Проверка что сообщение удалено
        assert status_msg.delete.called

    @pytest.mark.asyncio
    async def test_send_photos_multiple_batches(self, bot, message):
        """Тест: отправка фото группами по 10."""
        from services.wb_parser import ProductMedia

        # Создаем товар с 25 фото (3 группы: 10, 10, 5)
        photos = [f"https://example.com/photo{i}.webp" for i in range(1, 26)]
        media = ProductMedia(
            nm_id="12345678",
            name="Много фото",
            photos=photos,
            video=None
        )

        downloader = MediaDownloader(bot)
        chat_id = 123456789

        await downloader.send_photos(chat_id, media, message)

        # Проверка что было 3 вызова send_media_group
        assert bot.send_media_group.call_count == 3

        # Проверка размеров групп
        calls = bot.send_media_group.call_args_list
        assert len(calls[0][1]['media']) == 10  # Первая группа
        assert len(calls[1][1]['media']) == 10  # Вторая группа
        assert len(calls[2][1]['media']) == 5   # Третья группа

    @pytest.mark.asyncio
    async def test_send_photos_no_photos_error(self, bot, message):
        """Тест: ошибка при отсутствии фото."""
        from services.wb_parser import ProductMedia

        media = ProductMedia(
            nm_id="12345678",
            name="Без фото",
            photos=[],
            video="https://example.com/video.mp4"
        )

        downloader = MediaDownloader(bot)
        chat_id = 123456789

        with pytest.raises(NoMediaError, match="нет фотографий"):
            await downloader.send_photos(chat_id, media, message)

    @pytest.mark.asyncio
    async def test_send_video_success(self, bot, product_media, message):
        """Тест: успешная отправка видео."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        await downloader.send_video(chat_id, product_media, message)

        # Проверка что send_video был вызван
        assert bot.send_video.called
        assert bot.send_video.call_count == 1

        # Проверка параметров
        call_kwargs = bot.send_video.call_args[1]
        assert call_kwargs['chat_id'] == chat_id
        assert call_kwargs['caption'] == f"Видео: {product_media.name}"
        assert call_kwargs['request_timeout'] == 120

        # Проверка что прогресс обновлялся
        assert message.edit_text.called

        # Проверка что сообщение удалено после успеха
        assert message.delete.called

    @pytest.mark.asyncio
    async def test_send_video_no_video_error(self, bot, message):
        """Тест: ошибка при отсутствии видео."""
        from services.wb_parser import ProductMedia

        media = ProductMedia(
            nm_id="12345678",
            name="Без видео",
            photos=["https://example.com/photo1.webp"],
            video=None
        )

        downloader = MediaDownloader(bot)
        chat_id = 123456789

        with pytest.raises(NoMediaError, match="нет видео"):
            await downloader.send_video(chat_id, media, message)

    @pytest.mark.asyncio
    async def test_send_video_send_error(self, bot, product_media, message):
        """Тест: ошибка при отправке видео."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        # Настройка ошибки при отправке
        bot.send_video.side_effect = RuntimeError("Send failed")

        with pytest.raises(RuntimeError, match="Send failed"):
            await downloader.send_video(chat_id, product_media, message)

        # Проверка что было обновлено сообщение об ошибке
        assert message.edit_text.call_count >= 2  # Сначала "Загружаю", потом ошибка

    @pytest.mark.asyncio
    async def test_send_both_photos_and_video(self, bot, product_media, message):
        """Тест: отправка фото и видео."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        # Mock для bot.send_message (создание нового status_msg для видео)
        new_status_msg = MagicMock()
        new_status_msg.edit_text = AsyncMock()
        new_status_msg.delete = AsyncMock()
        bot.send_message = AsyncMock(return_value=new_status_msg)

        await downloader.send_both(chat_id, product_media, message)

        # Проверка что отправлены и фото и видео
        assert bot.send_media_group.called
        assert bot.send_video.called

        # Проверка что создано новое сообщение для видео
        assert bot.send_message.called

    @pytest.mark.asyncio
    async def test_send_both_only_photos(self, bot, message):
        """Тест: send_both с только фото."""
        from services.wb_parser import ProductMedia

        media = ProductMedia(
            nm_id="12345678",
            name="Только фото",
            photos=["https://example.com/photo1.webp"],
            video=None
        )

        downloader = MediaDownloader(bot)
        chat_id = 123456789

        await downloader.send_both(chat_id, media, message)

        # Проверка что отправлены только фото
        assert bot.send_media_group.called
        assert not bot.send_video.called

    @pytest.mark.asyncio
    async def test_send_both_only_video(self, bot, message):
        """Тест: send_both с только видео."""
        from services.wb_parser import ProductMedia

        media = ProductMedia(
            nm_id="12345678",
            name="Только видео",
            photos=[],
            video="https://example.com/video.mp4"
        )

        downloader = MediaDownloader(bot)
        chat_id = 123456789

        await downloader.send_both(chat_id, media, message)

        # Проверка что отправлено только видео
        assert not bot.send_media_group.called
        assert bot.send_video.called

    @pytest.mark.asyncio
    async def test_send_both_no_media_error(self, bot, message):
        """Тест: ошибка при отсутствии медиа."""
        from services.wb_parser import ProductMedia

        media = ProductMedia(
            nm_id="12345678",
            name="Без медиа",
            photos=[],
            video=None
        )

        downloader = MediaDownloader(bot)
        chat_id = 123456789

        with pytest.raises(NoMediaError, match="нет медиафайлов"):
            await downloader.send_both(chat_id, media, message)

    @pytest.mark.asyncio
    async def test_send_both_video_error_graceful(self, bot, product_media, message, caplog):
        """Тест: send_both продолжает работу если видео не удалось отправить."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        # Mock для bot.send_message
        new_status_msg = MagicMock()
        new_status_msg.edit_text = AsyncMock()
        new_status_msg.delete = AsyncMock()
        bot.send_message = AsyncMock(return_value=new_status_msg)

        # Видео не отправляется, но фото отправлены
        bot.send_video.side_effect = RuntimeError("Video failed")

        # Не должно быть исключения
        await downloader.send_both(chat_id, product_media, message)

        # Проверка что фото были отправлены
        assert bot.send_media_group.called

        # Проверка что была попытка отправить видео
        assert bot.send_video.called

        # Проверка логирования предупреждения
        assert "Видео не удалось отправить" in caplog.text

    @pytest.mark.asyncio
    async def test_send_photos_with_callback_success(self, bot, product_media, message):
        """Тест: send_photos вызывает callback после успешной отправки."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        # Callback для отслеживания вызова
        callback_called = []

        async def on_success(count: int):
            callback_called.append(count)

        await downloader.send_photos(
            chat_id, product_media, message, on_success=on_success
        )

        # Проверка что callback был вызван с правильным количеством фото
        assert len(callback_called) == 1
        assert callback_called[0] == len(product_media.photos)

        # Проверка что отправка прошла успешно
        assert bot.send_media_group.called

    @pytest.mark.asyncio
    async def test_send_photos_with_callback_error(self, bot, product_media, message, caplog):
        """Тест: send_photos продолжает работу если callback кидает exception."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        async def on_success(count: int):
            raise ValueError("Callback error")

        # Не должно быть исключения из-за ошибки в callback
        await downloader.send_photos(
            chat_id, product_media, message, on_success=on_success
        )

        # Проверка что отправка прошла успешно
        assert bot.send_media_group.called

        # Проверка что ошибка callback была залогирована
        assert "Ошибка в callback после отправки фото" in caplog.text
        assert "ValueError" in caplog.text

    @pytest.mark.asyncio
    async def test_send_video_with_callback_success(self, bot, product_media, message):
        """Тест: send_video вызывает callback после успешной отправки."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        # Callback для отслеживания вызова
        callback_called = [False]

        async def on_success():
            callback_called[0] = True

        await downloader.send_video(
            chat_id, product_media, message, on_success=on_success
        )

        # Проверка что callback был вызван
        assert callback_called[0] is True

        # Проверка что отправка прошла успешно
        assert bot.send_video.called

    @pytest.mark.asyncio
    async def test_send_video_with_callback_error(self, bot, product_media, message, caplog):
        """Тест: send_video продолжает работу если callback кидает exception."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        async def on_success():
            raise RuntimeError("Callback failed")

        # Не должно быть исключения из-за ошибки в callback
        await downloader.send_video(
            chat_id, product_media, message, on_success=on_success
        )

        # Проверка что отправка прошла успешно
        assert bot.send_video.called

        # Проверка что ошибка callback была залогирована
        assert "Ошибка в callback после отправки видео" in caplog.text
        assert "RuntimeError" in caplog.text

    @pytest.mark.asyncio
    async def test_send_both_with_callbacks_success(self, bot, product_media, message):
        """Тест: send_both вызывает оба callback после успешной отправки."""
        downloader = MediaDownloader(bot)
        chat_id = 123456789

        # Mock для bot.send_message
        new_status_msg = MagicMock()
        new_status_msg.edit_text = AsyncMock()
        new_status_msg.delete = AsyncMock()
        bot.send_message = AsyncMock(return_value=new_status_msg)

        # Callbacks для отслеживания вызовов
        photos_callback_called = []
        video_callback_called = [False]

        async def on_photos_success(count: int):
            photos_callback_called.append(count)

        async def on_video_success():
            video_callback_called[0] = True

        await downloader.send_both(
            chat_id,
            product_media,
            message,
            on_photos_success=on_photos_success,
            on_video_success=on_video_success
        )

        # Проверка что оба callback были вызваны
        assert len(photos_callback_called) == 1
        assert photos_callback_called[0] == len(product_media.photos)
        assert video_callback_called[0] is True

        # Проверка что отправлены и фото и видео
        assert bot.send_media_group.called
        assert bot.send_video.called
