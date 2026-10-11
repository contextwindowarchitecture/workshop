"""What the Go package `briefing` in integrations/fullsend shares with this Python port: the item and batch shape, the
freeze, the assembler call and the handoff to a runtime.

A host that already has a notion of who may speak (here: repository permission) becomes a CWA application by writing
producers that read the host with read credentials, freezing a snapshot before anything else runs, and handing the
payload to the runtime in the places the runtime already takes text. Nothing here calls a model. The constants are the
Go package's, so a snapshot frozen here has the digest the Go integration committed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from cwa import AssemblyResult, Snapshot
from cwa import assemble as cwa_assemble

HERE = Path(__file__).resolve().parent
TOKENIZER = "estimate-utf8/v1"   # the published estimate; the 20% margin covers its error (R-16)
RENDERER = "cwa-messages/v1"     # system entries, one user message, tools (R-7)
WINDOW = 200_000                 # the model's context limit; budget.input is the briefing's share, the rest is the runtime's
MARGIN_PERCENT = 20
SYSTEM_SEPARATOR = "\n\n"        # the only text the handoff adds; the attributes hash what the runtime receives


def read(fixture: str = "issue-7811") -> dict[str, Any]:
    """A forge read: everything a host-side producer fetched before the sandbox starts (fixtures/, fictional)."""
    return json.loads((HERE / "fixtures" / f"{fixture}.json").read_text(encoding="utf-8"))


def registry(route_version: str = "fullsend-triage/v1") -> tuple[dict[str, Any], dict[str, Any]]:
    """The route policy and the profile for a route version, from registry/."""
    route = json.loads((HERE / "registry" / f"{route_version.split('/')[0]}.route-policy.json").read_text(encoding="utf-8"))
    assert route["version"] == route_version, route_version
    profile = next(json.loads(p.read_text(encoding="utf-8")) for p in (HERE / "registry").glob("*.profile.json")
                   if json.loads(p.read_text(encoding="utf-8"))["route_policy_version"] == route_version)
    return route, profile


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def new_item(id: str, slot: str, source: str, source_version: str, authority: str, freshness: str, body: str, **fields: Any) -> dict[str, Any]:
    """The eight required fields (R-2). Governing and state items are verified by the source that produced them;
    everything else is the producer's unverified claim, which only the governance gate reads (R-10, R-15)."""
    trust = "verified" if authority in ("governing", "state") else "unverified"
    return {"id": id, "slot": slot, "source": source, "source_version": source_version, "authority": authority,
            "trust": trust, "freshness": freshness, "body": body, **fields}


def batch(producer_id: str, kind: str, items: list[dict[str, Any]], excluded: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """One producer's output. Its identity is the runner component that read the source, bound here, never read
    from an item (R-15)."""
    return {"producer": {"id": producer_id, "kind": kind}, "items": list(items), "excluded": list(excluded or [])}


def freeze(r: dict[str, Any], scope: dict[str, str], route: dict[str, Any], profile: dict[str, Any], input: int,
           batches: list[dict[str, Any]], conflicts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The snapshot: everything that can affect an assembly, frozen before it begins (R-23). The budget is the
    briefing's share of the window; the rest is reserved for what the runtime adds after the handoff (R-16)."""
    return {
        "assembly_time": r["assembly_time"],
        "scope": scope,
        "budget": {"input": input, "reserved_output": WINDOW - input, "margin_percent": MARGIN_PERCENT},
        "profile": profile,
        "route_policy": route,
        "tokenizer": TOKENIZER,
        "renderer": RENDERER,
        "batches": sorted(batches, key=lambda b: b["producer"]["id"]),
        "conflicts": list(conflicts or []),
    }


def assemble(document: dict[str, Any]) -> AssemblyResult:  # cwa-lint: allow, a wrapper that only calls cwa.assemble
    """Admission, conflicts, fitting and rendering are the assembler's; this module only produces and freezes."""
    return cwa_assemble(Snapshot.from_json(document))


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def handoff(document: dict[str, Any], result: AssemblyResult) -> dict[str, Any]:
    """The payload mapped onto the two inputs every fullsend runtime already takes: the agent definition (the system
    entries, joined) and the prompt (the one user message), with the span attributes the run's root span records.
    A refusal has no definition or prompt, only attributes: no sandbox starts (R-17)."""
    trace = result.trace
    attrs: dict[str, Any] = {"cwa.route": document["route_policy"]["route"], "cwa.profile.id": trace["profile"]["id"],
                             "cwa.profile.version": trace["profile"]["version"], "cwa.snapshot_digest": trace["context"]["snapshot_digest"],
                             "cwa.refused": result.payload is None}
    if result.payload is None:
        attrs["cwa.refused.reason"] = trace["refused"]["reason"]
        if trace.get("recovery"):
            attrs["cwa.recovery.action"] = trace["recovery"]["action"]
        return {"agent_definition": None, "prompt": None, "attributes": attrs}
    rendered = json.loads(result.payload)
    assert len(rendered["messages"]) == 1 and rendered["messages"][0]["role"] == "user", "cwa-messages/v1 renders one user message"
    definition = SYSTEM_SEPARATOR.join(e["text"] for e in rendered.get("system", []))
    prompt = rendered["messages"][0]["content"]
    attrs.update({"cwa.payload.sha256": trace["result"]["hash"], "cwa.input_tokens": trace["result"]["input_tokens"],
                  "cwa.included": len(trace["included"]), "cwa.excluded": len(trace["excluded"]),
                  "cwa.handoff.agent_definition.sha256": digest(definition), "cwa.handoff.prompt.sha256": digest(prompt)})
    return {"agent_definition": definition, "prompt": prompt, "attributes": attrs}
