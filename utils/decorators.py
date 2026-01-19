"""Декораторы для логирования и мониторинга."""

import time
import logging
import functools
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
        if functools.iscoroutinefunction(func):
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

        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
