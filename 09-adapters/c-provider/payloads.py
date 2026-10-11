"""Payloads to adapt: the specification's example snapshot rendered under both message renderers, and a refusal.

    uv run payloads.py            # the three results, with sizes and hashes

The item set is fixed and vendored; only the renderer varies. cwa-messages/v1 gives one user message with one string;
cwa-message-blocks/v1 gives the same text as one {id, text} entry per item, so an application can put a provider's cache
breakpoint at any item boundary. Both carry system entries and tool entries that the provider adapter has to map.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cwa import AssemblyResult, Snapshot, assemble

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE.parents[1] / "shared" / "contract" / "cwa" / "examples" / "messages-snapshot.json"
MESSAGES, BLOCKS = "cwa-messages/v1", "cwa-message-blocks/v1"


def snapshot(renderer: str = MESSAGES) -> dict:
    document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    document["renderer"] = renderer
    return document


def rendered(renderer: str = MESSAGES) -> AssemblyResult:
    return assemble(Snapshot.from_json(snapshot(renderer)))


def refused() -> AssemblyResult:
    document = snapshot()
    document["budget"]["input"] = 90
    return assemble(Snapshot.from_json(document))


def reserved_output() -> int:
    return snapshot()["budget"]["reserved_output"]


if __name__ == "__main__":
    for label, result in (("messages", rendered(MESSAGES)), ("blocks", rendered(BLOCKS)), ("refused", refused())):
        if result.payload is None:
            print(f"{label}: refused {result.trace['refused']['reason']}; no payload, so no request")
            continue
        ir = json.loads(result.payload)
        content = ir["messages"][0]["content"]
        print(f"{label}: {result.trace['result']['input_tokens']} tokens, sha256 {result.trace['result']['hash'][:16]}, "
              f"{len(ir['system'])} system entr{'y' if len(ir['system']) == 1 else 'ies'}, {len(ir['tools'])} tools, user content is "
              + ("one string" if isinstance(content, str) else f"{len(content)} blocks"))
    sys.exit(0)
