"""What the whole kit shares: the request, the data, the knowledge base, the routes, and item and batch helpers.

The firm is Larkbridge Wealth (fictional). The tenant is fixed; a request is one client's message in one portal session
about their one account. Everything here is infrastructure; the capstone's work is in the modules impl.py selects.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
KNOWLEDGE = DATA / "knowledge"
POLICY = HERE / "policy"
TENANT = "larkbridge"
sys.path.insert(0, str(ROOT / "shared"))
from fernway.corpus import Chunk, bm25 as _bm25, chunks as _chunks, front_matter, jaccard, words  # noqa: E402,F401


@dataclass(frozen=True)
class Turn:
    role: str  # "user" or "assistant"
    text: str
    at: str


@dataclass(frozen=True)
class Request:
    client: str
    session: str
    asked_at: str
    question: str
    turns: tuple[Turn, ...] = ()
    device: str = "known"  # "known" or "new": what the portal's device check said about this session
    faults: frozenset[str] = frozenset()

    @property
    def account(self) -> str:
        return clients()[self.client]["account"]

    @property
    def scope(self) -> dict[str, str]:
        return {"tenant": TENANT, "user": self.client, "session": self.session, "task": self.account}

    @classmethod
    def load(cls, path: str | Path) -> Request:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(client=d["client"], session=d["session"], asked_at=d["asked_at"], question=d["question"], turns=tuple(Turn(**t) for t in d.get("turns", [])),
                   device=d.get("device", "known"), faults=frozenset(d.get("faults", [])))


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _load(name: str) -> Any:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def clients() -> dict[str, Any]:
    return _load("clients.json")["clients"]


def ledger() -> dict[str, Any]:
    return _load("ledger.json")


def market() -> dict[str, Any]:
    return _load("market.json")


def tools() -> dict[str, Any]:
    return _load("tools.json")


def intents() -> dict[str, Any]:
    return _load("intents.json")


def chunks() -> tuple[Chunk, ...]:
    return _chunks(KNOWLEDGE, "kb")


def bm25(question: str) -> list[tuple[Chunk, float]]:
    return _bm25(question, directory=KNOWLEDGE, prefix="kb")


def routes() -> dict[str, Any]:
    return json.loads((POLICY / "routes.json").read_text(encoding="utf-8"))


def capabilities_policy() -> dict[str, Any]:
    return json.loads((POLICY / "capabilities.json").read_text(encoding="utf-8"))


def policy(route: str, name: str) -> Any:
    path = POLICY / route / name
    return json.loads(path.read_text(encoding="utf-8")) if name.endswith(".json") else path.read_text(encoding="utf-8")


def budget(tier: str) -> dict[str, Any]:
    t = routes()["tiers"][tier]
    return {"input": t["model_context_limit"] - t["reserved_output"], "reserved_output": t["reserved_output"], "margin_percent": t["margin_percent"]}


def item(**fields: Any) -> dict[str, Any]:
    return {"token_budget": None, "variants": [], "conflict_policy": "defers", "eligibility": "route-policy", **fields}


def batch(producer_id: str, kind: str, items: list[dict[str, Any]], excluded: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"producer": {"id": producer_id, "kind": kind}, "items": items, "excluded": excluded or []}
