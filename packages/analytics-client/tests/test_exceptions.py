"""Tests for Analytics Client exceptions."""

from analytics_client.exceptions import (
    AnalyticsServiceError,
    ConnectionError,
    ServerError,
    TimeoutError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Test exception hierarchy."""

    def test_connection_error_inherits_base(self):
        """ConnectionError should inherit from AnalyticsServiceError."""
        assert issubclass(ConnectionError, AnalyticsServiceError)

    def test_timeout_error_inherits_base(self):
        """TimeoutError should inherit from AnalyticsServiceError."""
        assert issubclass(TimeoutError, AnalyticsServiceError)

    def test_validation_error_inherits_base(self):
        """ValidationError should inherit from AnalyticsServiceError."""
        assert issubclass(ValidationError, AnalyticsServiceError)

    def test_server_error_inherits_base(self):
        """ServerError should inherit from AnalyticsServiceError."""
        assert issubclass(ServerError, AnalyticsServiceError)


class TestExceptionAttributes:
    """Test exception attributes."""

    def test_validation_error_has_status_code(self):
        """ValidationError should have status_code 422."""
        error = ValidationError("invalid data")
        assert error.status_code == 422
        assert error.message == "invalid data"

    def test_server_error_has_status_code(self):
        """ServerError should have configurable status_code."""
        error = ServerError("internal error", status_code=503)
        assert error.status_code == 503
        assert error.message == "internal error"

    def test_server_error_default_status_code(self):
        """ServerError should default to 500."""
        error = ServerError("internal error")
        assert error.status_code == 500

    def test_validation_error_str(self):
        """ValidationError should have descriptive string."""
        error = ValidationError("missing field")
        assert "Validation error" in str(error)
        assert "missing field" in str(error)

    def test_server_error_str(self):
        """ServerError should have descriptive string."""
        error = ServerError("db down", status_code=503)
        assert "Server error" in str(error)
        assert "503" in str(error)
        assert "db down" in str(error)
