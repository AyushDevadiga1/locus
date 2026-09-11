"""Keyboard timing capture without storing raw text."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class KeystrokeEvent:
    """Timing-focused keyboard event for idle and activity analysis."""

    key: str
    timestamp: datetime


def record_keypress(key: str) -> KeystrokeEvent:
    """Placeholder implementation for key timing capture."""

    return KeystrokeEvent(key=key, timestamp=datetime.utcnow())
