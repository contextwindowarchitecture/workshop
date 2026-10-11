"""A scorer over traces: a policy mistake is visible in the trace before anyone reads a model's output.

Route v1 of the security review shed memory first under budget pressure, and so dropped a high-severity prior finding.
Nothing failed; the trace recorded an over_budget row for it. A scorer that reads traces flags that row on every run,
which is how the v2 policy (memory protected, docs and test diffs shed first) was motivated and is held in place."""

from __future__ import annotations

from typing import Any


def dropped_high_severity(document: dict[str, Any], trace: dict[str, Any]) -> list[str]:
    """Ids of prior findings (interaction.memory) whose body is marked high severity and that fitting omitted."""
    items = {i["id"]: i for b in document["batches"] for i in b["items"]}
    flagged = []
    for row in trace["excluded"]:
        item = items.get(row["item_id"])
        if row["reason"] == "over_budget" and item and item["slot"] == "interaction.memory" and item["body"].startswith("high ·"):
            flagged.append(row["item_id"])
    return flagged
