"""A black-box harness for assemblers behind the adapter protocol: run one, compare several, report conformance.

    uv run harness.py run <snapshot.json> [--impl labs]                 # one adapter, one snapshot: the outcome
    uv run harness.py compare <case dir> [--adapter "cmd" ...]          # every adapter against the expectation and each other
    uv run harness.py conformance [--impl labs] [--adapter "cmd"]       # all vendored cases and rejections: conformance-report.json
    uv run harness.py agreement <snapshot.json> --adapter "cmd" --adapter "cmd"   # do these assemblers produce the same bytes?

An adapter is any command that speaks the protocol. The default is this module's Python adapter (solution/ or, with
--impl labs, yours). Pass --adapter to add others: the demo's Go and Rust binaries, or its TypeScript adapter, each a
different implementation of the same specification. The pass rule is the published one: payload bytes equal, trace
equal field for field with trace_id, timings and recovery.detail removed, and a case that uses an optional component
the adapter lacks counts as skipped.
"""

from __future__ import annotations

import argparse
import base64
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = ROOT / "shared" / "contract" / "cwa"
CASES, REJECTIONS = CONTRACT / "conformance" / "cases", CONTRACT / "conformance" / "rejections"
IGNORED = ("trace_id", "timings")
OPTIONAL_RENDERERS = {"cwa-message-blocks/v1"}


def default_command(which: str | None = None) -> list[str]:
    import os
    chosen = which or os.environ.get("CWA_W9B_IMPL", "solution")
    return ["uv", "run", "--quiet", "python", str(HERE / chosen / "adapter.py")]


@dataclass(frozen=True)
class Outcome:
    kind: str  # assembled | refused | rejected | unsupported | error
    payload: bytes | None
    trace: dict[str, Any] | None
    stderr: str


def run_adapter(command: list[str], snapshot_bytes: bytes) -> Outcome:
    proc = subprocess.run(command, input=snapshot_bytes, capture_output=True, cwd=HERE)
    err = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode == 2:
        return Outcome("rejected", None, None, err)
    if proc.returncode == 3:
        return Outcome("unsupported", None, None, err)
    if proc.returncode != 0:
        return Outcome("error", None, None, f"exit {proc.returncode}: {err}")
    try:
        answer = json.loads(proc.stdout.decode("utf-8"))
        payload = base64.b64decode(answer["payload"]) if answer["payload"] is not None else None
        return Outcome("assembled" if payload is not None else "refused", payload, answer["trace"], err)
    except (ValueError, KeyError, TypeError) as error:
        return Outcome("error", None, None, f"stdout is not the protocol's JSON object: {error}")


def comparable(trace: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in trace.items() if k not in IGNORED}
    if isinstance(out.get("recovery"), dict):
        out["recovery"] = {k: v for k, v in out["recovery"].items() if k != "detail"}
    return out


def first_difference(actual: Any, expected: Any, path: str = "") -> str | None:
    """A JSON pointer to the first place two documents differ, keys in UTF-16 order, or None."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        for key in sorted(set(actual) | set(expected), key=lambda k: k.encode("utf-16-be")):
            if key not in actual or key not in expected:
                return f"{path}/{key}"
            found = first_difference(actual[key], expected[key], f"{path}/{key}")
            if found:
                return found
        return None
    if isinstance(actual, list) and isinstance(expected, list):
        for i in range(max(len(actual), len(expected))):
            if i >= len(actual) or i >= len(expected):
                return f"{path}/{i}"
            found = first_difference(actual[i], expected[i], f"{path}/{i}")
            if found:
                return found
        return None
    return None if actual == expected else (path or "/")


def judge_case(case: Path, outcome: Outcome) -> tuple[str, str]:
    """passed | failed | skipped, and why."""
    expected_trace = json.loads((case / "expected.trace.json").read_text(encoding="utf-8"))
    expected_payload = (case / "expected.payload.txt").read_bytes() if (case / "expected.payload.txt").exists() else None
    if outcome.kind == "unsupported":
        snapshot = json.loads((case / "snapshot.json").read_text(encoding="utf-8"))
        if snapshot.get("renderer") in OPTIONAL_RENDERERS:
            return "skipped", outcome.stderr
        return "failed", f"required component: {outcome.stderr}"
    if outcome.kind in ("rejected", "error"):
        return "failed", outcome.stderr[:200]
    if outcome.payload != expected_payload:
        return "failed", "payload bytes differ"
    where = first_difference(comparable(outcome.trace), comparable(expected_trace))
    return ("passed", "") if where is None else ("failed", f"trace differs at {where}")


def judge_rejection(rejection: Path, outcome: Outcome) -> tuple[str, str]:
    if outcome.kind == "rejected":
        return "rejected", ""
    if outcome.kind == "unsupported":
        return "skipped", outcome.stderr
    return "failed", f"not rejected: {outcome.kind}"


def conformance(command: list[str], name: str, version: str, language: str) -> dict[str, Any]:
    lock = json.loads((ROOT / "shared" / "contract" / "cwa.lock.json").read_text(encoding="utf-8"))
    report: dict[str, Any] = {"implementation": {"name": name, "version": version, "language": language},
                              "contract": {"repository": lock["repository"], "commit": lock["spec_commit"], "dirty": lock.get("dirty", False)},
                              "cases": [], "rejections": []}
    for case in sorted(CASES.iterdir()):
        meta = json.loads((case / "case.json").read_text(encoding="utf-8"))
        outcome, _ = judge_case(case, run_adapter(command, (case / "snapshot.json").read_bytes()))
        report["cases"].append({"id": case.name, "rules": meta["rules"], "outcome": outcome})
    for rejection in sorted(REJECTIONS.iterdir()):
        meta = json.loads((rejection / "case.json").read_text(encoding="utf-8"))
        outcome, _ = judge_rejection(rejection, run_adapter(command, (rejection / "snapshot.json").read_bytes()))
        report["rejections"].append({"id": rejection.name, "rules": meta["rules"], "outcome": outcome})
    return report


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("run", "compare", "agreement"):
        s = sub.add_parser(name)
        s.add_argument("target")
        s.add_argument("--adapter", action="append", default=[], help="an adapter command line; may repeat")
        s.add_argument("--impl", choices=["labs", "solution"], default=None)
    c = sub.add_parser("conformance")
    c.add_argument("--adapter"); c.add_argument("--impl", choices=["labs", "solution"], default=None)
    c.add_argument("--name", default="cwa-assembler"); c.add_argument("--version", default="0.0.1"); c.add_argument("--language", default="python")
    c.add_argument("--out", default="conformance-report.json")
    args = p.parse_args(argv)
    if args.command == "conformance":
        command = shlex.split(args.adapter) if args.adapter else default_command(args.impl)
        report = conformance(command, args.name, args.version, args.language)
        (HERE / args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        passed = sum(c["outcome"] == "passed" for c in report["cases"]); skipped = sum(c["outcome"] == "skipped" for c in report["cases"])
        rejected = sum(r["outcome"] == "rejected" for r in report["rejections"])
        print(f"{passed}/{len(report['cases'])} cases passed ({skipped} skipped), {rejected}/{len(report['rejections'])} rejections rejected -> {args.out}")
        for c in report["cases"]:
            if c["outcome"] == "failed":
                print(f"  FAILED {c['id']}")
        for r in report["rejections"]:
            if r["outcome"] == "failed":
                print(f"  NOT REJECTED {r['id']}")
        return 0 if passed + skipped == len(report["cases"]) and rejected + sum(r["outcome"] == "skipped" for r in report["rejections"]) == len(report["rejections"]) else 1
    commands = [shlex.split(a) for a in args.adapter] or [default_command(args.impl)]
    if args.command == "run":
        outcome = run_adapter(commands[0], Path(args.target).read_bytes())
        print(f"{outcome.kind}" + (f": {outcome.stderr}" if outcome.stderr else ""))
        if outcome.trace:
            print(f"  digest {outcome.trace['context']['snapshot_digest'][:16]}  " + (f"payload sha256 {outcome.trace['result']['hash'][:16]}, {outcome.trace['result']['input_tokens']} tokens" if outcome.trace["result"] else f"refused {outcome.trace['refused']['reason']}"))
        return 0
    if args.command == "compare":
        case = Path(args.target)
        outcomes = [(" ".join(c), run_adapter(c, (case / "snapshot.json").read_bytes())) for c in commands]
        for label, outcome in outcomes:
            verdict, why = judge_case(case, outcome)
            print(f"{verdict:<8} {label}" + (f"  ({why})" if why else ""))
        hashes = {(o.trace or {}).get("result", {}) and o.trace["result"]["hash"] for _, o in outcomes}
        if len(outcomes) > 1:
            print("agree" if len(hashes) == 1 else "DISAGREE: the adapters produced different payloads")
        return 0
    outcomes = [(" ".join(c), run_adapter(c, Path(args.target).read_bytes())) for c in commands]
    first = outcomes[0][1]
    for label, outcome in outcomes:
        same_payload = outcome.payload == first.payload
        where = first_difference(comparable(outcome.trace or {}), comparable(first.trace or {}))
        print(f"{label}: {outcome.kind}; payload {'same' if same_payload else 'DIFFERENT'} as the first; trace {'same' if where is None else 'differs at ' + where}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
