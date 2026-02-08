"""Pytest fixtures for Analytics Client tests."""

import pytest


@pytest.fixture
def base_url() -> str:
    """Base URL for Analytics Service."""
    return "http://analytics-service:8003"
