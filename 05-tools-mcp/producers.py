"""The agent's producers, one batch each per inference. The capability policy is in capability_policy.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from request import Request, accounts, corpus

POLICY = Path(__file__).resolve().parent / "policy"


@dataclass(frozen=True)
class Step:
    """One tool call the model asked for, and what the application did with it."""

    turn: int
    tool: str
    arguments: dict[str, Any]
    approved: bool
    reason: str
    executed: bool = False
    ok: bool = False
    value: Any = None
    observed_at: str = ""


def item(**fields: Any) -> dict[str, Any]:
    return {"token_budget": None, "variants": [], "conflict_policy": "defers", "eligibility": "route-policy", **fields}


def batch(producer_id: str, kind: str, items: list[dict[str, Any]], excluded: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"producer": {"id": producer_id, "kind": kind}, "items": items, "excluded": excluded or []}


def app_policy() -> dict[str, Any]:
    meta, body = corpus.front_matter((POLICY / "instructions.md").read_text(encoding="utf-8"))
    return batch("app-policy", "policy", [item(
        id="policy:instructions", slot="governance.instructions", source="app:policy/instructions.md",
        source_version=meta["version"], authority="governing", trust="verified", freshness=meta["updated"],
        conflict_policy="governs", lineage="verbatim", injection_risk="none", body=body,
    )])


def accounts_db(request: Request, now: str) -> dict[str, Any]:
    db = accounts()
    workspace, member = db["workspaces"][request.tenant], db["users"][request.user]
    return batch("accounts-db", "state", [item(
        id=f"account:{request.tenant}", slot="state.user", source=f"accounts-db:workspaces/{request.tenant}",
        source_version=str(workspace["version"]), authority="state", trust="verified", freshness=now,
        scope={"tenant": request.tenant}, conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"{member['name']} ({request.user}) is a workspace {member['role']} of {workspace['name']} ({request.tenant}), "
             f"on the {workspace['plan']} plan, data region {workspace['region']}.",
    )])


def _call(step: Step) -> str:
    return f"{step.tool}({', '.join(f'{k}={v!r}' for k, v in sorted(step.arguments.items()))})"


def observation_id(n: int) -> str:
    return f"obs:{n}"


def agent_controller(request: Request, task: str, steps: list[Step], turn: int, max_turns: int, now: str) -> dict[str, Any]:
    """The task state the application writes before each inference: which turn, every call so far and what the guard
    decided. The model reads what happened; it never writes it (R-8). A denial comes back here, never as a fake result."""
    lines = [f"Turn {turn} of {max_turns}.", "Tool calls so far:" if steps else "No tool calls yet."]
    for n, step in enumerate(steps, start=1):
        if not step.approved:
            lines.append(f"{n}. {_call(step)}: denied by the application, {step.reason.rstrip('.')}. It was not called.")
        else:
            lines.append(f"{n}. {_call(step)}: {'done' if step.ok else 'failed'}, see observation {observation_id(n)}.")
    if turn == max_turns:
        lines.append("This is the last turn: no tools are offered. Answer now from what you have.")
    return batch("agent-controller", "state", [item(
        id=f"task:{task}", slot="state.task", source=f"agent-controller:{task}", source_version=str(turn),
        authority="state", trust="verified", freshness=now, scope={"tenant": request.tenant, "task": task},
        conflict_policy="governs", lineage="extracted", injection_risk="none", body="\n".join(lines),
    )])


def fernway_accounts(request: Request, task: str, steps: list[Step], server: str, version: str) -> dict[str, Any]:
    """Every executed call's result as an observation: data, never instructions (R-10, R-15). The source is the call,
    so a repeated call is superseded by its latest observation (R-25)."""
    items = []
    for n, step in enumerate(steps, start=1):
        if not step.executed:
            continue
        arguments = "&".join(f"{k}={v}" for k, v in sorted(step.arguments.items()))
        outcome = {"result": step.value} if step.ok else {"error": step.value}
        items.append(item(
            id=observation_id(n), slot="evidence.tool_results", source=f"mcp:{server}/{step.tool}?{arguments}",
            source_version=version, authority="observation", trust="unverified", freshness=step.observed_at,
            scope={"tenant": request.tenant, "task": task}, conflict_policy="governs", lineage="verbatim",
            injection_risk="untrusted_content", body=json.dumps({"tool": step.tool, "arguments": step.arguments, **outcome}, sort_keys=True),
        ))
    return batch("fernway-accounts", "mcp", items)


def chat_session(request: Request) -> dict[str, Any]:
    scope, source, items = {"session": request.session}, f"chat:{request.session}", []
    for n, turn in enumerate(request.turns, start=1):
        generated = turn.role == "assistant"
        items.append(item(
            id=f"turn:{request.session}:{n:04d}", slot="interaction.history", source=source, source_version="1",
            authority="untrusted" if generated else "user", lineage="generated" if generated else "verbatim",
            trust="unverified", freshness=turn.at, scope=scope, injection_risk="untrusted_content", body=turn.text,
        ))
    items.append(item(
        id=f"turn:{request.session}:{len(request.turns) + 1:04d}", slot="interaction.query", source=source, source_version="1",
        authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at, scope=scope,
        injection_risk="untrusted_content", body=request.question,
    ))
    return batch("chat-session", "interaction", items)
