"""Pydantic models for API Gateway Client."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    """User model."""

    user_id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Token(BaseModel):
    """Token model."""

    token_id: int
    telegram_id: int
    token_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class HealthStatus(BaseModel):
    """Health status model."""

    status: str
    service: str
    timestamp: Optional[datetime] = None
