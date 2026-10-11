"""What the whole kit shares: the request, the data, the guidelines, the routes, and item and batch helpers.

The practice is Harbor Street Family Practice (fictional). The tenant is fixed; a request is one clinician's request
during one encounter with one patient, with the room's transcript so far. Everything here is infrastructure; the
capstone's work is in the modules impl.py selects.
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
GUIDELINES = DATA / "guidelines"
POLICY = HERE / "policy"
TENANT = "harbor-street"
sys.path.insert(0, str(ROOT / "shared"))
from fernway.corpus import Chunk, bm25 as _bm25, chunks as _chunks, front_matter, jaccard, words  # noqa: E402,F401


@dataclass(frozen=True)
class Turn:
    speaker: str  # "clinician" or "patient", as the speech-to-text engine labelled it: a guess, never an identity
    text: str
    at: str


@dataclass(frozen=True)
class Request:
    encounter: str
    clinician: str
    session: str
    asked_at: str
    question: str
    turns: tuple[Turn, ...] = ()
    faults: frozenset[str] = frozenset()

    @property
    def patient(self) -> str:
        return encounters()[self.encounter]["patient"]

    @property
    def scope(self) -> dict[str, str]:
        # Scope keys are the specification's closed set (tenant, user, session, task, locale, step). The task is this
        # patient's care, so prior notes about the patient are in scope across encounters; the encounter rides in sources.
        return {"tenant": TENANT, "user": self.clinician, "session": self.session, "task": self.patient}

    @classmethod
    def load(cls, path: str | Path) -> Request:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(encounter=d["encounter"], clinician=d["clinician"], session=d["session"], asked_at=d["asked_at"], question=d["question"],
                   turns=tuple(Turn(**t) for t in d.get("turns", [])), faults=frozenset(d.get("faults", [])))


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _load(name: str) -> Any:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def patients() -> dict[str, Any]:
    return _load("patients.json")["patients"]


def clinicians() -> dict[str, Any]:
    return _load("clinicians.json")["clinicians"]


def encounters() -> dict[str, Any]:
    return _load("encounters.json")["encounters"]


def telemetry() -> dict[str, Any]:
    return _load("telemetry.json")["readings"]


def ehr_notes() -> list[dict[str, Any]]:
    return _load("ehr_notes.json")["notes"]


def tools() -> dict[str, Any]:
    return _load("tools.json")


def intents() -> dict[str, Any]:
    return _load("intents.json")


def chunks() -> tuple[Chunk, ...]:
    return _chunks(GUIDELINES, "guide")


def bm25(question: str) -> list[tuple[Chunk, float]]:
    return _bm25(question, directory=GUIDELINES, prefix="guide")


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
