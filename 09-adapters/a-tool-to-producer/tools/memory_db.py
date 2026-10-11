"""The memory store you already run: a SQL table of memories, here SQLite in memory, loaded from the Fernway fixture.

This is the tool being wrapped, not the lab. The table is what a memory feature usually has: one row per memory with
who it belongs to, where it came from, when it was saved, when it expires, and a revoked_by column that is NULL until
a later turn contradicts it. Nothing in the table knows about CWA.

    conn = memory_db.connect()
    conn.execute("SELECT id, text FROM memories WHERE workspace = ? AND user = ?", ("w_kitewood", "u_ada"))
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from fernway import MEMORIES  # noqa: E402

SCHEMA = """
CREATE TABLE memories (
    id         TEXT PRIMARY KEY,
    workspace  TEXT NOT NULL,
    user       TEXT NOT NULL,
    text       TEXT NOT NULL,
    from_turn  TEXT NOT NULL,
    saved_at   TEXT NOT NULL,
    expires    TEXT NOT NULL,
    revoked_by TEXT
)
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    rows = json.loads(MEMORIES.read_text(encoding="utf-8"))["memories"]
    conn.executemany(
        "INSERT INTO memories VALUES (:id, :workspace, :user, :text, :from_turn, :saved_at, :expires, :revoked_by)",
        [{"revoked_by": None, **row} for row in rows],
    )
    conn.commit()
    return conn
