"""SQLite storage: collected items, past briefings, and what each briefing covered."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from briefing.models import Item

DEFAULT_DB_PATH = Path("data/briefing.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id            INTEGER PRIMARY KEY,
    source        TEXT NOT NULL,
    type          TEXT NOT NULL,
    title         TEXT NOT NULL,
    url           TEXT UNIQUE,
    author        TEXT,
    published_at  TEXT NOT NULL,
    collected_at  TEXT NOT NULL,
    clean_text    TEXT NOT NULL,
    content_hash  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS briefings (
    date          TEXT PRIMARY KEY,   -- YYYY-MM-DD
    markdown      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    cost_usd      REAL
);

-- One row per story a briefing covered, so later runs can avoid repeats.
CREATE TABLE IF NOT EXISTS covered_stories (
    id            INTEGER PRIMARY KEY,
    briefing_date TEXT NOT NULL REFERENCES briefings(date),
    story_key     TEXT NOT NULL,
    summary       TEXT NOT NULL,
    section       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concepts (
    briefing_date TEXT PRIMARY KEY REFERENCES briefings(date),
    name          TEXT NOT NULL,
    summary       TEXT NOT NULL
);
"""


def connect(path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_item(conn: sqlite3.Connection, item: Item) -> bool:
    """Store an item. Returns False if it was already seen (same URL or same text)."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO items
           (source, type, title, url, author, published_at, collected_at, clean_text, content_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            item.source,
            item.type.value,
            item.title,
            item.url,
            item.author,
            item.published_at.isoformat(),
            datetime.now().astimezone().isoformat(),
            item.clean_text,
            item.content_hash,
        ),
    )
    conn.commit()
    return cur.rowcount == 1
