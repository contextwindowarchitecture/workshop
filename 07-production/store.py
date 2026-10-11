"""The snapshot store: every inference the agent makes, kept so any answer can be explained, replayed and re-decided.

    uv run store.py runs                       # stored runs, newest first
    uv run store.py show RUN                   # one run: each inference's decisions, each tool call, the answer
    uv run store.py replay RUN                 # re-assemble every stored snapshot; same bytes, or a finding (R-23)
    uv run store.py whatif policy/candidates/history-tight [--run RUN]
                                               # re-decide stored snapshots under a candidate policy and profile:
                                               # how many inferences would change, and how, before shipping it

A snapshot holds everything that decided a request, so storing it, not the prompt, is what makes an answer debuggable
later. Snapshots are stored once, by digest; runs and inferences point at them. The store is store/cwa.sqlite, or
CWA_W7_STORE. It holds what users asked and what the application knew about them: give it the retention and access
rules of the data in it, and never copy it into the tracing backend (telemetry.py carries digests, not content).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from cwa import Snapshot, assemble

HERE = Path(__file__).resolve().parent
DEFAULT = HERE / "store" / "cwa.sqlite"
SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (digest TEXT PRIMARY KEY, document TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, user TEXT NOT NULL, question TEXT NOT NULL,
    model TEXT NOT NULL, answer TEXT, deployment INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS inferences (run_id TEXT NOT NULL REFERENCES runs, turn INTEGER NOT NULL, snapshot TEXT NOT NULL REFERENCES snapshots,
    payload_sha256 TEXT, input_tokens INTEGER, refused TEXT, trace TEXT NOT NULL, PRIMARY KEY (run_id, turn));
CREATE TABLE IF NOT EXISTS steps (run_id TEXT NOT NULL, turn INTEGER NOT NULL, n INTEGER NOT NULL, tool TEXT NOT NULL, arguments TEXT NOT NULL,
    approved INTEGER NOT NULL, reason TEXT NOT NULL, executed INTEGER NOT NULL, ok INTEGER NOT NULL, PRIMARY KEY (run_id, turn, n));
"""


def path() -> Path:
    return Path(os.environ["CWA_W7_STORE"]) if os.environ.get("CWA_W7_STORE") else DEFAULT


def connect(location: Path | None = None) -> sqlite3.Connection:
    location = location or path()
    location.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(location)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def save(db: sqlite3.Connection, run_id: str, record: dict[str, Any], *, deployment: bool = False) -> None:
    """Keep a run record from agent.run(): snapshots once by digest, then the run, its inferences and its steps."""
    req = record["request"]
    db.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
               (run_id, req["asked_at"], req["user"], req["question"], record["model"], record["answer"], int(deployment)))
    for inference in record["inferences"]:
        trace = inference["trace"]
        digest = trace["context"]["snapshot_digest"]
        db.execute("INSERT OR IGNORE INTO snapshots VALUES (?, ?)", (digest, json.dumps(inference["snapshot"], ensure_ascii=False)))
        db.execute("INSERT OR REPLACE INTO inferences VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (run_id, inference["turn"], digest, (trace["result"] or {}).get("hash"), (trace["result"] or {}).get("input_tokens"),
                    trace["refused"]["reason"], json.dumps(trace, ensure_ascii=False)))
        for n, step in enumerate(inference["steps"], start=1):
            db.execute("INSERT OR REPLACE INTO steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (run_id, inference["turn"], n, step["tool"], json.dumps(step["arguments"], sort_keys=True), int(step["approved"]),
                        step["reason"], int(step["executed"]), int(step["ok"])))
    db.commit()


def runs(db: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.execute("SELECT r.*, COUNT(i.turn) AS inferences FROM runs r LEFT JOIN inferences i USING (run_id) GROUP BY r.run_id ORDER BY started_at DESC, run_id DESC").fetchall()


def decisions(trace: dict[str, Any]) -> dict[str, str]:
    """Every item's fate in one trace: included, compressed, or excluded with its reason; plus the refusal, if any."""
    out = {row["item_id"]: "included" for row in trace["included"]}
    out.update({row["item_id"]: f"compressed:{row['variant_id']}" for row in trace["compressed"]})
    out.update({row["item_id"]: f"excluded:{row['reason']}" for row in trace["excluded"]})
    if trace["refused"]["bool"]:
        out["(assembly)"] = f"refused:{trace['refused']['reason']}"
    return out


@dataclass(frozen=True)
class Replayed:
    run_id: str
    turn: int
    digest: str
    same: bool


def replay(db: sqlite3.Connection, run_id: str) -> list[Replayed]:
    out = []
    for row in db.execute("SELECT i.turn, i.snapshot, i.payload_sha256, i.trace, s.document FROM inferences i JOIN snapshots s ON s.digest = i.snapshot WHERE run_id = ? ORDER BY turn", (run_id,)):
        result = assemble(Snapshot.from_json(json.loads(row["document"])))
        stored = json.loads(row["trace"])
        fresh = {k: v for k, v in result.trace.items() if k not in ("trace_id", "timings")}
        same = fresh == stored and ((result.trace["result"] or {}).get("hash") == row["payload_sha256"])
        out.append(Replayed(run_id, row["turn"], row["snapshot"], same))
    return out


@dataclass(frozen=True)
class Difference:
    run_id: str
    turn: int
    changes: dict[str, tuple[str, str]]  # item -> (now, under the candidate)


def whatif(db: sqlite3.Connection, route_policy: dict[str, Any], profile: dict[str, Any], run_id: str | None = None) -> tuple[int, list[Difference]]:
    """Re-decide every stored snapshot with the candidate route policy and profile in place of the ones it carried, and
    report each inference whose decisions change. Nothing is sent and nothing stored changes."""
    where, params = ("WHERE run_id = ?", (run_id,)) if run_id else ("", ())
    total, differences = 0, []
    for row in db.execute(f"SELECT i.run_id, i.turn, i.trace, s.document FROM inferences i JOIN snapshots s ON s.digest = i.snapshot {where} ORDER BY run_id, turn", params):
        total += 1
        document = json.loads(row["document"])
        document["route_policy"], document["profile"] = route_policy, profile
        candidate = decisions(assemble(Snapshot.from_json(document)).trace)
        current = decisions(json.loads(row["trace"]))
        changes = {k: (current.get(k, "absent"), candidate.get(k, "absent")) for k in sorted(set(current) | set(candidate)) if current.get(k) != candidate.get(k)}
        if changes:
            differences.append(Difference(row["run_id"], row["turn"], changes))
    return total, differences


def show(db: sqlite3.Connection, run_id: str, out: TextIO = sys.stdout) -> None:
    run = db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if run is None:
        print(f"no run {run_id}", file=out)
        return
    print(f"{run_id}  {run['started_at']}  {run['user']}  model {run['model']}{'  [deployment]' if run['deployment'] else ''}\n  q: {run['question'][:100]}", file=out)
    for inf in db.execute("SELECT * FROM inferences WHERE run_id = ? ORDER BY turn", (run_id,)):
        trace = json.loads(inf["trace"])
        tools = [r["item_id"] for r in trace["included"] if r["slot"] == "governance.capabilities"]
        print(f"  turn {inf['turn']}: snapshot {inf['snapshot'][:16]}  " + (f"refused {inf['refused']}" if inf["refused"] else f"{inf['input_tokens']} tokens, payload {inf['payload_sha256'][:12]}") + f"  tools {len(tools)}", file=out)
        for row in trace["excluded"]:
            print(f"      - {row['item_id']}: {row['reason']} [{row['stage']}]", file=out)
        for step in db.execute("SELECT * FROM steps WHERE run_id = ? AND turn = ? ORDER BY n", (run_id, inf["turn"])):
            print(f"      {step['tool']}({step['arguments']}): {'approved' if step['approved'] else 'DENIED'}, {step['reason'][:80]}" + (f" -> {'ok' if step['ok'] else 'error'}" if step["executed"] else ""), file=out)
    print(f"  answer: {run['answer']}", file=out)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("runs")
    sub.add_parser("show").add_argument("run_id")
    sub.add_parser("replay").add_argument("run_id")
    w = sub.add_parser("whatif")
    w.add_argument("candidate", help="a directory with route-policy.json and profile.json")
    w.add_argument("--run")
    args = p.parse_args(argv)
    db = connect()
    if args.command == "runs":
        for row in runs(db):
            print(f"{row['run_id']:<28} {row['started_at']}  {row['user']:<6} {row['inferences']} inference(s)  {'[deployment] ' if row['deployment'] else ''}{(row['answer'] or '(no answer)')[:60]}")
        return 0
    if args.command == "show":
        show(db, args.run_id)
        return 0
    if args.command == "replay":
        replayed = replay(db, args.run_id)
        for r in replayed:
            print(f"turn {r.turn}: {'same bytes, same trace' if r.same else 'DIFFERS'}  {r.digest[:16]}")
        return 0 if replayed and all(r.same for r in replayed) else 1
    candidate = Path(args.candidate)
    total, differences = whatif(db, json.loads((candidate / "route-policy.json").read_text(encoding="utf-8")),
                                json.loads((candidate / "profile.json").read_text(encoding="utf-8")), args.run)
    print(f"{len(differences)} of {total} inference(s) would change under {candidate.name}")
    for d in differences:
        print(f"  {d.run_id} turn {d.turn}:")
        for item, (now, then) in d.changes.items():
            print(f"      {item}: {now} -> {then}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
