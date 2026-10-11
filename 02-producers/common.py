"""What every lab shares: the request, the corpus, the policy, the freeze, and the decisions table.

None of this is the lesson. The lesson is in labs/, where you write the producers; this module gives you the request
they answer, the text they retrieve from, the route they are admitted under, and a way to freeze their batches into a
snapshot and read what the assembler decided. Nothing here assembles except freeze_and_assemble(), which hands the
snapshot to the reference assembler and returns its result unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any, TextIO

from cwa import AssemblyResult, Snapshot, assemble

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTRACT = ROOT / "shared" / "contract" / "cwa"
DATA = HERE / "data"
POLICY = HERE / "policy"
HELP_CENTER = DATA / "help-center"

Item = dict[str, Any]
Batch = dict[str, Any]


# --- the request -----------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Turn:
    role: str  # "user" or "assistant"
    text: str
    at: str


@dataclass(frozen=True)
class Request:
    """One question from one signed-in user, with the clock read once. Everything a producer may read about the
    request is here; the application authenticated the user and bound the scope before any producer ran."""

    tenant: str
    user: str
    session: str
    asked_at: str
    question: str
    turns: tuple[Turn, ...] = ()
    account_read_at: str | None = None  # when the account row was read; None means at asked_at
    faults: frozenset[str] = frozenset()  # deliberate producer bugs a scenario injects, by name

    @property
    def scope(self) -> dict[str, str]:
        return {"tenant": self.tenant, "user": self.user, "session": self.session}


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


# --- items and batches -----------------------------------------------------------------------------------------------


def item(**fields: Any) -> Item:
    """A context item with its policy fields declared rather than defaulted, so defaults_filled stays short and every
    field the assembler acts on is one the producer chose (R-3). Pass any field to override."""
    return {"token_budget": None, "variants": [], "conflict_policy": "defers", "eligibility": "route-policy", **fields}


def batch(producer_id: str, kind: str, items: list[Item], excluded: list[dict[str, Any]] | None = None) -> Batch:
    return {"producer": {"id": producer_id, "kind": kind}, "items": items, "excluded": excluded or []}


def content_hash(text: str) -> str:
    """The key variants are cached by (R-18): the SHA-256 of the body's UTF-8 bytes."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- the corpus ------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Chunk:
    id: str  # help:<article>@<version>#<paragraph>
    article: str
    title: str
    version: str
    updated: str
    text: str


def front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a leading `---` block of `key: value` lines from the body that follows it."""
    head, sep, body = text.partition("\n---\n")
    if not text.startswith("---\n") or not sep:
        raise ValueError("expected a --- front matter block")
    fields: dict[str, str] = {}
    for line in head.splitlines()[1:]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, body.strip()


@cache
def chunks() -> tuple[Chunk, ...]:
    """Every paragraph of every article, in file order. A chunk id names the article, its version and the paragraph,
    so an edited article gets new ids and a cited id always means the text it was cited for."""
    found = []
    for path in sorted(HELP_CENTER.glob("*.md")):
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        for index, paragraph in enumerate(p.strip() for p in body.split("\n\n") if p.strip()):
            found.append(Chunk(f"help:{meta['id']}@{meta['version']}#{index}", meta["id"], meta["title"],
                               meta["version"], meta["updated"], paragraph))
    return tuple(found)


_WORD = re.compile(r"[a-z0-9]+")


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def bm25(question: str, k1: float = 1.5, b: float = 0.75) -> list[tuple[Chunk, float]]:
    """Every chunk scored against the question by BM25 over its text, best first, ties broken by id so the
    order is the same on every machine. A plain implementation, with no dependencies, so the committed scenarios hold
    everywhere. Scoring is the retriever's job and not the lesson; packaging the scores is."""
    docs = [(chunk, words(chunk.text)) for chunk in chunks()]
    n = len(docs)
    avg = sum(len(terms) for _, terms in docs) / n
    df: dict[str, int] = {}
    for _, terms in docs:
        for term in set(terms):
            df[term] = df.get(term, 0) + 1
    query = words(question)
    scored = []
    for chunk, terms in docs:
        score = 0.0
        for term in set(query):
            tf = terms.count(term)
            if not tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(terms) / avg))
        scored.append((chunk, round(score, 3)))
    return sorted(scored, key=lambda pair: (-pair[1], pair[0].id))


def jaccard(a: str, b: str) -> float:
    """Word-set overlap, the near-duplicate measure the retrieval lab uses. 1.0 means the same words."""
    x, y = set(words(a)), set(words(b))
    return len(x & y) / len(x | y) if x | y else 1.0


# --- the policy and the freeze ---------------------------------------------------------------------------------------


def policy(name: str) -> Any:
    return json.loads((POLICY / name).read_text(encoding="utf-8"))


def contract(relative: str) -> Any:
    return json.loads((CONTRACT / relative).read_text(encoding="utf-8"))


def snapshot(request: Request, batches: list[Batch]) -> dict[str, Any]:
    """Freeze the producers' batches with the route's policy, the profile, the budget and the clock
    (snapshot.schema.json). The application does this once per call, after every producer has run (R-23)."""
    settings = policy("assembly.json")
    return {
        "assembly_time": request.asked_at,
        "scope": request.scope,
        "budget": settings["budget"],
        "profile": policy("profile.json"),
        "route_policy": policy("route-policy.json"),
        "tokenizer": settings["tokenizer"],
        "renderer": settings["renderer"],
        "batches": batches,
        "conflicts": [],
    }


def freeze_and_assemble(request: Request, batches: list[Batch]) -> tuple[dict[str, Any], AssemblyResult]:
    document = snapshot(request, batches)
    return document, assemble(Snapshot.from_json(document))


# --- reading the result ----------------------------------------------------------------------------------------------


def report(document: dict[str, Any], result: AssemblyResult, out: TextIO = sys.stdout, defaults: bool = False) -> None:
    """The trace as a table: + included, ~ compressed, - excluded with reason and stage, ! conflicts."""
    trace = result.trace
    candidates = {i["id"]: i for b in document["batches"] for i in b["items"]}
    if trace["refused"]["bool"]:
        recovery = (trace.get("recovery") or {}).get("action")
        print(f"REFUSED: {trace['refused']['reason']}" + (f"  recovery: {recovery}" if recovery else ""), file=out)
    else:
        budget = trace["budget"]
        print(f"assembled {trace['profile']['id']} v{trace['profile']['version']}: {trace['result']['input_tokens']} "
              f"input tokens of {budget['input']} with a {budget.get('margin_percent', 0)}% margin, "
              f"payload sha256 {trace['result']['hash'][:16]}", file=out)
    for row in trace["included"]:
        rel = candidates.get(row["item_id"], {}).get("relevance")
        print(f"  + {row['slot']:<22} {row['item_id']:<30} {row['tokens']:>4} tokens"
              + (f"  relevance {rel:g}" if rel is not None else ""), file=out)
    for row in trace["compressed"]:
        print(f"  ~ {row['slot']:<22} {row['item_id']:<30} {row['from']:>4} -> {row['to']} tokens  "
              f"variant {row['variant_id']} ({row['method']})", file=out)
    for row in trace["excluded"]:
        slot = row.get("slot") or candidates.get(row["item_id"], {}).get("slot", "")
        extra = f"  duplicate_of {row['duplicate_of']}" if row.get("duplicate_of") else ""
        extra += f"  superseded_by {row['superseded_by']}" if row.get("superseded_by") else ""
        print(f"  - {slot:<22} {row['item_id']:<30} {row['reason']}  [{row['stage']}]{extra}", file=out)
    for row in trace["conflicts"]:
        print(f"  ! {row['kind']:<22} {row['group_id']:<30} {row['resolution']} by {row['decided_by']}", file=out)
    filled = trace["defaults_filled"]
    print(f"  defaults filled: {len(filled)}   snapshot digest {trace['context']['snapshot_digest'][:16]}", file=out)
    if defaults and filled:
        by_item: dict[str, list[str]] = {}
        for row in filled:
            by_item.setdefault(row["item_id"], []).append(row["field"])
        for item_id, fields in by_item.items():
            print(f"      {item_id:<30} {', '.join(fields)}", file=out)
