"""Producers that are given, not labs: the route's instructions and the conversation. Read W2's fixed.py for why each
field is what it is."""

from __future__ import annotations

from common import POLICY, Batch, Request, batch, item

from fernway.corpus import front_matter  # noqa: E402  (common put shared/ on sys.path)


def app_policy() -> Batch:
    meta, body = front_matter((POLICY / "instructions.md").read_text(encoding="utf-8"))
    return batch("app-policy", "policy", [item(
        id="policy:instructions", slot="governance.instructions", source="app:policy/instructions.md",
        source_version=meta["version"], authority="governing", trust="verified", freshness=meta["updated"],
        conflict_policy="governs", lineage="verbatim", injection_risk="none", body=body,
    )])


def chat_session(request: Request) -> Batch:
    return batch("chat-session", "interaction", [item(
        id=f"turn:{request.session}:0001", slot="interaction.query", source=f"chat:{request.session}",
        source_version="1", authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at,
        scope={"session": request.session}, injection_risk="untrusted_content", body=request.question,
    )])
