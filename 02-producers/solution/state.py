"""Lab C, solved: the accounts-db producer, kind state, slot state.user."""

from __future__ import annotations

import json

from common import DATA, Batch, Request, batch, item


def accounts_db(request: Request) -> Batch:
    accounts = json.loads((DATA / "accounts.json").read_text(encoding="utf-8"))
    workspace, member = accounts["workspaces"][request.tenant], accounts["users"][request.user]
    read_at = request.account_read_at or request.asked_at  # freshness is when the row was read, never when it changed
    common = dict(slot="state.user", authority="state", trust="verified", freshness=read_at,
                  conflict_policy="governs", lineage="extracted", injection_risk="none")
    return batch("accounts-db", "state", [
        item(id=f"account:{request.tenant}:plan", source=f"accounts-db:workspaces/{request.tenant}",
             source_version=str(workspace["version"]), scope={"tenant": request.tenant},
             body=f"Workspace {workspace['name']} is on the {workspace['plan']} plan, billed {workspace['billing']}, "
                  f"since {workspace['plan_since']}. {workspace['seats']} seats. Data region: {workspace['region']}.",
             **common),
        item(id=f"account:{request.tenant}:{request.user}", source=f"accounts-db:users/{request.user}",
             source_version=str(member["version"]), scope={"tenant": request.tenant, "user": request.user},
             body=f"{member['name']} is a workspace {member['role']}"
                  + (" and a billing admin." if member["billing_admin"] else ", not a billing admin."),
             **common),
    ])
