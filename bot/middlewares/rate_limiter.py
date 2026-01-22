"""Rate limiting middleware для защиты от спама."""

import time
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config.settings import Settings

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов от пользователей."""

    def __init__(self):
        self.settings = Settings()
        self._user_last_request: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Проверка rate limit перед обработкой сообщения.

        Args:
            handler: Следующий handler в цепочке
            event: Message событие
            data: Данные контекста

        Returns:
            Результат handler или None если rate limit превышен
        """
        user_id = event.from_user.id
        current_time = time.time()
        limit_seconds = self.settings.RATE_LIMIT_SECONDS

        # Проверяем время последнего запроса
        last_request = self._user_last_request.get(user_id, 0)
        time_passed = current_time - last_request

        if time_passed < limit_seconds:
            # Rate limit превышен
            wait_time = int(limit_seconds - time_passed) + 1
            logger.debug(
                f"Rate limit для user {user_id}: "
                f"прошло {time_passed:.1f}s, нужно {limit_seconds}s"
            )
            await event.answer(
                f"⏳ Вы отправляете слишком часто.\n"
                f"Подождите {wait_time} сек., после чего можно снова отправлять запросы."
            )
            return None

        # Сохраняем время запроса
        self._user_last_request[user_id] = current_time

        # Периодическая очистка старых записей (каждые 100 запросов)
        if len(self._user_last_request) > 1000:
            self._cleanup_old_entries(current_time)

        return await handler(event, data)

    def _cleanup_old_entries(self, current_time: float) -> None:
        """Удаление записей старше 1 часа."""
        hour_ago = current_time - 3600
        self._user_last_request = {
            user_id: timestamp
            for user_id, timestamp in self._user_last_request.items()
            if timestamp > hour_ago
        }
        logger.debug(f"Rate limiter cleanup: осталось {len(self._user_last_request)} записей")
