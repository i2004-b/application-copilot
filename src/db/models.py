"""
Minimal persistence layer -- plain sqlite3, no ORM, on purpose. This is a
solo 3-week project; a full ORM is more setup than payoff. If you outgrow
this later (e.g. once the tracker-product integration happens), swapping
in SQLAlchemy is a clean, well-scoped refactor -- and "I outgrew the
starter and refactored it" is itself a fine thing to say in an interview.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

from src.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    source TEXT NOT NULL,           -- 'greenhouse' | 'lever' | 'ashby'
    raw_jd TEXT NOT NULL,
    extracted_json TEXT,            -- ExtractedJob, serialized
    extraction_model TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    posting_id INTEGER NOT NULL REFERENCES postings(id),
    bullet_text TEXT NOT NULL,
    score REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def save_posting(company: str, source: str, raw_jd: str, extracted: dict, model: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO postings (company, source, raw_jd, extracted_json, extraction_model) "
            "VALUES (?, ?, ?, ?, ?)",
            (company, source, raw_jd, json.dumps(extracted), model),
        )
        return cur.lastrowid


def save_matches(posting_id: int, matches: list[dict]) -> None:
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO matches (posting_id, bullet_text, score) VALUES (?, ?, ?)",
            [(posting_id, m["text"], m["score"]) for m in matches],
        )


def all_postings_with_matches() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM postings ORDER BY fetched_at DESC").fetchall()
        results = []
        for row in rows:
            matches = conn.execute(
                "SELECT bullet_text, score FROM matches WHERE posting_id = ? ORDER BY score DESC",
                (row["id"],),
            ).fetchall()
            results.append(
                {
                    **dict(row),
                    "extracted": json.loads(row["extracted_json"]) if row["extracted_json"] else None,
                    "matches": [dict(m) for m in matches],
                }
            )
        return results
