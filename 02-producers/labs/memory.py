"""Lab B: the memory-store producer. Kind memory, slot interaction.memory.

Fill in memory_store() until `CWA_W2_IMPL=labs uv run pytest tests/test_lab_b.py` passes.

What a conformant memory producer does (guides/producers.md, R-9, R-14, R-2):

1. Read the memory store, `common.MEMORIES` (shared/fixtures/memories.json). Keep only rows for the request's tenant and user. If "memory-store-ignores-user" is in
   request.faults, skip the user filter: that is the bug a scenario injects to show that the item's own scope still
   keeps another user's memory out of the payload.
2. Never emit an expired or revoked entry. A row with `revoked_by` is reported as
   `{"item_id": ..., "reason": "revoked", "stage": "producer"}`. A row whose `expires` is at or before
   request.asked_at (compare with `common.instant`) is reported with reason `expired`. Neither row carries the text.
3. Emit every other row as an item: slot interaction.memory, authority `generated`, trust `unverified`,
   `freshness` = saved_at, `expires` = the row's deadline (required in this slot, R-9), `source` = the turn it came
   from (the route requires the `turn:` prefix), `scope` = the row's own tenant and user, lineage `summarised`,
   `injection_risk: untrusted_content`.
4. Return the batch with both lists: `{"producer": {"id": "memory-store", "kind": "memory"}, "items": ..., "excluded": ...}`.
"""

from __future__ import annotations

from common import Batch, Request


def memory_store(request: Request) -> Batch:
    raise NotImplementedError("Lab B: see the module docstring")
