"""Dataclasses describing sessions and task blocks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Block:
    """A focused working block within a session."""

    start: datetime
    end: datetime | None = None
    title: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Session:
    """A higher-level work session aggregating one or more blocks."""

    start: datetime
    end: datetime | None = None
    blocks: list[Block] = field(default_factory=list)
    title: str | None = None
