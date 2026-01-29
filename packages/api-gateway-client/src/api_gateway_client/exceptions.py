"""Exceptions for API Gateway Client.

Exception hierarchy:
    ApiGatewayError (base)
    ├── ConnectionError - Network connection failed
    ├── TimeoutError - Request timed out
    ├── AuthenticationError (401) - Invalid or missing credentials
    ├── AuthorizationError (403) - Access denied
    ├── NotFoundError (404) - Resource not found
    ├── ValidationError (422) - Invalid request data
    ├── RateLimitError (429) - Rate limit exceeded
    └── ServerError (5xx) - Server-side error
"""


class ApiGatewayError(Exception):
    """Base exception for API Gateway Client.

    All exceptions raised by the client inherit from this class.
    """

    pass


class ConnectionError(ApiGatewayError):
    """Raised when connection to API Gateway fails.

    This typically happens when:
    - API Gateway is unreachable
    - DNS resolution fails
    - Network is unavailable
    """

    pass


class TimeoutError(ApiGatewayError):
    """Raised when request times out.

    This happens when:
    - Server doesn't respond within timeout period
    - Connection hangs
    """

    pass


class AuthenticationError(ApiGatewayError):
    """Raised when authentication fails (HTTP 401).

    This happens when:
    - JWT token is invalid
    - JWT token is expired
    - No authentication provided
    """

    status_code: int = 401

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Authentication failed: {message}")


class AuthorizationError(ApiGatewayError):
    """Raised when authorization fails (HTTP 403).

    This happens when:
    - User doesn't have required permissions
    - Resource access is forbidden
    """

    status_code: int = 403

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Authorization failed: {message}")


class NotFoundError(ApiGatewayError):
    """Raised when resource is not found (HTTP 404).

    This happens when:
    - User doesn't exist
    - Token doesn't exist
    - Endpoint doesn't exist
    """

    status_code: int = 404

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Not found: {message}")


class ValidationError(ApiGatewayError):
    """Raised when request validation fails (HTTP 422).

    This happens when:
    - Request body has invalid format
    - Required fields are missing
    - Field values are invalid
    """

    status_code: int = 422

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Validation error: {message}")


class RateLimitError(ApiGatewayError):
    """Raised when rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying
    """

    status_code: int = 429

    def __init__(self, message: str, retry_after: int = 0):
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {message}")


class ServerError(ApiGatewayError):
    """Raised when server returns 5xx error.

    Attributes:
        status_code: HTTP status code (500, 502, 503, etc.)
    """

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(f"Server error ({status_code}): {message}")
