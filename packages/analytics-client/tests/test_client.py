"""Tests for Analytics Client."""

import pytest
import httpx
import respx

from analytics_client import AnalyticsClient
from analytics_client.exceptions import (
    ConnectionError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from analytics_client.models import DailyStats, EventCreated, UsersCount


class TestAnalyticsClientInit:
    """Test AnalyticsClient initialization."""

    def test_client_stores_base_url(self, base_url):
        """Client should store base_url."""
        client = AnalyticsClient(base_url=base_url)
        assert client.base_url == base_url

    def test_client_default_timeout(self, base_url):
        """Client should have default timeout of 10 seconds."""
        client = AnalyticsClient(base_url=base_url)
        assert client.timeout == 10.0

    def test_client_custom_timeout(self, base_url):
        """Client should accept custom timeout."""
        client = AnalyticsClient(base_url=base_url, timeout=30.0)
        assert client.timeout == 30.0


class TestAnalyticsClientContextManager:
    """Test AnalyticsClient context manager."""

    @pytest.mark.asyncio
    async def test_client_creates_httpx_client_on_enter(self, base_url):
        """Client should create httpx.AsyncClient on __aenter__."""
        client = AnalyticsClient(base_url=base_url)
        async with client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_client_closes_httpx_client_on_exit(self, base_url):
        """Client should close httpx.AsyncClient on __aexit__."""
        client = AnalyticsClient(base_url=base_url)
        async with client:
            inner_client = client._client
        assert inner_client.is_closed

    @pytest.mark.asyncio
    async def test_events_property_raises_without_context(self, base_url):
        """events property should raise RuntimeError outside context manager."""
        client = AnalyticsClient(base_url=base_url)
        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = client.events

    @pytest.mark.asyncio
    async def test_stats_property_raises_without_context(self, base_url):
        """stats property should raise RuntimeError outside context manager."""
        client = AnalyticsClient(base_url=base_url)
        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = client.stats


class TestEventsClient:
    """Test events functionality."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_record_event_returns_created(self, base_url):
        """events.record() should return EventCreated."""
        respx.post(f"{base_url}/events").mock(
            return_value=httpx.Response(
                201,
                json={"status": "created"},
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            result = await client.events.record(
                telegram_id=123456789,
                event_type="user.started",
            )
            assert isinstance(result, EventCreated)
            assert result.status == "created"

    @pytest.mark.asyncio
    @respx.mock
    async def test_record_event_with_data(self, base_url):
        """events.record() should send event_data in payload."""
        route = respx.post(f"{base_url}/events").mock(
            return_value=httpx.Response(
                201,
                json={"status": "created"},
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            await client.events.record(
                telegram_id=123456789,
                event_type="article.requested",
                event_data={"nm_id": 12345},
            )

        request = route.calls[0].request
        body = request.content.decode()
        assert '"nm_id"' in body
        assert '"event_data"' in body

    @pytest.mark.asyncio
    @respx.mock
    async def test_record_event_without_data(self, base_url):
        """events.record() without event_data should not include it in payload."""
        route = respx.post(f"{base_url}/events").mock(
            return_value=httpx.Response(
                201,
                json={"status": "created"},
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            await client.events.record(
                telegram_id=123456789,
                event_type="user.started",
            )

        request = route.calls[0].request
        body = request.content.decode()
        assert '"event_data"' not in body


class TestStatsClient:
    """Test statistics functionality."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_daily_returns_stats(self, base_url):
        """stats.get_daily() should return DailyStats."""
        respx.get(f"{base_url}/stats/daily", params={"date": "2026-02-08"}).mock(
            return_value=httpx.Response(
                200,
                json={
                    "date": "2026-02-08",
                    "stats": {"user.started": 5, "article.requested": 42},
                    "total_events": 47,
                },
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            result = await client.stats.get_daily("2026-02-08")
            assert isinstance(result, DailyStats)
            assert result.date == "2026-02-08"
            assert result.stats == {"user.started": 5, "article.requested": 42}
            assert result.total_events == 47

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_daily_empty_stats(self, base_url):
        """stats.get_daily() for empty day should return empty stats."""
        respx.get(f"{base_url}/stats/daily", params={"date": "2020-01-01"}).mock(
            return_value=httpx.Response(
                200,
                json={
                    "date": "2020-01-01",
                    "stats": {},
                    "total_events": 0,
                },
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            result = await client.stats.get_daily("2020-01-01")
            assert result.stats == {}
            assert result.total_events == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_users_count_returns_count(self, base_url):
        """stats.get_users_count() should return UsersCount."""
        respx.get(f"{base_url}/stats/users/count").mock(
            return_value=httpx.Response(
                200,
                json={"count": 150},
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            result = await client.stats.get_users_count()
            assert isinstance(result, UsersCount)
            assert result.count == 150

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_users_count_zero(self, base_url):
        """stats.get_users_count() with no users should return 0."""
        respx.get(f"{base_url}/stats/users/count").mock(
            return_value=httpx.Response(
                200,
                json={"count": 0},
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            result = await client.stats.get_users_count()
            assert result.count == 0


class TestErrorHandling:
    """Test HTTP error handling."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_400_raises_validation_error(self, base_url):
        """400 response should raise ValidationError."""
        respx.get(f"{base_url}/stats/daily", params={"date": "invalid"}).mock(
            return_value=httpx.Response(
                400, json={"detail": "Invalid date format. Use YYYY-MM-DD"}
            )
        )

        async with AnalyticsClient(base_url=base_url) as client:
            with pytest.raises(ValidationError):
                await client.stats.get_daily("invalid")

    @pytest.mark.asyncio
    @respx.mock
    async def test_422_raises_validation_error(self, base_url):
        """422 response should raise ValidationError."""
        respx.post(f"{base_url}/events").mock(
            return_value=httpx.Response(422, json={"detail": "telegram_id is required"})
        )

        async with AnalyticsClient(base_url=base_url) as client:
            with pytest.raises(ValidationError):
                await client.events.record(telegram_id=0, event_type="test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_500_raises_server_error(self, base_url):
        """500 response should raise ServerError."""
        respx.post(f"{base_url}/events").mock(
            return_value=httpx.Response(500, json={"detail": "Internal error"})
        )

        async with AnalyticsClient(base_url=base_url) as client:
            with pytest.raises(ServerError):
                await client.events.record(telegram_id=123, event_type="user.started")

    @pytest.mark.asyncio
    @respx.mock
    async def test_503_raises_server_error_with_code(self, base_url):
        """503 response should raise ServerError with correct status code."""
        respx.get(f"{base_url}/stats/users/count").mock(
            return_value=httpx.Response(503, json={"detail": "Service unavailable"})
        )

        async with AnalyticsClient(base_url=base_url) as client:
            with pytest.raises(ServerError) as exc_info:
                await client.stats.get_users_count()
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_connection_error_on_unreachable_host(self, base_url):
        """Connection error should raise ConnectionError."""
        async with AnalyticsClient(
            base_url="http://unreachable-host:9999", timeout=0.1
        ) as client:
            with pytest.raises((ConnectionError, TimeoutError)):
                await client.events.record(telegram_id=123, event_type="user.started")
