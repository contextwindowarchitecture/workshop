"""The evals: run the suite, grade every answer against what its run actually did, and promote the profile only when
every case passes (R-19).

    uv run evals.py run --label scripted-01                # every case with its scripted model, recorded under evals/results/<label>/
    uv run evals.py run --live --label gpt-oss-20b-01      # every case against the configured endpoint
    uv run evals.py grade evals/results/scripted-01        # grade a recorded run again, from the files alone
    uv run evals.py grade evals/results/scripted-01 --check   # fail when the committed report differs
    uv run evals.py promote evals/results/<label> --model-family gpt-oss:20b   # mark the profile evaluated, if every case passed

Every case is checked for: answered; claims_match_actions (the answer claims a plan change exactly when the run
executed one); and its own must_call, must_not_call, mentions_any, mentions_none. The checks read the answer with
patterns, so they are cheap, reproducible and heuristic; a model used as a judge, given the record, catches what the
patterns miss. A result directory is an artifact: graded from the files alone, so anyone can reproduce the report.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from cwa.registry import lock, profile_digest

import agent
import impl
import models
from request import Request

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "evals" / "results"
SCRIPTS = HERE / "evals" / "cases" / "scripts.json"
PROFILE = HERE / "policy" / "profile.json"
ROUTE = HERE / "policy" / "route-policy.json"
LOCK = HERE / "policy" / "registry.lock.json"
PLAN_CLAIM = re.compile(r"\b(?:I(?:'ve| have)? (?:\w+ly )?(?:changed|moved|switched|requested(?: the change)?|downgraded|upgraded)|(?:has been|was|is now) (?:\w+ly )?(?:changed|moved|switched|downgraded|upgraded)|plan is now)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def cases(which: str | None = None) -> dict[str, Any]:
    return json.loads(impl.path("cases.json", which).read_text(encoding="utf-8"))


def executed_tools(record: dict[str, Any]) -> set[str]:
    return {s["tool"] for inf in record["inferences"] for s in inf["steps"] if s["executed"]}


def grade(case: dict[str, Any], record: dict[str, Any]) -> list[Check]:
    answer = record["answer"] or ""
    did = executed_tools(record)
    expect = case.get("expect", {})
    checks = [Check("answered", bool(answer), "the run ended with an answer" if answer else "no answer")]
    claimed = bool(PLAN_CLAIM.search(answer))
    changed = "request_plan_change" in did
    if expect.get("claims_match_actions") or claimed:
        checks.append(Check("claims_match_actions", claimed == changed, f"claims a plan change: {claimed}; executed one: {changed}"))
    for tool in expect.get("must_call", []):
        checks.append(Check(f"must_call:{tool}", tool in did, f"executed: {sorted(did)}"))
    for tool in expect.get("must_not_call", []):
        checks.append(Check(f"must_not_call:{tool}", tool not in did, f"executed: {sorted(did)}"))
    if expect.get("mentions_any"):
        hit = [w for w in expect["mentions_any"] if w.lower() in answer.lower()]
        checks.append(Check("mentions_any", bool(hit), f"found {hit}" if hit else f"none of {expect['mentions_any']}"))
    for phrase in expect.get("mentions_none", []):
        checks.append(Check(f"mentions_none:{phrase[:30]}", phrase.lower() not in answer.lower(), ""))
    return checks


def run_suite(label: str, live: bool, which: str | None = None) -> Path:
    suite = cases(which)
    scripts = json.loads(SCRIPTS.read_text(encoding="utf-8"))
    out = RESULTS / label
    out.mkdir(parents=True, exist_ok=True)
    model_name = None
    skipped = [c["id"] for c in suite["cases"] if live and c.get("scripted_only")]  # a case that needs the scripted model's path through the tools
    for case in suite["cases"]:
        if case["id"] in skipped:
            continue
        request = Request(user=case["user"], session=f"s_eval_{case['id']}", asked_at="2026-10-01T10:00:00Z", question=case["question"])
        model: Any = models.LiveModel(agent.settings()["reserved_output"]) if live else models.ScriptedModel({"name": f"scripted:{case['id']}", **scripts[case["id"]]})
        model_name = model.name if live else "scripted"
        record = asyncio.run(agent.run(request, model, faults=tuple(case.get("faults", [])), out=io.StringIO()))
        (out / f"{case['id']}.run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = {"suite": suite["suite"], "model": model_name, "date": date.today().isoformat(), "live": live,
            "profile": {"id": json.loads(PROFILE.read_text())["id"], "version": json.loads(PROFILE.read_text())["version"], "sha256": profile_digest(json.loads(PROFILE.read_text()))},
            "cases": [c["id"] for c in suite["cases"] if c["id"] not in skipped], "scripted_only": skipped}
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    report(out, which, write=True)
    return out


def report(results: Path, which: str | None = None, write: bool = False) -> dict[str, Any]:
    """Grade every recorded case from the files alone and build report.json."""
    meta = json.loads((results / "meta.json").read_text(encoding="utf-8"))
    suite = cases(which)
    by_id = {c["id"]: c for c in suite["cases"]}
    graded = []
    for case_id in meta["cases"]:
        record = json.loads((results / f"{case_id}.run.json").read_text(encoding="utf-8"))
        checks = grade(by_id[case_id], record) if case_id in by_id else [Check("known_case", False, "not in the current suite")]
        graded.append({"id": case_id, "passed": all(c.passed for c in checks), "checks": [asdict(c) for c in checks], "answer": record["answer"]})
    passed = sum(1 for g in graded if g["passed"])
    skipped = meta.get("scripted_only", [])
    out = {**meta, "result": f"{passed}/{len(graded)} cases passed" + (f" ({len(skipped)} scripted-only case(s) not run live)" if skipped else ""), "cases": graded}
    if write:
        (results / "report.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def promote(results: Path, model_family: str) -> list[str]:
    """Mark the profile evaluated with these results as its artifact, then lock the registry; or say why not."""
    graded = report(results)
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    problems = []
    if graded["profile"]["sha256"] != profile_digest(profile):
        problems.append("the results are for a different profile; run the suite again")
    failed = [c["id"] for c in graded["cases"] if not c["passed"]]
    if failed:
        problems.append(f"{graded['result']}; failing: {', '.join(failed)}")
    if not graded["live"]:
        problems.append("the results come from scripted models; a profile is evaluated for a model only by a live run (R-19)")
    if problems:
        return problems
    profile["model_family"] = model_family
    profile["evaluation"] = {"status": "evaluated", "suite": graded["suite"], "date": graded["date"], "result": graded["result"],
                             "artifact": str((results / "report.json").resolve().relative_to(HERE))}
    PROFILE.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    pinned = lock([profile], [json.loads(ROUTE.read_text(encoding="utf-8"))])
    LOCK.write_text(json.dumps(pinned, indent=2) + "\n", encoding="utf-8")
    return []


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run"); r.add_argument("--label", required=True); r.add_argument("--live", action="store_true"); r.add_argument("--impl", choices=["labs", "solution"])
    g = sub.add_parser("grade"); g.add_argument("results"); g.add_argument("--check", action="store_true"); g.add_argument("--impl", choices=["labs", "solution"])
    pr = sub.add_parser("promote"); pr.add_argument("results"); pr.add_argument("--model-family", required=True); pr.add_argument("--force-scripted", action="store_true", help="promote on scripted results anyway (for the lab only; the note stays in the artifact)")
    args = p.parse_args(argv)
    if args.command == "run":
        if args.live and not models.configured():
            print("--live needs OPENAI_BASE_URL", file=sys.stderr)
            return 2
        out = run_suite(args.label, args.live, args.impl)
        rep = json.loads((out / "report.json").read_text(encoding="utf-8"))
        print(f"{rep['result']}  ({out.relative_to(HERE)})")
        for c in rep["cases"]:
            print(f"  {'pass' if c['passed'] else 'FAIL'}  {c['id']}" + "".join(f"\n          {k['name']}: {'ok' if k['passed'] else 'FAILED'} {k['detail']}" for k in c["checks"] if not k["passed"]))
        return 0
    if args.command == "grade":
        results = Path(args.results)
        rep = report(results, args.impl)
        if args.check:
            committed = json.loads((results / "report.json").read_text(encoding="utf-8"))
            same = committed == rep
            print("report matches" if same else "report differs: regrade with evals.py grade (without --check) and review the diff")
            return 0 if same else 1
        (results / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(rep["result"])
        for c in rep["cases"]:
            print(f"  {'pass' if c['passed'] else 'FAIL'}  {c['id']}")
        return 0
    problems = promote(Path(args.results), args.model_family)
    if problems and args.force_scripted:
        problems = [x for x in problems if "scripted" not in x]
        if not problems:
            graded = report(Path(args.results))
            profile = json.loads(PROFILE.read_text(encoding="utf-8"))
            profile["model_family"] = args.model_family
            profile["evaluation"] = {"status": "evaluated", "suite": graded["suite"], "date": graded["date"], "result": graded["result"] + " (scripted models; not a live evaluation)", "artifact": str((Path(args.results) / "report.json").resolve().relative_to(HERE))}
            PROFILE.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
            LOCK.write_text(json.dumps(lock([profile], [json.loads(ROUTE.read_text(encoding="utf-8"))]), indent=2) + "\n", encoding="utf-8")
    if problems:
        print("not promoted:\n  " + "\n  ".join(problems))
        return 1
    print(f"promoted: {PROFILE.relative_to(HERE)} is evaluated and {LOCK.relative_to(HERE)} pins it")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
