"""Тесты для utils/decorators.py"""

import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from utils.decorators import (
    log_execution_time,
    log_function_call,
    retry_on_telegram_error
)


class TestLogExecutionTime:
    """Тесты для декоратора log_execution_time."""

    def test_sync_function_success(self, caplog):
        """Тест: sync функция выполняется успешно с логированием."""
        @log_execution_time()
        def test_func():
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = test_func()

        assert result == "result"
        assert "START:" in caplog.text
        assert "test_func()" in caplog.text
        assert "завершена за" in caplog.text

    @pytest.mark.asyncio
    async def test_async_function_success(self, caplog):
        """Тест: async функция выполняется успешно с логированием."""
        @log_execution_time()
        async def test_func():
            await asyncio.sleep(0.01)
            return "async_result"

        with caplog.at_level(logging.DEBUG):
            result = await test_func()

        assert result == "async_result"
        assert "START:" in caplog.text
        assert "test_func()" in caplog.text
        assert "завершена за" in caplog.text

    def test_sync_function_with_error(self, caplog):
        """Тест: sync функция с ошибкой логирует исключение."""
        @log_execution_time()
        def test_func():
            raise ValueError("Test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match="Test error"):
                test_func()

        assert "завершилась с ошибкой" in caplog.text
        assert "Test error" in caplog.text

    @pytest.mark.asyncio
    async def test_async_function_with_error(self, caplog):
        """Тест: async функция с ошибкой логирует исключение."""
        @log_execution_time()
        async def test_func():
            raise RuntimeError("Async error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError, match="Async error"):
                await test_func()

        assert "завершилась с ошибкой" in caplog.text


class TestLogFunctionCall:
    """Тесты для декоратора log_function_call."""

    def test_function_call_without_args_logging(self, caplog):
        """Тест: логирование вызова без аргументов."""
        @log_function_call(log_args=False)
        def test_func(a, b):
            return a + b

        with caplog.at_level(logging.DEBUG):
            result = test_func(1, 2)

        assert result == 3
        assert "CALL:" in caplog.text
        assert "test_func()" in caplog.text
        # Не должно быть аргументов
        assert "args=" not in caplog.text

    def test_function_call_with_args_logging(self, caplog):
        """Тест: логирование вызова с аргументами."""
        @log_function_call(log_args=True)
        def test_func(a, b, c=None):
            return a + b

        with caplog.at_level(logging.DEBUG):
            result = test_func(5, 10, c="test")

        assert result == 15
        assert "CALL:" in caplog.text
        assert "test_func(args=" in caplog.text
        assert "kwargs=" in caplog.text

    @pytest.mark.asyncio
    async def test_async_function_call(self, caplog):
        """Тест: логирование async функции."""
        @log_function_call(log_args=True)
        async def test_func(x):
            await asyncio.sleep(0.01)
            return x * 2

        with caplog.at_level(logging.DEBUG):
            result = await test_func(5)

        assert result == 10
        assert "CALL:" in caplog.text
        assert "test_func(args=(5,)" in caplog.text


class TestRetryOnTelegramError:
    """Тесты для декоратора retry_on_telegram_error."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """Тест: успех с первой попытки."""
        mock_func = AsyncMock(return_value="success")

        @retry_on_telegram_error(max_retries=3, delay=0.1)
        async def test_func():
            return await mock_func()

        result = await test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_then_success(self, caplog):
        """Тест: ошибка → retry → успех."""
        call_count = 0

        # Создаем кастомный класс сетевой ошибки
        class TelegramNetworkError(Exception):
            pass

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Первый вызов - сетевая ошибка
                raise TelegramNetworkError("Connection failed")
            return "success"

        @retry_on_telegram_error(max_retries=3, delay=0.05)
        async def test_func():
            return await failing_then_success()

        with caplog.at_level(logging.WARNING):
            result = await test_func()

        assert result == "success"
        assert call_count == 2
        assert "попытка 1/3 неудачна" in caplog.text
        assert "Повтор через" in caplog.text

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, caplog):
        """Тест: превышение максимального количества попыток."""
        # Создаем кастомный класс сетевой ошибки
        class TelegramNetworkError(Exception):
            pass

        @retry_on_telegram_error(max_retries=2, delay=0.05)
        async def test_func():
            raise TelegramNetworkError("Always fail")

        with caplog.at_level(logging.WARNING):
            with pytest.raises(TelegramNetworkError, match="Always fail"):
                await test_func()

        assert "попытка 1/2 неудачна" in caplog.text
        assert "завершилась с ошибкой после 2 попыток" in caplog.text

    @pytest.mark.asyncio
    async def test_non_network_error_no_retry(self, caplog):
        """Тест: не сетевая ошибка → выброс без retry."""
        @retry_on_telegram_error(max_retries=3, delay=0.1)
        async def test_func():
            raise ValueError("Regular error, not network")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match="Regular error"):
                await test_func()

        # Должна быть ошибка, но без retry (не сетевая)
        assert "завершилась с ошибкой после 1 попыток" in caplog.text
        assert "попытка" not in caplog.text  # Warning о повторах не будет

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Тест: экспоненциальная задержка."""
        # Создаем кастомный класс сетевой ошибки
        class TelegramNetworkError(Exception):
            pass

        delays = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays.append(delay)
            await original_sleep(0)  # Не тормозим тест

        with patch('asyncio.sleep', side_effect=mock_sleep):
            @retry_on_telegram_error(max_retries=3, delay=1.0)
            async def test_func():
                raise TelegramNetworkError("Always fail")

            with pytest.raises(TelegramNetworkError):
                await test_func()

        # Проверка экспоненциальной задержки: 1s, 2s, 4s
        assert len(delays) == 2  # 2 retry (3 попытки = 2 задержки)
        assert delays[0] == 1.0  # delay * 2^0
        assert delays[1] == 2.0  # delay * 2^1

    @pytest.mark.asyncio
    async def test_timeout_error_is_retried(self, caplog):
        """Тест: TimeoutError считается сетевой ошибкой."""
        call_count = 0

        async def failing_with_timeout():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Request timeout")
            return "recovered"

        @retry_on_telegram_error(max_retries=3, delay=0.05)
        async def test_func():
            return await failing_with_timeout()

        result = await test_func()

        assert result == "recovered"
        assert call_count == 2
