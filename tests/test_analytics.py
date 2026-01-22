"""Тесты для services/analytics.py."""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from services.analytics import AnalyticsService


@pytest.fixture
def analytics():
    """Экземпляр AnalyticsService для тестов."""
    return AnalyticsService()


@pytest.fixture
def mock_pool():
    """Mock пула asyncpg."""
    pool = MagicMock()
    conn = MagicMock()

    # Mock acquire context manager
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock()

    pool.acquire = MagicMock(return_value=conn)
    return pool, conn


class TestTrackUserStart:
    """Тесты для track_user_start."""

    @pytest.mark.asyncio
    async def test_new_user(self, analytics):
        """Новый пользователь - возвращает True."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        # Mock acquire context manager
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        # fetchrow возвращает None (пользователь не найден)
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            result = await analytics.track_user_start(
                user_id=123456789,
                username="testuser",
                first_name="Test",
                last_name="User"
            )

        # Проверяем что вернулся True (новый пользователь)
        assert result is True

        # Проверяем что был INSERT в users
        calls = mock_conn.execute.call_args_list
        assert len(calls) == 2  # INSERT users + INSERT events

        # Проверяем первый вызов (INSERT users)
        insert_users_sql = calls[0][0][0]
        assert "INSERT INTO shared.users" in insert_users_sql

    @pytest.mark.asyncio
    async def test_returning_user(self, analytics):
        """Повторный пользователь - возвращает False."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        # fetchrow возвращает запись (пользователь существует)
        mock_conn.fetchrow = AsyncMock(return_value={"telegram_id": 123456789})
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            result = await analytics.track_user_start(
                user_id=123456789,
                username="testuser",
                first_name="Test",
                last_name="User"
            )

        # Проверяем что вернулся False (повторный пользователь)
        assert result is False

        # Проверяем что был UPDATE users
        calls = mock_conn.execute.call_args_list
        assert len(calls) == 2  # UPDATE users + INSERT events

        update_users_sql = calls[0][0][0]
        assert "UPDATE shared.users" in update_users_sql

    @pytest.mark.asyncio
    async def test_db_unavailable(self, analytics):
        """БД недоступна - graceful degradation (возвращает None)."""
        with patch("services.analytics.get_pool", return_value=None):
            result = await analytics.track_user_start(
                user_id=123456789,
                username="testuser",
                first_name="Test",
                last_name="User"
            )

        # Проверяем что вернулся None (БД недоступна)
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error(self, analytics):
        """Ошибка БД - graceful degradation (возвращает None)."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        # fetchrow бросает исключение
        mock_conn.fetchrow = AsyncMock(side_effect=Exception("Database error"))

        with patch("services.analytics.get_pool", return_value=mock_pool):
            result = await analytics.track_user_start(
                user_id=123456789,
                username="testuser",
                first_name="Test",
                last_name="User"
            )

        # Проверяем что вернулся None (ошибка обработана)
        assert result is None


class TestTrackArticleRequest:
    """Тесты для track_article_request."""

    @pytest.mark.asyncio
    async def test_success(self, analytics):
        """Успешная запись события article_request."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            await analytics.track_article_request(
                user_id=123456789,
                nm_id=12345678
            )

        # Проверяем что был INSERT в events
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "INSERT INTO shared.analytics_events" in call_args[0]
        assert "article_request" in call_args[0]

    @pytest.mark.asyncio
    async def test_db_unavailable(self, analytics):
        """БД недоступна - не падаем."""
        with patch("services.analytics.get_pool", return_value=None):
            # Не должно бросить исключение
            await analytics.track_article_request(
                user_id=123456789,
                nm_id=12345678
            )


class TestTrackPhotosSent:
    """Тесты для track_photos_sent."""

    @pytest.mark.asyncio
    async def test_success(self, analytics):
        """Успешная запись события photo_sent."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            await analytics.track_photos_sent(
                user_id=123456789,
                nm_id=12345678,
                count=5
            )

        # Проверяем что был INSERT
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "photo_sent" in call_args[0]


class TestTrackVideoSent:
    """Тесты для track_video_sent."""

    @pytest.mark.asyncio
    async def test_success(self, analytics):
        """Успешная запись события video_sent."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            await analytics.track_video_sent(
                user_id=123456789,
                nm_id=12345678
            )

        # Проверяем что был INSERT
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "video_sent" in call_args[0]


class TestTrackError:
    """Тесты для track_error."""

    @pytest.mark.asyncio
    async def test_success(self, analytics):
        """Успешная запись события error."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            await analytics.track_error(
                user_id=123456789,
                error_type="product_not_found",
                error_message="Товар 12345678 не найден"
            )

        # Проверяем что был INSERT
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "error" in call_args[0]

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, analytics):
        """Обработка спецсимволов в сообщении об ошибке."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.execute = AsyncMock()

        with patch("services.analytics.get_pool", return_value=mock_pool):
            # Сообщение с кавычками
            await analytics.track_error(
                user_id=123456789,
                error_type="test_error",
                error_message='Message with "quotes" and \'apostrophes\''
            )

        # Проверяем что не упало
        mock_conn.execute.assert_called_once()


class TestGetDailyStats:
    """Тесты для get_daily_stats."""

    @pytest.mark.asyncio
    async def test_success(self, analytics):
        """Успешное получение статистики за день."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        # Мокируем все запросы к БД
        mock_conn.fetchval = AsyncMock(side_effect=[
            5,   # new_users
            23,  # total_users
            8,   # returning_users
            42,  # article_requests
            15,  # videos_sent
            2,   # errors
        ])

        # Мокируем fetchrow для фото
        mock_conn.fetchrow = AsyncMock(return_value={
            "total_photos": 156,
            "unique_products": 38
        })

        with patch("services.analytics.get_pool", return_value=mock_pool):
            stats = await analytics.get_daily_stats(date(2026, 1, 22))

        # Проверяем структуру результата
        assert stats is not None
        assert stats["new_users"] == 5
        assert stats["total_users"] == 23
        assert stats["returning_users"] == 8
        assert stats["article_requests"] == 42
        assert stats["photos_sent"] == 156
        assert stats["unique_products"] == 38
        assert stats["videos_sent"] == 15
        assert stats["errors"] == 2

    @pytest.mark.asyncio
    async def test_db_unavailable(self, analytics):
        """БД недоступна - возвращает None."""
        with patch("services.analytics.get_pool", return_value=None):
            stats = await analytics.get_daily_stats(date(2026, 1, 22))

        assert stats is None

    @pytest.mark.asyncio
    async def test_db_error(self, analytics):
        """Ошибка БД - возвращает None."""
        mock_pool, mock_conn = MagicMock(), MagicMock()

        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        # fetchval бросает исключение
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Query error"))

        with patch("services.analytics.get_pool", return_value=mock_pool):
            stats = await analytics.get_daily_stats(date(2026, 1, 22))

        assert stats is None
