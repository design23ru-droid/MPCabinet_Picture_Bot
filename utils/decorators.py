"""Декораторы для логирования и мониторинга."""

import time
import logging
import functools
import inspect
from typing import Callable, Any


def log_execution_time(logger: logging.Logger = None):
    """
    Декоратор для логирования времени выполнения функции.

    Args:
        logger: Logger для вывода. Если None, используется logger модуля функции

    Usage:
        @log_execution_time()
        async def my_function():
            ...

        @log_execution_time(logger=custom_logger)
        def another_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            func_name = func.__qualname__
            start_time = time.perf_counter()

            logger.debug(f"⏱️  START: {func_name}()")

            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                logger.info(f"✅ {func_name}() завершена за {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(
                    f"❌ {func_name}() завершилась с ошибкой за {elapsed:.3f}s: {e}"
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            func_name = func.__qualname__
            start_time = time.perf_counter()

            logger.debug(f"⏱️  START: {func_name}()")

            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                logger.info(f"✅ {func_name}() завершена за {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(
                    f"❌ {func_name}() завершилась с ошибкой за {elapsed:.3f}s: {e}"
                )
                raise

        # Определяем, async или sync функция
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_function_call(logger: logging.Logger = None, log_args: bool = False):
    """
    Декоратор для детального логирования вызовов функций.

    Args:
        logger: Logger для вывода
        log_args: Логировать ли аргументы функции (может содержать чувствительные данные!)

    Usage:
        @log_function_call(log_args=True)
        async def process_data(data_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            func_name = func.__qualname__

            if log_args:
                logger.debug(f"📞 CALL: {func_name}(args={args}, kwargs={kwargs})")
            else:
                logger.debug(f"📞 CALL: {func_name}()")

            result = await func(*args, **kwargs)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            func_name = func.__qualname__

            if log_args:
                logger.debug(f"📞 CALL: {func_name}(args={args}, kwargs={kwargs})")
            else:
                logger.debug(f"📞 CALL: {func_name}()")

            result = func(*args, **kwargs)
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_telegram_error(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для автоматических повторов при сетевых ошибках Telegram.

    Args:
        max_retries: Максимальное количество попыток
        delay: Начальная задержка между попытками (секунды)

    Usage:
        @retry_on_telegram_error(max_retries=3, delay=1.0)
        async def send_message():
            await bot.send_message(...)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            func_name = func.__qualname__

            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Проверяем, является ли это сетевой ошибкой Telegram
                    error_name = type(e).__name__
                    is_network_error = (
                        'TelegramNetworkError' in error_name or
                        'ClientConnectorError' in error_name or
                        'ClientOSError' in error_name or
                        'TimeoutError' in error_name or
                        'ServerDisconnectedError' in error_name
                    )

                    if not is_network_error or attempt >= max_retries:
                        # Не сетевая ошибка или последняя попытка - пробрасываем
                        logger.error(
                            f"❌ {func_name}() завершилась с ошибкой после {attempt} попыток: "
                            f"{error_name}: {e}"
                        )
                        raise

                    # Сетевая ошибка, повторяем
                    retry_delay = delay * (2 ** (attempt - 1))  # Экспоненциальная задержка
                    logger.warning(
                        f"⚠️  {func_name}() попытка {attempt}/{max_retries} неудачна: "
                        f"{error_name}. Повтор через {retry_delay:.1f}s..."
                    )

                    import asyncio
                    await asyncio.sleep(retry_delay)

            # Не должны сюда попасть, но на всякий случай
            raise last_exception

        return wrapper
    return decorator
