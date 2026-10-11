"""Lab B, solved: the memory-store producer, kind memory, slot interaction.memory."""

from __future__ import annotations

import json

from common import DATA, Batch, Request, instant, item


def memory_store(request: Request) -> Batch:
    asked = instant(request.asked_at)
    ignores_user = "memory-store-ignores-user" in request.faults
    items, excluded = [], []
    for memory in json.loads((DATA / "memories.json").read_text(encoding="utf-8"))["memories"]:
        if memory["workspace"] != request.tenant:
            continue
        if memory["user"] != request.user and not ignores_user:
            continue
        # Expired and revoked entries are never sent: report them by id, without their text (R-9, R-14).
        if "revoked_by" in memory:
            excluded.append({"item_id": memory["id"], "reason": "revoked", "stage": "producer"})
            continue
        if instant(memory["expires"]) <= asked:
            excluded.append({"item_id": memory["id"], "reason": "expired", "stage": "producer"})
            continue
        items.append(item(
            id=memory["id"], slot="interaction.memory", source=memory["from_turn"], source_version="1",
            authority="generated", trust="unverified", freshness=memory["saved_at"], expires=memory["expires"],
            scope={"tenant": memory["workspace"], "user": memory["user"]},  # the item's own scope, not the request's
            lineage="summarised", injection_risk="untrusted_content", body=memory["text"],
        ))
    return {"producer": {"id": "memory-store", "kind": "memory"}, "items": items, "excluded": excluded}
