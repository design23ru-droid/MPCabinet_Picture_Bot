"""Глобальная обработка ошибок."""

from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable
import logging

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для глобальной обработки ошибок."""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с перехватом ошибок.

        Args:
            handler: Следующий handler в цепочке
            event: Update событие
            data: Данные контекста

        Returns:
            Результат handler или None при ошибке
        """
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Unhandled error: {e}")

            # Попытка отправить сообщение пользователю
            if event.message:
                try:
                    await event.message.answer(
                        "❌ Произошла непредвиденная ошибка. "
                        "Попробуйте позже или обратитесь к администратору."
                    )
                except Exception:
                    pass
            elif event.callback_query:
                try:
                    await event.callback_query.message.edit_text(
                        "❌ Произошла непредвиденная ошибка. "
                        "Попробуйте позже."
                    )
                except Exception:
                    pass
