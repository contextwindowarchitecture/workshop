"""Lab 2, solved: a SQL memory table to a memory producer batch."""

from __future__ import annotations

import sqlite3

from common import Batch, Request, instant, item

LIVE_ONLY = "SELECT * FROM memories WHERE workspace = ? AND user = ? AND revoked_by IS NULL AND expires > ? ORDER BY id"
EVERYTHING = "SELECT * FROM memories WHERE workspace = ? AND user = ? ORDER BY id"


def adapt(conn: sqlite3.Connection, request: Request, *, silent: bool = False) -> Batch:
    """silent=True is the bug this lab is about: a WHERE clause that quietly drops what should be reported."""
    items, excluded = [], []
    if silent:
        rows = conn.execute(LIVE_ONLY, (request.tenant, request.user, request.asked_at)).fetchall()
    else:
        rows = conn.execute(EVERYTHING, (request.tenant, request.user)).fetchall()
    asked = instant(request.asked_at)
    for row in rows:
        if row["revoked_by"] is not None:
            excluded.append({"item_id": row["id"], "reason": "revoked", "stage": "producer"})
            continue
        if instant(row["expires"]) <= asked:
            excluded.append({"item_id": row["id"], "reason": "expired", "stage": "producer"})
            continue
        items.append(item(
            id=row["id"], slot="interaction.memory", source=row["from_turn"], source_version="1",
            authority="generated", trust="unverified", freshness=row["saved_at"], expires=row["expires"],
            scope={"tenant": row["workspace"], "user": row["user"]}, lineage="summarised",
            injection_risk="untrusted_content", body=row["text"],
        ))
    return {"producer": {"id": "memory-store", "kind": "memory"}, "items": items, "excluded": excluded}
