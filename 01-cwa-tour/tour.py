"""The tour, from the command line. Every command is model-free and reads nothing outside this directory and the
vendored contract.

    uv run tour.py list                      # the exercises, with what changed in each; no answers
    uv run tour.py run 03-chunk-claims-governing      # assemble it and print the decisions
    uv run tour.py run 07-budget-pressure --payload   # also print the rendered payload
    uv run tour.py reveal 03-chunk-claims-governing   # what it proves and the codes to look for, after predicting
    uv run tour.py replay scenarios/00-baseline/snapshot.json   # assemble a stored snapshot twice; same bytes, same hash
    uv run tour.py diff 00-baseline 02-imperative-chunk          # what changed between two exercises' traces
    uv run tour.py checklist                  # the spec's §6.1 tests, each mapped to a command here

The decisions table has one row per rendered occurrence (+), per excluded item (-), per compressed item (~) and per
conflict group (!). A refusal prints its reason and recovery action and sends nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from cwa import AssemblyResult, Snapshot, SnapshotError, assemble

import exercises

HERE = Path(__file__).resolve().parent


def freeze(document: dict[str, Any]) -> Snapshot:
    return Snapshot.from_json(document)


def report(document: dict[str, Any], result: AssemblyResult, out: TextIO = sys.stdout) -> None:
    """The trace as a table: what was sent, what was left out, what was shortened, and how each conflict went."""
    trace = result.trace
    candidates = {item["id"]: item for batch in document["batches"] for item in batch["items"]}

    def note(item_id: str) -> str:
        item = candidates.get(item_id, {})
        bits = []
        if item.get("relevance") is not None:
            bits.append(f"relevance {item['relevance']:g}")
        if item.get("authority"):
            bits.append(item["authority"])
        return ("  " + ", ".join(bits)) if bits else ""

    if trace["refused"]["bool"]:
        recovery = (trace.get("recovery") or {}).get("action")
        print(f"REFUSED: {trace['refused']['reason']}" + (f"  recovery: {recovery}" if recovery else "")
              + "\n  no payload; nothing reaches a model (R-17)", file=out)
    else:
        budget = trace["budget"]
        margin = f" with a {budget['margin_percent']}% margin" if budget.get("margin_percent") else ""
        print(f"assembled {trace['profile']['id']} v{trace['profile']['version']}: "
              f"{trace['result']['input_tokens']} input tokens of {budget['input']}{margin}, "
              f"payload sha256 {trace['result']['hash'][:16]}", file=out)
    for row in trace["included"]:
        print(f"  + {row['slot']:<27} {row['item_id']:<26} {row['tokens']:>4} tokens{note(row['item_id'])}", file=out)
    for row in trace["compressed"]:
        print(f"  ~ {row['slot']:<27} {row['item_id']:<26} {row['from']:>4} -> {row['to']} tokens  "
              f"variant {row['variant_id']} ({row['method']})", file=out)
    for row in trace["excluded"]:
        slot = row.get("slot") or candidates.get(row["item_id"], {}).get("slot", "")
        extra = ""
        if row.get("duplicate_of"):
            extra = f"  duplicate_of {row['duplicate_of']}"
        if row.get("superseded_by"):
            extra = f"  superseded_by {row['superseded_by']}"
        print(f"  - {slot:<27} {row['item_id']:<26} {row['reason']}  [{row['stage']}]{extra}", file=out)
    for row in trace["conflicts"]:
        winner = f"  winner {row['winner']}" if row.get("winner") else ""
        print(f"  ! {row['kind']:<27} {row['group_id']:<26} {row['resolution']} by {row['decided_by']}{winner}", file=out)
    filled = len(trace["defaults_filled"])
    print(f"  defaults filled: {filled}   snapshot digest: {trace['context']['snapshot_digest'][:16]}   "
          f"tokenizer {trace['context']['tokenizer']}   renderer {trace['context']['renderer']}", file=out)


def show_payload(result: AssemblyResult, out: TextIO = sys.stdout) -> None:
    if result.payload is None:
        print("(no payload)", file=out)
        return
    payload = json.loads(result.payload)
    for entry in payload.get("system", []):
        print("\n-- system --\n" + entry["text"], file=out)
    for tool in payload.get("tools", []):
        print("\n-- tool --\n" + json.dumps(tool, ensure_ascii=False), file=out)
    for message in payload.get("messages", []):
        content = message["content"]
        if isinstance(content, list):
            content = "\n".join(block["text"] for block in content)
        print(f"\n-- {message['role']} --\n{content}", file=out)


def cmd_list(_: argparse.Namespace) -> int:
    for exercise in exercises.EXERCISES:
        print(f"{exercise.name}\n    {exercise.description}")
        for question in exercise.predict:
            print(f"    ? {question}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    exercise = exercises.BY_NAME[args.exercise]
    document = exercises.snapshot(exercise.name)
    print(f"{exercise.name}: {exercise.description}\n")
    try:
        result = assemble(freeze(document))
    except SnapshotError as error:
        print("REJECTED before assembly: the snapshot is invalid (R-17). No payload, no trace.")
        for problem in error.problems:
            print(f"  {problem}")
        return 0
    report(document, result)
    if args.payload:
        show_payload(result)
    return 0


def cmd_reveal(args: argparse.Namespace) -> int:
    exercise = exercises.BY_NAME[args.exercise]
    print(f"{exercise.name}  ({', '.join(exercise.rules)})\n\n{exercise.proves}\n")
    if exercise.rejected:
        print("look for: a rejection, not a refusal; no trace at all")
    elif exercise.look_for:
        print("look for: " + ", ".join(exercise.look_for))
    else:
        print("look for: no new exclusion; compare with 00-baseline using `tour.py diff`")
    return 0


def _comparable(trace: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in trace.items() if k not in ("trace_id", "timings")}


def cmd_replay(args: argparse.Namespace) -> int:
    document = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    first = assemble(freeze(document))
    second = assemble(freeze(document))
    print(f"snapshot digest  {first.trace['context']['snapshot_digest']}")
    for label, result in (("first run ", first), ("second run", second)):
        hash_ = result.trace["result"]["hash"] if result.trace["result"] else "(refused)"
        print(f"{label}       payload sha256 {hash_}   trace_id {result.trace['trace_id']}")
    same = first.payload == second.payload and _comparable(first.trace) == _comparable(second.trace)
    print("identical payload bytes and trace (trace_id aside): " + ("yes" if same else "NO"))
    expected = Path(args.snapshot).parent / "trace.json"
    if expected.exists():
        committed = json.loads(expected.read_text(encoding="utf-8"))
        print("matches the committed trace beside it: " + ("yes" if _comparable(first.trace) == committed else "NO"))
    return 0 if same else 1


def cmd_diff(args: argparse.Namespace) -> int:
    results = {}
    for name in (args.left, args.right):
        try:
            results[name] = assemble(freeze(exercises.snapshot(name))).trace
        except SnapshotError:
            print(f"{name} is rejected; nothing to diff")
            return 1
    left, right = results[args.left], results[args.right]

    def ids(trace: dict[str, Any], key: str) -> set[str]:
        return {row["item_id"] for row in trace[key]}

    changes = 0
    for key in ("included", "excluded", "compressed"):
        for item_id in sorted(ids(left, key) - ids(right, key)):
            print(f"  {key}: {item_id} only in {args.left}")
            changes += 1
        for item_id in sorted(ids(right, key) - ids(left, key)):
            reason = next((r.get("reason", "") for r in right[key] if r["item_id"] == item_id), "")
            print(f"  {key}: {item_id} only in {args.right}" + (f"  ({reason})" if reason else ""))
            changes += 1
    if left["refused"] != right["refused"]:
        print(f"  refused: {left['refused']} -> {right['refused']}")
        changes += 1
    if not changes:
        print("  same decisions: identical included, excluded and compressed lists, same refusal state")
    for name, trace in ((args.left, left), (args.right, right)):
        hash_ = trace["result"]["hash"][:16] if trace["result"] else "refused: " + str(trace["refused"]["reason"])
        print(f"  {name}: payload {hash_}   digest {trace['context']['snapshot_digest'][:16]}")
    if left["result"] and right["result"] and left["result"]["hash"] != right["result"]["hash"]:
        print("  payload bytes differ; the decisions above say whether anything else did")
    return 0


CHECKLIST = (
    ("Assembly snapshot", "R-23", "tour.py replay scenarios/00-baseline/snapshot.json"),
    ("Golden task", "R-21", "tour.py run 00-baseline  (refunds-eu:v17#p4 is in evidence.knowledge)"),
    ("Counterfactual ablation", "R-21", "tour.py run 11-evidence-required  (remove the evidence; the trace explains the refusal)"),
    ("Conflict", "R-7", "tour.py diff 00-baseline 02-imperative-chunk  (imperative text changes no decision)"),
    ("Budget pressure", "R-16", "tour.py run 07-budget-pressure  (protected slots intact; droppable, then compressible)"),
    ("Freshness", "R-9", "tour.py run 05-expired-memory"),
    ("Refusal", "R-12", "tour.py run 11-evidence-required"),
    ("Capability source", "R-15", "tour.py run 09-tool-from-mcp"),
    ("Cache reuse", "R-7", "W6; needs two turns under a cache-ordered profile"),
)


def cmd_checklist(_: argparse.Namespace) -> int:
    print("Spec §6.1, the tests the trace makes possible, each as a command here:\n")
    for test, rule, command in CHECKLIST:
        print(f"  [ ] {test:<24} {rule:<5} {command}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    run = sub.add_parser("run")
    run.add_argument("exercise", choices=exercises.names())
    run.add_argument("--payload", action="store_true", help="also print the rendered payload")
    run.set_defaults(func=cmd_run)
    reveal = sub.add_parser("reveal")
    reveal.add_argument("exercise", choices=exercises.names())
    reveal.set_defaults(func=cmd_reveal)
    replay = sub.add_parser("replay")
    replay.add_argument("snapshot")
    replay.set_defaults(func=cmd_replay)
    diff = sub.add_parser("diff")
    diff.add_argument("left", choices=exercises.names())
    diff.add_argument("right", choices=exercises.names())
    diff.set_defaults(func=cmd_diff)
    sub.add_parser("checklist").set_defaults(func=cmd_checklist)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
