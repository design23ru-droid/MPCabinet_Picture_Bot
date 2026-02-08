"""Тесты для services/gateway_adapter.py — интеграция с analytics-service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTrackEventWithAnalyticsService:
    """Тесты: USE_ANALYTICS_SERVICE=True — отправка событий через analytics-service."""

    @pytest.mark.asyncio
    async def test_track_event_via_analytics_service(self):
        """track_event при USE_ANALYTICS_SERVICE=True отправляет в analytics-service."""
        mock_settings = MagicMock()
        mock_settings.USE_GATEWAY = False
        mock_settings.USE_ANALYTICS_SERVICE = True
        mock_settings.ANALYTICS_SERVICE_URL = "http://analytics-service:8003"
        mock_settings.ANALYTICS_SERVICE_TIMEOUT = 10
        mock_settings.GATEWAY_URL = "http://api-gateway:8000"
        mock_settings.GATEWAY_API_KEY = None
        mock_settings.GATEWAY_TIMEOUT = 10

        mock_events_client = AsyncMock()
        mock_events_client.record = AsyncMock()

        mock_analytics_client = AsyncMock()
        mock_analytics_client.events = mock_events_client
        mock_analytics_client.__aenter__ = AsyncMock(return_value=mock_analytics_client)
        mock_analytics_client.__aexit__ = AsyncMock(return_value=None)

        with patch("services.gateway_adapter.get_settings", return_value=mock_settings), \
             patch("analytics_client.AnalyticsClient", return_value=mock_analytics_client):

            from services.gateway_adapter import GatewayAdapter
            adapter = GatewayAdapter.__new__(GatewayAdapter)
            adapter.use_gateway = False
            adapter.use_analytics_service = True
            adapter.analytics_service_url = "http://analytics-service:8003"
            adapter.analytics_service_timeout = 10
            adapter.gateway_url = "http://api-gateway:8000"
            adapter.api_key = None
            adapter.timeout = 10
            adapter._analytics = None

            result = await adapter.track_event(123, "article_request", {"nm_id": 456})

            assert result is True
            mock_events_client.record.assert_called_once_with(
                telegram_id=123,
                event_type="article_request",
                event_data={"nm_id": 456},
            )

    @pytest.mark.asyncio
    async def test_track_event_fallback_on_service_error(self):
        """track_event при ошибке analytics-service делает fallback на локальную БД."""
        mock_settings = MagicMock()
        mock_settings.USE_GATEWAY = False
        mock_settings.USE_ANALYTICS_SERVICE = True
        mock_settings.ANALYTICS_SERVICE_URL = "http://analytics-service:8003"
        mock_settings.ANALYTICS_SERVICE_TIMEOUT = 10
        mock_settings.GATEWAY_URL = "http://api-gateway:8000"
        mock_settings.GATEWAY_API_KEY = None
        mock_settings.GATEWAY_TIMEOUT = 10

        mock_events_client = AsyncMock()
        mock_events_client.record = AsyncMock(side_effect=Exception("Connection refused"))

        mock_analytics_client = AsyncMock()
        mock_analytics_client.events = mock_events_client
        mock_analytics_client.__aenter__ = AsyncMock(return_value=mock_analytics_client)
        mock_analytics_client.__aexit__ = AsyncMock(return_value=None)

        mock_local_analytics = AsyncMock()
        mock_local_analytics.track_article_request = AsyncMock()

        with patch("services.gateway_adapter.get_settings", return_value=mock_settings), \
             patch("analytics_client.AnalyticsClient", return_value=mock_analytics_client):

            from services.gateway_adapter import GatewayAdapter
            adapter = GatewayAdapter.__new__(GatewayAdapter)
            adapter.use_gateway = False
            adapter.use_analytics_service = True
            adapter.analytics_service_url = "http://analytics-service:8003"
            adapter.analytics_service_timeout = 10
            adapter.gateway_url = "http://api-gateway:8000"
            adapter.api_key = None
            adapter.timeout = 10
            adapter._analytics = mock_local_analytics

            result = await adapter.track_event(123, "article_request", {"nm_id": 456})

            assert result is True
            mock_local_analytics.track_article_request.assert_called_once_with(123, 456)

    @pytest.mark.asyncio
    async def test_track_event_local_when_flag_disabled(self):
        """track_event при USE_ANALYTICS_SERVICE=False использует локальную БД."""
        mock_local_analytics = AsyncMock()
        mock_local_analytics.track_article_request = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.USE_GATEWAY = False
        mock_settings.USE_ANALYTICS_SERVICE = False
        mock_settings.GATEWAY_URL = "http://api-gateway:8000"
        mock_settings.GATEWAY_API_KEY = None
        mock_settings.GATEWAY_TIMEOUT = 10

        with patch("services.gateway_adapter.get_settings", return_value=mock_settings):
            from services.gateway_adapter import GatewayAdapter
            adapter = GatewayAdapter.__new__(GatewayAdapter)
            adapter.use_gateway = False
            adapter.use_analytics_service = False
            adapter.gateway_url = "http://api-gateway:8000"
            adapter.api_key = None
            adapter.timeout = 10
            adapter._analytics = mock_local_analytics

            result = await adapter.track_event(123, "article_request", {"nm_id": 456})

            assert result is True
            mock_local_analytics.track_article_request.assert_called_once_with(123, 456)

    @pytest.mark.asyncio
    async def test_track_event_photo_sent_via_service(self):
        """track_event photo_sent через analytics-service."""
        mock_events_client = AsyncMock()
        mock_events_client.record = AsyncMock()

        mock_analytics_client = AsyncMock()
        mock_analytics_client.events = mock_events_client
        mock_analytics_client.__aenter__ = AsyncMock(return_value=mock_analytics_client)
        mock_analytics_client.__aexit__ = AsyncMock(return_value=None)

        with patch("analytics_client.AnalyticsClient", return_value=mock_analytics_client):
            from services.gateway_adapter import GatewayAdapter
            adapter = GatewayAdapter.__new__(GatewayAdapter)
            adapter.use_gateway = False
            adapter.use_analytics_service = True
            adapter.analytics_service_url = "http://analytics-service:8003"
            adapter.analytics_service_timeout = 10
            adapter.gateway_url = "http://api-gateway:8000"
            adapter.api_key = None
            adapter.timeout = 10
            adapter._analytics = None

            result = await adapter.track_event(
                123, "photo_sent", {"nm_id": 456, "count": 5}
            )

            assert result is True
            mock_events_client.record.assert_called_once_with(
                telegram_id=123,
                event_type="photo_sent",
                event_data={"nm_id": 456, "count": 5},
            )

    @pytest.mark.asyncio
    async def test_track_event_error_via_service(self):
        """track_event error через analytics-service."""
        mock_events_client = AsyncMock()
        mock_events_client.record = AsyncMock()

        mock_analytics_client = AsyncMock()
        mock_analytics_client.events = mock_events_client
        mock_analytics_client.__aenter__ = AsyncMock(return_value=mock_analytics_client)
        mock_analytics_client.__aexit__ = AsyncMock(return_value=None)

        with patch("analytics_client.AnalyticsClient", return_value=mock_analytics_client):
            from services.gateway_adapter import GatewayAdapter
            adapter = GatewayAdapter.__new__(GatewayAdapter)
            adapter.use_gateway = False
            adapter.use_analytics_service = True
            adapter.analytics_service_url = "http://analytics-service:8003"
            adapter.analytics_service_timeout = 10
            adapter.gateway_url = "http://api-gateway:8000"
            adapter.api_key = None
            adapter.timeout = 10
            adapter._analytics = None

            result = await adapter.track_event(
                123, "error", {"error_type": "product_not_found", "message": "Not found"}
            )

            assert result is True
            mock_events_client.record.assert_called_once_with(
                telegram_id=123,
                event_type="error",
                event_data={"error_type": "product_not_found", "message": "Not found"},
            )


class TestDigestWithAnalyticsService:
    """Тесты: digest.py с USE_ANALYTICS_SERVICE."""

    @pytest.mark.asyncio
    async def test_digest_via_analytics_service(self):
        """Дайджест получает статистику через analytics-service и конвертирует в dict."""
        from datetime import date

        mock_stats_client = AsyncMock()
        mock_stats_client.get_daily = AsyncMock(return_value=MagicMock(
            date="2026-02-07",
            stats={"article_request": 10, "photo_sent": 5},
            total_events=15,
        ))
        mock_stats_client.get_users_count = AsyncMock(return_value=MagicMock(count=42))
        mock_stats_client.get_users_by_event = AsyncMock(side_effect=[
            MagicMock(count=42),   # funnel_started (user.started)
            MagicMock(count=30),   # funnel_active (article_request)
            MagicMock(count=15),   # funnel_returning (article_request, min_count=2)
        ])

        mock_analytics_client = AsyncMock()
        mock_analytics_client.stats = mock_stats_client
        mock_analytics_client.__aenter__ = AsyncMock(return_value=mock_analytics_client)
        mock_analytics_client.__aexit__ = AsyncMock(return_value=None)

        mock_settings = MagicMock()
        mock_settings.USE_ANALYTICS_SERVICE = True
        mock_settings.ANALYTICS_SERVICE_URL = "http://analytics-service:8003"
        mock_settings.ANALYTICS_SERVICE_TIMEOUT = 10
        mock_settings.ENABLE_ANALYTICS = True
        mock_settings.ANALYTICS_CHANNEL_ID = -1003238492068

        mock_bot = AsyncMock()
        mock_send = AsyncMock(return_value=True)

        with patch("services.digest.get_settings", return_value=mock_settings), \
             patch("analytics_client.AnalyticsClient", return_value=mock_analytics_client), \
             patch("services.digest.send_daily_digest", mock_send):

            from services.digest import send_daily_digest_job
            result = await send_daily_digest_job(mock_bot, target_date=date(2026, 2, 7))

            assert result is True
            mock_stats_client.get_daily.assert_called_once_with("2026-02-07")
            mock_stats_client.get_users_count.assert_called_once()
            # Проверяем что stats конвертирован в dict
            call_args = mock_send.call_args
            stats_dict = call_args[0][1]
            assert stats_dict["article_requests"] == 10
            assert stats_dict["photos_sent"] == 5
            assert stats_dict["total_users"] == 42
            # Воронка
            assert stats_dict["funnel_started"] == 42
            assert stats_dict["funnel_active"] == 30
            assert stats_dict["funnel_returning"] == 15

    @pytest.mark.asyncio
    async def test_digest_fallback_on_service_error(self):
        """Дайджест делает fallback на локальную БД при ошибке analytics-service."""
        from datetime import date

        mock_stats_client = AsyncMock()
        mock_stats_client.get_daily = AsyncMock(side_effect=Exception("Service down"))

        mock_analytics_client = AsyncMock()
        mock_analytics_client.stats = mock_stats_client
        mock_analytics_client.__aenter__ = AsyncMock(return_value=mock_analytics_client)
        mock_analytics_client.__aexit__ = AsyncMock(return_value=None)

        mock_local_analytics = AsyncMock()
        mock_local_analytics.get_daily_stats = AsyncMock(return_value={
            "new_users": 3, "total_users": 10, "article_requests": 5,
        })

        mock_settings = MagicMock()
        mock_settings.USE_ANALYTICS_SERVICE = True
        mock_settings.ANALYTICS_SERVICE_URL = "http://analytics-service:8003"
        mock_settings.ANALYTICS_SERVICE_TIMEOUT = 10
        mock_settings.ENABLE_ANALYTICS = True
        mock_settings.ANALYTICS_CHANNEL_ID = -1003238492068

        mock_bot = AsyncMock()

        with patch("services.digest.get_settings", return_value=mock_settings), \
             patch("analytics_client.AnalyticsClient", return_value=mock_analytics_client), \
             patch("services.digest.AnalyticsService", return_value=mock_local_analytics), \
             patch("services.digest.send_daily_digest", new_callable=AsyncMock, return_value=True):

            from services.digest import send_daily_digest_job
            result = await send_daily_digest_job(mock_bot, target_date=date(2026, 2, 7))

            assert result is True
            mock_local_analytics.get_daily_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_digest_local_when_flag_disabled(self):
        """Дайджест использует локальную БД при USE_ANALYTICS_SERVICE=False."""
        from datetime import date

        mock_local_analytics = AsyncMock()
        mock_local_analytics.get_daily_stats = AsyncMock(return_value={
            "new_users": 3, "total_users": 10, "article_requests": 5,
        })

        mock_settings = MagicMock()
        mock_settings.USE_ANALYTICS_SERVICE = False
        mock_settings.ENABLE_ANALYTICS = True
        mock_settings.ANALYTICS_CHANNEL_ID = -1003238492068

        mock_bot = AsyncMock()

        with patch("services.digest.get_settings", return_value=mock_settings), \
             patch("services.digest.AnalyticsService", return_value=mock_local_analytics), \
             patch("services.digest.send_daily_digest", new_callable=AsyncMock, return_value=True):

            from services.digest import send_daily_digest_job
            result = await send_daily_digest_job(mock_bot, target_date=date(2026, 2, 7))

            assert result is True
            mock_local_analytics.get_daily_stats.assert_called_once()