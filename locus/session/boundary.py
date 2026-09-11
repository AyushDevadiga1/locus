"""Boundary detection logic for task/session transitions."""

from __future__ import annotations

from datetime import datetime, timedelta


def has_session_gap(last_seen: datetime, now: datetime, idle_seconds: int = 300) -> bool:
    """Return True when the user has been idle long enough to likely switch tasks."""

    return (now - last_seen).total_seconds() > idle_seconds


def is_new_block(last_seen: datetime, now: datetime, max_gap: int = 120) -> bool:
    """Return True when a pause is large enough to suggest a new focused block."""

    return (now - last_seen).total_seconds() > max_gap
