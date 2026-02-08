"""Exceptions for Analytics Client.

Exception hierarchy:
    AnalyticsServiceError (base)
    +-- ConnectionError - Network connection failed
    +-- TimeoutError - Request timed out
    +-- ValidationError (422) - Invalid request data
    +-- ServerError (5xx) - Server-side error
"""


class AnalyticsServiceError(Exception):
    """Base exception for Analytics Client.

    All exceptions raised by the client inherit from this class.
    """

    pass


class ConnectionError(AnalyticsServiceError):
    """Raised when connection to Analytics Service fails.

    This typically happens when:
    - Analytics Service is unreachable
    - DNS resolution fails
    - Network is unavailable
    """

    pass


class TimeoutError(AnalyticsServiceError):
    """Raised when request times out.

    This happens when:
    - Server doesn't respond within timeout period
    - Connection hangs
    """

    pass


class ValidationError(AnalyticsServiceError):
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


class ServerError(AnalyticsServiceError):
    """Raised when server returns 5xx error.

    Attributes:
        status_code: HTTP status code (500, 502, 503, etc.)
    """

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(f"Server error ({status_code}): {message}")
