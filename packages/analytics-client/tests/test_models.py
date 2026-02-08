"""Tests for Analytics Client models."""

from analytics_client.models import DailyStats, EventCreated, UsersCount


class TestDailyStats:
    """Test DailyStats model."""

    def test_daily_stats_creation(self):
        """DailyStats should be created with valid data."""
        stats = DailyStats(
            date="2026-02-08",
            stats={"user.started": 5, "article.requested": 42},
            total_events=47,
        )
        assert stats.date == "2026-02-08"
        assert stats.stats == {"user.started": 5, "article.requested": 42}
        assert stats.total_events == 47

    def test_daily_stats_empty(self):
        """DailyStats should work with empty stats."""
        stats = DailyStats(date="2020-01-01", stats={}, total_events=0)
        assert stats.stats == {}
        assert stats.total_events == 0


class TestUsersCount:
    """Test UsersCount model."""

    def test_users_count_creation(self):
        """UsersCount should be created with valid data."""
        users = UsersCount(count=150)
        assert users.count == 150

    def test_users_count_zero(self):
        """UsersCount should work with zero."""
        users = UsersCount(count=0)
        assert users.count == 0


class TestEventCreated:
    """Test EventCreated model."""

    def test_event_created_status(self):
        """EventCreated should have status field."""
        result = EventCreated(status="created")
        assert result.status == "created"
