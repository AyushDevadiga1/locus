"""Active window and focus tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class WindowSnapshot:
    """Minimal representation of an active window."""

    title: str | None
    app_name: str | None
    timestamp: datetime


def read_active_window() -> WindowSnapshot:
    """Placeholder for desktop focus capture implementation."""

    return WindowSnapshot(
        title=None,
        app_name=None,
        timestamp=datetime.utcnow(),
    )
