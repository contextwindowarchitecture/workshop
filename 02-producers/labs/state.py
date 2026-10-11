"""Lab C: the accounts-db producer. Kind state, slot state.user.

Fill in accounts_db() until `CWA_W2_IMPL=labs uv run pytest tests/test_lab_c.py` passes.

What a conformant state producer does (guides/producers.md, R-8):

1. Read the workspace and the user from the accounts store, `common.ACCOUNTS` (shared/fixtures/accounts.json), for request.tenant and request.user. State is read at
   request time from the system of record; the application owns it and the model never writes it.
2. Emit one typed item per fact, both in state.user: the workspace's plan (id `account:<tenant>:plan`, scope
   `{"tenant": ...}`) and the user's membership (id `account:<tenant>:<user>`, scope tenant and user). Authority
   `state`, trust `verified`, lineage `extracted`, `injection_risk: none`, conflict_policy `governs`.
3. `freshness` is when the row was read, which is `request.account_read_at` if set and otherwise
   `request.asked_at`. It is not when the plan last changed. The route admits state for 300 seconds, so a cached
   read older than that is excluded as stale_state, which is exactly what should happen.
4. `source` names the row (`accounts-db:workspaces/<tenant>`, `accounts-db:users/<user>`) and `source_version` its
   version number, as a string.
5. Return `common.batch("accounts-db", "state", items)`.
"""

from __future__ import annotations

from common import Batch, Request


def accounts_db(request: Request) -> Batch:
    raise NotImplementedError("Lab C: see the module docstring")
