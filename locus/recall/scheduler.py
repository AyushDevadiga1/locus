"""SM-2 inspired review scheduling for pending work items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ReviewItem:
    """An item queued for later review."""

    topic: str
    next_review: datetime
    ease: float = 2.5
    interval_days: int = 1


def schedule_review(topic: str, now: datetime | None = None) -> ReviewItem:
    """Create a scheduled review item for a session topic."""

    current_time = now or datetime.utcnow()
    return ReviewItem(topic=topic, next_review=current_time + timedelta(days=1))
