"""Pydantic models for Analytics Client."""

from typing import Dict

from pydantic import BaseModel


class DailyStats(BaseModel):
    """Daily statistics response model."""

    date: str
    stats: Dict[str, int]
    total_events: int


class UsersCount(BaseModel):
    """Users count response model."""

    count: int


class EventCreated(BaseModel):
    """Event created response model."""

    status: str
