"""Конфигурация и фикстуры для pytest."""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot
from aiogram.types import User, Chat, Message, CallbackQuery
from aioresponses import aioresponses

from services.wb_parser import ProductMedia


@pytest.fixture(scope="session")
def event_loop():
    """Общий event loop для всех async тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def bot():
    """Mock бота Telegram."""
    bot_mock = MagicMock(spec=Bot)
    bot_mock.send_message = AsyncMock()
    bot_mock.send_media_group = AsyncMock()
    bot_mock.send_video = AsyncMock()
    return bot_mock


@pytest.fixture
def user():
    """Тестовый пользователь."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser"
    )


@pytest.fixture
def chat():
    """Тестовый чат."""
    return Chat(id=123456789, type="private")


@pytest.fixture
def message(user, chat):
    """Mock сообщения."""
    msg = MagicMock(spec=Message)
    msg.from_user = user
    msg.chat = chat
    msg.message_id = 1
    msg.text = "12345678"
    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    msg.delete = AsyncMock()
    return msg


@pytest.fixture
def callback_query(user, message):
    """Mock callback query."""
    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = user
    cb.message = message
    cb.data = "download:12345678:photo"
    cb.answer = AsyncMock()
    return cb


@pytest.fixture
def product_media():
    """Тестовый ProductMedia."""
    return ProductMedia(
        nm_id="12345678",
        name="Тестовый товар",
        photos=[
            "https://basket-01.wbbasket.ru/vol123/part12345/12345678/images/big/1.webp",
            "https://basket-01.wbbasket.ru/vol123/part12345/12345678/images/big/2.webp",
            "https://basket-01.wbbasket.ru/vol123/part12345/12345678/images/big/3.webp",
        ],
        video="https://video.wildberries.ru/12345678/12345678.mp4"
    )


@pytest.fixture
def product_media_photos_only():
    """ProductMedia только с фото."""
    return ProductMedia(
        nm_id="12345678",
        name="Товар без видео",
        photos=[
            "https://basket-01.wbbasket.ru/vol123/part12345/12345678/images/big/1.webp",
        ],
        video=None
    )


@pytest.fixture
def product_media_video_only():
    """ProductMedia только с видео."""
    return ProductMedia(
        nm_id="12345678",
        name="Товар без фото",
        photos=[],
        video="https://video.wildberries.ru/12345678/12345678.mp4"
    )


@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp responses."""
    with aioresponses() as m:
        yield m
