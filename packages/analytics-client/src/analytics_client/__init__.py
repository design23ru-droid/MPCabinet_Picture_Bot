"""Analytics Client - Async HTTP client for Analytics Service microservice."""

from analytics_client.client import AnalyticsClient
from analytics_client.exceptions import (
    AnalyticsServiceError,
    ConnectionError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from analytics_client.models import (
    DailyStats,
    EventCreated,
    UsersCount,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "AnalyticsClient",
    # Exceptions
    "AnalyticsServiceError",
    "ConnectionError",
    "TimeoutError",
    "ValidationError",
    "ServerError",
    # Models
    "DailyStats",
    "EventCreated",
    "UsersCount",
]
