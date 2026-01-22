"""Тесты для bot/handlers/start.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from bot.handlers.start import cmd_start, cmd_help


class TestStartHandler:
    """Тесты для обработчика команд /start и /help."""

    @pytest.mark.asyncio
    async def test_cmd_start(self, message):
        """Тест: команда /start отправляет приветственное сообщение (2 части)."""
        await cmd_start(message)

        # Проверка что было 2 вызова answer (приветствие разделено на части)
        assert message.answer.called
        assert message.answer.call_count == 2

        # Проверка первого сообщения (о проекте MPCabinet)
        first_call_args = message.answer.call_args_list[0][0][0]
        assert "MPCabinet" in first_call_args
        assert "t.me/" in first_call_args
        assert "экосистемы" in first_call_args or "экосистема" in first_call_args

        # Проверка второго сообщения (инструкция)
        second_call_args = message.answer.call_args_list[1][0][0]
        assert "артикул" in second_call_args
        assert "скачать" in second_call_args or "Чтобы скачать" in second_call_args

    @pytest.mark.asyncio
    async def test_cmd_help(self, message):
        """Тест: команда /help отправляет справку."""
        await cmd_help(message)

        # Проверка что был вызван answer
        assert message.answer.called
        assert message.answer.call_count == 1

        # Проверка текста справки
        call_args = message.answer.call_args[0][0]
        assert "Как пользоваться" in call_args
        assert "Отправьте артикул" in call_args
        assert "Примеры" in call_args
        assert "wildberries.ru" in call_args
