"""Глобальная обработка ошибок."""

from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable
import logging
import traceback

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
            # Собираем контекстную информацию
            error_context = self._build_error_context(event, e)

            # Логируем с полным stack trace
            logger.error(
                f"❌ НЕОБРАБОТАННАЯ ОШИБКА\n"
                f"{'=' * 80}\n"
                f"{error_context}\n"
                f"{'=' * 80}\n"
                f"Exception: {type(e).__name__}: {e}\n"
                f"{'=' * 80}\n"
                f"Stack trace:\n"
                f"{traceback.format_exc()}"
                f"{'=' * 80}"
            )

            # Попытка отправить сообщение пользователю
            if event.message:
                try:
                    await event.message.answer(
                        "❌ Произошла непредвиденная ошибка. "
                        "Попробуйте позже или обратитесь к администратору."
                    )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            elif event.callback_query:
                try:
                    await event.callback_query.message.edit_text(
                        "❌ Произошла непредвиденная ошибка. "
                        "Попробуйте позже."
                    )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")

    def _build_error_context(self, event: Update, exception: Exception) -> str:
        """
        Собирает детальную информацию об ошибке для логирования.

        Args:
            event: Update событие
            exception: Возникшее исключение

        Returns:
            Строка с контекстной информацией
        """
        context_lines = []

        # Update ID
        context_lines.append(f"Update ID: {event.update_id}")

        # Информация о пользователе
        user = None
        if event.message:
            user = event.message.from_user
            context_lines.append(f"Event type: message")
            context_lines.append(f"Message text: {event.message.text[:100] if event.message.text else 'N/A'}")
            context_lines.append(f"Chat ID: {event.message.chat.id}")
        elif event.callback_query:
            user = event.callback_query.from_user
            context_lines.append(f"Event type: callback_query")
            context_lines.append(f"Callback data: {event.callback_query.data}")
            context_lines.append(f"Chat ID: {event.callback_query.message.chat.id}")
        else:
            context_lines.append(f"Event type: unknown")

        if user:
            context_lines.append(
                f"User: id={user.id}, "
                f"username=@{user.username if user.username else 'None'}, "
                f"name={user.first_name or ''} {user.last_name or ''}".strip()
            )

        # Тип исключения
        context_lines.append(f"Exception type: {type(exception).__module__}.{type(exception).__name__}")

        return "\n".join(context_lines)
