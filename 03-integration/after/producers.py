"""Step 3: every piece of the old prompt becomes items with an authority and a source.

Write five producers. Each returns a batch, {"producer": {"id", "kind"}, "items": [...], "excluded": [...]}, and the
two that assert facts also return which fact each item asserts, so context.py can declare conflict groups.

    app_policy()                      -> batch              governance.instructions from policy/instructions.md
    accounts_db(request)              -> (batch, facts)     state.user: the plan item asserts the fact "plan"
    memory_store(request)             -> (batch, facts)     interaction.memory; a memory with a "fact" key asserts it;
                                                            expired and revoked rows reported, never sent
    help_center_search(request, top_k) -> batch             evidence.knowledge, one scored item per paragraph
    chat_session(request)             -> batch              interaction.history and interaction.query

You wrote all of these in W2 (02-producers/solution/) and W9 module A. Bring them over and make two changes: the
state and memory producers return facts, and the memory producer honours the "memory-store-ignores-user" fault so
the scope test can inject it. request.accounts(), request.memories() and request.corpus are the data.
"""

from __future__ import annotations

from typing import Any

from request import Request

Facts = dict[str, str]


def app_policy() -> dict[str, Any]:
    raise NotImplementedError("Step 3: see MIGRATION.md")


def accounts_db(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("Step 3: see MIGRATION.md")


def memory_store(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("Step 3: see MIGRATION.md")


def help_center_search(request: Request, top_k: int) -> dict[str, Any]:
    raise NotImplementedError("Step 3: see MIGRATION.md")


def chat_session(request: Request) -> dict[str, Any]:
    raise NotImplementedError("Step 3: see MIGRATION.md")
