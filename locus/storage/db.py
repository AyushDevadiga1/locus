"""SQLite database initialization and migration helpers."""

from __future__ import annotations

import sqlite3


def connect_db(path: str = "locus.db") -> sqlite3.Connection:
    """Create a SQLite connection for local storage."""

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection
