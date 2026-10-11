"""Two producers you are given, so a snapshot can be assembled while you write the other three.

    app-policy     governance.instructions   policy/instructions.md, versioned by the team that owns the route
    chat-session   interaction.history       every prior turn; how many fit is the route's decision
                   interaction.query         the question being asked now

Read them once: they show the fields a governance item and an interaction item carry, and they are the shape your
own producers should have.
"""

from __future__ import annotations

from common import POLICY, Batch, Request, batch, front_matter, item


def app_policy() -> Batch:
    """Governance must be verified and unmarked, or the governance gate excludes it (R-10)."""
    meta, body = front_matter((POLICY / "instructions.md").read_text(encoding="utf-8"))
    return batch("app-policy", "policy", [item(
        id="policy:instructions", slot="governance.instructions", source="app:policy/instructions.md",
        source_version=meta["version"], authority="governing", trust="verified", freshness=meta["updated"],
        conflict_policy="governs", lineage="verbatim", injection_risk="none", body=body,
    )])


def turn_id(session: str, n: int) -> str:
    return f"turn:{session}:{n:04d}"  # zero-padded, so id order is conversation order


def chat_session(request: Request) -> Batch:
    """Every prior turn and the live query. A prior model turn carries untrusted authority and generated lineage
    (R-1); every turn and the query carry the injection marker (R-10) and the session scope (R-2)."""
    scope = {"session": request.session}
    source = f"chat:{request.session}"
    items = []
    for n, turn in enumerate(request.turns, start=1):
        generated = turn.role == "assistant"
        items.append(item(
            id=turn_id(request.session, n), slot="interaction.history", source=source, source_version="1",
            authority="untrusted" if generated else "user", lineage="generated" if generated else "verbatim",
            trust="unverified", freshness=turn.at, scope=scope, injection_risk="untrusted_content", body=turn.text,
        ))
    items.append(item(
        id=turn_id(request.session, len(request.turns) + 1), slot="interaction.query", source=source,
        source_version="1", authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at,
        scope=scope, injection_risk="untrusted_content", body=request.question,
    ))
    return batch("chat-session", "interaction", items)
