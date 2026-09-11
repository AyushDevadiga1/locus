"""Application configuration for Locus."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Default runtime settings for the application."""

    db_path: str = "locus.db"
    idle_timeout_seconds: int = 300
    max_session_minutes: int = 240


DEFAULT_SETTINGS = Settings()
