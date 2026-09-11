"""Aggregate signals into session and block records."""

from __future__ import annotations

from datetime import datetime

from locus.session.schema import Block, Session


def build_session(start: datetime, title: str | None = None) -> Session:
    """Create a session shell for later enrichment."""

    return Session(start=start, title=title)


def add_block(session: Session, start: datetime, title: str | None = None) -> Block:
    """Add a block to a session."""

    block = Block(start=start, title=title)
    session.blocks.append(block)
    return block
