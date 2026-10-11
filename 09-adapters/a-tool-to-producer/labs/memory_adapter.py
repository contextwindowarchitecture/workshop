"""Lab 2: wrap the SQL memory table as the memory-store producer.

The tool is tools/memory_db.py, a SQLite table `memories(id, workspace, user, text, from_turn, saved_at, expires,
revoked_by)`. Write adapt() until `CWA_W9A_IMPL=labs uv run pytest tests/test_lab_memory.py` passes.

The one thing this lab is about: a memory producer reports what it suppresses (R-9, R-14), and the natural SQL query
makes that impossible. `WHERE revoked_by IS NULL AND expires > ?` returns only live rows, and the rows it leaves out
vanish without a trace, because the assembler can only record what it was offered or told about. So:

1. Select every row for request.tenant and request.user, ordered by id. Decide in Python, not in the WHERE clause.
2. A row with revoked_by set: an excluded row {"item_id", "reason": "revoked", "stage": "producer"}, no text.
   A row whose expires is at or before request.asked_at (compare with common.instant): reason "expired", no text.
3. Every other row: an item in interaction.memory with authority generated, trust unverified, freshness = saved_at,
   expires = the row's deadline, source = from_turn (the route requires the `turn:` prefix), scope = the row's own
   workspace and user, lineage summarised, injection_risk untrusted_content, body = text.
4. Return {"producer": {"id": "memory-store", "kind": "memory"}, "items": ..., "excluded": ...}.

Keep the `silent` parameter and make silent=True do it the wrong way, with the live-only WHERE clause. run.py
--fault silent-sql uses it, so you can see for yourself what the trace looks like when a producer drops rows quietly:
nothing. That is the breach admission cannot see, and the reason the producer conformance claim rests on the
producer's word.
"""

from __future__ import annotations

import sqlite3

from common import Batch, Request


def adapt(conn: sqlite3.Connection, request: Request, *, silent: bool = False) -> Batch:
    raise NotImplementedError("Lab 2: see the module docstring")
