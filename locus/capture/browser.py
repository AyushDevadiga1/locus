"""Browser metadata ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BrowserContext:
    """Minimal browser context payload."""

    url: str | None = None
    title: str | None = None
    timestamp: datetime | None = None


def parse_browser_payload(payload: dict) -> BrowserContext:
    """Validate and normalize incoming browser metadata."""

    return BrowserContext(
        url=payload.get("url"),
        title=payload.get("title"),
        timestamp=datetime.utcnow(),
    )
