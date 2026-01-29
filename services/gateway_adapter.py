"""
GatewayAdapter - Адаптер для интеграции с API Gateway.

Feature Flag: USE_GATEWAY
- True: вызовы через api-gateway-client (микросервисы)
- False: локальная БД (текущая логика)

При ошибке Gateway автоматически происходит fallback на локальную БД.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class UserRegistrationResult:
    """Результат регистрации пользователя."""
    telegram_id: int
    username: Optional[str]
    is_new: bool


class GatewayAdapter:
    """
    Адаптер для работы с API Gateway или локальной БД.

    Использует Feature Flag USE_GATEWAY для выбора backend:
    - USE_GATEWAY=True: вызовы через api-gateway-client
    - USE_GATEWAY=False: локальная БД (analytics)

    При ошибке Gateway автоматически происходит fallback на локальную БД.
    """

    def __init__(self):
        """Инициализация адаптера."""
        settings = get_settings()
        self.use_gateway = settings.USE_GATEWAY
        self.gateway_url = settings.GATEWAY_URL
        self.api_key = settings.GATEWAY_API_KEY
        self.timeout = settings.GATEWAY_TIMEOUT

        # Lazy-init для локальных сервисов
        self._analytics = None

        logger.info(
            f"GatewayAdapter инициализирован: USE_GATEWAY={self.use_gateway}, "
            f"URL={self.gateway_url if self.use_gateway else 'N/A'}"
        )

    def _get_analytics(self):
        """Lazy initialization для AnalyticsService."""
        if self._analytics is None:
            from services.analytics import AnalyticsService
            self._analytics = AnalyticsService()
        return self._analytics

    def _create_client(self):
        """Создаёт API Gateway Client."""
        try:
            from api_gateway_client import APIGatewayClient
            return APIGatewayClient(
                base_url=self.gateway_url,
                api_key=self.api_key,
                timeout=float(self.timeout)
            )
        except ImportError:
            logger.error("api_gateway_client не установлен! pip install api-gateway-client")
            raise

    async def register_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str]
    ) -> UserRegistrationResult:
        """
        Регистрация пользователя.

        При USE_GATEWAY=True: вызов client.users.register()
        При USE_GATEWAY=False: вызов analytics.track_user_start()
        При ошибке Gateway: fallback на локальную БД.

        Args:
            user_id: Telegram ID пользователя
            username: Username (без @)
            first_name: Имя
            last_name: Фамилия

        Returns:
            UserRegistrationResult с информацией о регистрации
        """
        if self.use_gateway:
            try:
                return await self._register_user_via_gateway(
                    user_id, username, first_name
                )
            except Exception as e:
                logger.warning(
                    f"Gateway ошибка при register_user: {e}. Fallback на локальную БД."
                )
                # Fallback
                return await self._register_user_local(
                    user_id, username, first_name, last_name
                )
        else:
            return await self._register_user_local(
                user_id, username, first_name, last_name
            )

    async def _register_user_via_gateway(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str]
    ) -> UserRegistrationResult:
        """Регистрация через API Gateway."""
        client = self._create_client()
        async with client:
            user = await client.users.register(
                telegram_id=user_id,
                username=username,
                first_name=first_name
            )
            logger.info(f"Пользователь {user_id} зарегистрирован через Gateway")
            return UserRegistrationResult(
                telegram_id=user.telegram_id,
                username=user.username,
                is_new=getattr(user, 'is_new', True)
            )

    async def _register_user_local(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str]
    ) -> UserRegistrationResult:
        """Регистрация через локальную БД (analytics)."""
        analytics = self._get_analytics()
        is_new = await analytics.track_user_start(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        logger.debug(f"Пользователь {user_id} зарегистрирован локально, is_new={is_new}")
        return UserRegistrationResult(
            telegram_id=user_id,
            username=username,
            is_new=is_new if is_new is not None else True
        )

    async def track_event(
        self,
        user_id: int,
        event_type: str,
        event_data: dict
    ) -> bool:
        """
        Отслеживание события через Gateway или локально.

        Args:
            user_id: Telegram ID пользователя
            event_type: Тип события (article_request, photo_sent, video_sent, error)
            event_data: Данные события

        Returns:
            True если событие успешно записано
        """
        if self.use_gateway:
            try:
                return await self._track_event_via_gateway(user_id, event_type, event_data)
            except Exception as e:
                logger.warning(
                    f"Gateway ошибка при track_event: {e}. Fallback на локальную БД."
                )
                return await self._track_event_local(user_id, event_type, event_data)
        else:
            return await self._track_event_local(user_id, event_type, event_data)

    async def _track_event_via_gateway(
        self,
        user_id: int,
        event_type: str,
        event_data: dict
    ) -> bool:
        """Отслеживание события через API Gateway."""
        client = self._create_client()
        async with client:
            await client.analytics.track(
                telegram_id=user_id,
                event_type=event_type,
                event_data=event_data
            )
            logger.debug(f"Событие {event_type} для {user_id} отправлено через Gateway")
            return True

    async def _track_event_local(
        self,
        user_id: int,
        event_type: str,
        event_data: dict
    ) -> bool:
        """Отслеживание события через локальную БД."""
        analytics = self._get_analytics()

        # Маппинг на локальные методы
        if event_type == "article_request":
            await analytics.track_article_request(user_id, event_data.get("nm_id", 0))
        elif event_type == "photo_sent":
            await analytics.track_photos_sent(
                user_id,
                event_data.get("nm_id", 0),
                event_data.get("count", 0)
            )
        elif event_type == "video_sent":
            await analytics.track_video_sent(user_id, event_data.get("nm_id", 0))
        elif event_type == "error":
            await analytics.track_error(
                user_id,
                event_data.get("error_type", "unknown"),
                event_data.get("message", "")
            )
        else:
            logger.warning(f"Неизвестный тип события: {event_type}")
            return False

        logger.debug(f"Событие {event_type} для {user_id} записано локально")
        return True


# Singleton instance
_gateway_adapter: Optional[GatewayAdapter] = None


def get_gateway_adapter() -> GatewayAdapter:
    """Получить singleton экземпляр GatewayAdapter."""
    global _gateway_adapter
    if _gateway_adapter is None:
        _gateway_adapter = GatewayAdapter()
    return _gateway_adapter
