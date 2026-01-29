"""API Gateway Client - Async HTTP client for API Gateway microservice."""

from api_gateway_client.client import APIGatewayClient
from api_gateway_client.exceptions import (
    ApiGatewayError,
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from api_gateway_client.models import (
    HealthStatus,
    Token,
    User,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "APIGatewayClient",
    # Exceptions
    "ApiGatewayError",
    "ConnectionError",
    "TimeoutError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    # Models
    "User",
    "Token",
    "HealthStatus",
]
