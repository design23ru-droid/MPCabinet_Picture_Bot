"""Analytics Client implementation."""

import logging
from typing import Any, Dict, Optional

import httpx

from analytics_client.exceptions import (
    ConnectionError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from analytics_client.models import DailyStats, EventCreated, UsersCount

logger = logging.getLogger(__name__)


class _BaseSubClient:
    """Base class for sub-clients."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: httpx Response object

        Returns:
            Response JSON data

        Raises:
            ValidationError: On 422
            ServerError: On 5xx
        """
        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text or "Unknown error"}

        if response.is_success:
            return data

        detail = data.get("detail", "Unknown error")

        if response.status_code == 400:
            raise ValidationError(detail)
        elif response.status_code == 422:
            raise ValidationError(detail)
        elif response.status_code >= 500:
            raise ServerError(detail, status_code=response.status_code)
        else:
            raise ServerError(detail, status_code=response.status_code)


class EventsClient(_BaseSubClient):
    """Events management client."""

    async def record(
        self,
        telegram_id: int,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> EventCreated:
        """Record analytics event.

        Args:
            telegram_id: Telegram user ID
            event_type: Event type (e.g., "user.started", "article.requested")
            event_data: Optional event metadata

        Returns:
            EventCreated response
        """
        logger.debug(f"Recording event: type={event_type}, user={telegram_id}")
        payload: Dict[str, Any] = {
            "telegram_id": telegram_id,
            "event_type": event_type,
        }
        if event_data is not None:
            payload["event_data"] = event_data

        try:
            response = await self._client.post("/events", json=payload)
        except httpx.ConnectError as e:
            raise ConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise TimeoutError(str(e)) from e

        data = await self._handle_response(response)
        return EventCreated(**data)


class StatsClient(_BaseSubClient):
    """Statistics client."""

    async def get_daily(self, date: str) -> DailyStats:
        """Get daily statistics.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            DailyStats object
        """
        logger.debug(f"Getting daily stats for date={date}")
        try:
            response = await self._client.get("/stats/daily", params={"date": date})
        except httpx.ConnectError as e:
            raise ConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise TimeoutError(str(e)) from e

        data = await self._handle_response(response)
        return DailyStats(**data)

    async def get_users_count(self) -> UsersCount:
        """Get total unique users count.

        Returns:
            UsersCount object
        """
        logger.debug("Getting users count")
        try:
            response = await self._client.get("/stats/users/count")
        except httpx.ConnectError as e:
            raise ConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise TimeoutError(str(e)) from e

        data = await self._handle_response(response)
        return UsersCount(**data)


class AnalyticsClient:
    """Async HTTP client for Analytics Service.

    Usage:
        async with AnalyticsClient(base_url="http://analytics-service:8003") as client:
            # Record event
            await client.events.record(
                telegram_id=123, event_type="user.started"
            )

            # Get daily stats
            stats = await client.stats.get_daily("2026-02-08")

            # Get users count
            users = await client.stats.get_users_count()
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
    ):
        """Initialize Analytics Client.

        Args:
            base_url: Base URL for Analytics Service (e.g., http://localhost:8003)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._events: Optional[EventsClient] = None
        self._stats: Optional[StatsClient] = None

    async def __aenter__(self):
        """Enter context manager - create HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

        self._events = EventsClient(self._client)
        self._stats = StatsClient(self._client)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - close HTTP client."""
        if self._client:
            await self._client.aclose()

    @property
    def events(self) -> EventsClient:
        """Events client."""
        if self._events is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )
        return self._events

    @property
    def stats(self) -> StatsClient:
        """Stats client."""
        if self._stats is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )
        return self._stats
