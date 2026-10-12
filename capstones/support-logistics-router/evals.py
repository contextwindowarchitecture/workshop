"""The gate's evaluation: run every case with its scripted draft (or live), grade from the record, and promote the
routes' profiles only when every case passes.

    uv run evals.py run --label scripted-01 [--impl skeleton]
    uv run evals.py run --live --label <model>
    uv run evals.py grade evals/results/<label> [--check]
    uv run evals.py promote evals/results/<label> --model-family <model> [--force-scripted]

A case is a conversation, a scripted draft, and expect.json: the route it must take, the stages it may end in, the
articles it must cite, whether the guards must pass or which must fail, whether it must escalate, and what the trace
must show. Grading reads the record, not the draft alone.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from cwa.registry import lock, profile_digest

import app
import common
import impl
import models
from common import Request

HERE = Path(__file__).resolve().parent
CASES = HERE / "evals" / "cases"
RESULTS = HERE / "evals" / "results"


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def case_names() -> list[str]:
    return sorted(p.parent.name for p in CASES.glob("*/conversation.json"))


def grade(expect: dict[str, Any], record: dict[str, Any]) -> list[Check]:
    checks = []
    if "route" in expect:
        checks.append(Check("route", record["route"] == expect["route"], f"took {record['route']}"))
    if "attempts" in expect:
        tiers = [a["tier"] for a in record["attempts"]]
        checks.append(Check("escalation", tiers == expect["attempts"], f"attempts {tiers}"))
    if "first_refusal" in expect:
        first = record["attempts"][0]["trace"]["refused"]["reason"]
        checks.append(Check("first_refusal", first == expect["first_refusal"], f"first attempt refused {first}"))
    final = record["attempts"][-1]["trace"]
    if "trace" in expect:
        rows = {}
        for r in final["excluded"]:
            rows.setdefault(r["reason"], []).append(r["item_id"])
        for reason, want in expect["trace"].items():
            got = rows.get(reason, [])
            ok = (bool(got) if want is True else all(i in got for i in want))
            checks.append(Check(f"trace:{reason}", ok, f"{reason}: {got}"))
    guards_ok = all(g["ok"] for g in record["guards"])
    if "guards_pass" in expect:
        checks.append(Check("guards", guards_ok == expect["guards_pass"], f"guards {[g['name'] + (':ok' if g['ok'] else ':FAILED') for g in record['guards']]}"))
    if "failing_guard" in expect:
        failed = [g["name"] for g in record["guards"] if not g["ok"]]
        checks.append(Check("failing_guard", expect["failing_guard"] in failed, f"failed {failed}"))
    if expect.get("reply_is_fallback"):
        checks.append(Check("reply_is_fallback", record["reply"] == app.FALLBACK, "the draft was withheld" if record["reply"] == app.FALLBACK else "the draft went out"))
    if "next_stage_in" in expect:
        checks.append(Check("next_stage", record["next_stage"] in expect["next_stage_in"], f"stage {record['next_stage']}"))
    if "must_cite_any" in expect and record.get("parsed"):
        cited = set(record["parsed"]["citations"])
        checks.append(Check("must_cite_any", bool(cited & set(expect["must_cite_any"])), f"cited {sorted(cited)}"))
    return checks


def run_case(name: str, live: bool, which: str | None) -> dict[str, Any]:
    request = Request.load(CASES / name / "conversation.json")
    drafter: Any = models.LiveDrafter(common.budget("large")["reserved_output"]) if live else models.ScriptedDrafter(json.loads((CASES / name / "draft.json").read_text(encoding="utf-8")), f"scripted:{name}")
    return app.run(request, drafter, which, out=io.StringIO())


def run_suite(label: str, live: bool, which: str | None) -> Path:
    out = RESULTS / label
    out.mkdir(parents=True, exist_ok=True)
    model_name = "scripted"
    skipped = []
    for name in case_names():
        if live and json.loads((CASES / name / "expect.json").read_text(encoding="utf-8")).get("scripted_only"):
            skipped.append(name)  # the case scripts a bad draft to test a guard; a live model is not asked to misbehave
            continue
        record = run_case(name, live, which)
        model_name = record["model"] if live else "scripted"
        (out / f"{name}.run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    profiles = {route: json.loads((common.POLICY / route / "profile.json").read_text(encoding="utf-8")) for route in ("returns", "damaged", "general")}
    meta = {"suite": "c2-support-router/v1", "model": model_name, "live": live, "date": date.today().isoformat(), "impl": impl.name(which),
            "profiles": {r: {"id": p["id"], "version": p["version"], "sha256": profile_digest(p)} for r, p in profiles.items()},
            "cases": [n for n in case_names() if n not in skipped], "scripted_only": skipped}
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    report(out, write=True)
    return out


def report(results: Path, write: bool = False) -> dict[str, Any]:
    meta = json.loads((results / "meta.json").read_text(encoding="utf-8"))
    graded = []
    for name in meta["cases"]:
        record = json.loads((results / f"{name}.run.json").read_text(encoding="utf-8"))
        expect = json.loads((CASES / name / "expect.json").read_text(encoding="utf-8"))
        checks = grade(expect, record)
        graded.append({"id": name, "passed": all(c.passed for c in checks), "checks": [asdict(c) for c in checks], "reply": record["reply"]})
    skipped = meta.get("scripted_only", [])
    out = {**meta, "result": f"{sum(1 for g in graded if g['passed'])}/{len(graded)} cases passed" + (f" ({len(skipped)} scripted-only case(s) not run live)" if skipped else ""), "cases": graded}
    if write:
        (results / "report.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def promote(results: Path, model_family: str, force_scripted: bool = False) -> list[str]:
    graded = report(results)
    problems = []
    failed = [c["id"] for c in graded["cases"] if not c["passed"]]
    if failed:
        problems.append(f"{graded['result']}; failing: {', '.join(failed)}")
    if not graded["live"] and not force_scripted:
        problems.append("the results come from scripted drafts; a profile is evaluated for a model only by a live run (R-19)")
    profiles = {route: json.loads((common.POLICY / route / "profile.json").read_text(encoding="utf-8")) for route in graded["profiles"]}
    for route, pinned in graded["profiles"].items():
        if pinned["sha256"] != profile_digest(profiles[route]):
            problems.append(f"the results are for another version of the {route} profile; run the suite again")
    if problems:
        return problems
    for route, profile in profiles.items():
        profile["model_family"] = model_family
        profile["evaluation"] = {"status": "evaluated", "suite": graded["suite"], "date": graded["date"],
                                 "result": graded["result"] + ("" if graded["live"] else " (scripted drafts; not a live evaluation)"),
                                 "artifact": str((results / "report.json").relative_to(HERE))}
        (common.POLICY / route / "profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    policies = [common.policy(r, "route-policy.json") for r in profiles]
    (common.POLICY / "registry.lock.json").write_text(json.dumps(lock(list(profiles.values()), policies), indent=2) + "\n", encoding="utf-8")
    return []


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run"); r.add_argument("--label", required=True); r.add_argument("--live", action="store_true"); r.add_argument("--impl", choices=["skeleton", "solution"])
    g = sub.add_parser("grade"); g.add_argument("results"); g.add_argument("--check", action="store_true")
    pr = sub.add_parser("promote"); pr.add_argument("results"); pr.add_argument("--model-family", required=True); pr.add_argument("--force-scripted", action="store_true")
    args = p.parse_args(argv)
    if args.command == "run":
        if args.live and not models.configured():
            print("--live needs OPENAI_BASE_URL", file=sys.stderr)
            return 2
        try:
            out = run_suite(args.label, args.live, args.impl)
        except NotImplementedError as todo:
            print(f"not written yet: {todo}")
            return 2
        rep = json.loads((out / "report.json").read_text(encoding="utf-8"))
        print(f"{rep['result']}  ({out.relative_to(HERE)})")
        for c in rep["cases"]:
            print(f"  {'pass' if c['passed'] else 'FAIL'}  {c['id']}" + "".join(f"\n          {k['name']}: FAILED {k['detail']}" for k in c["checks"] if not k["passed"]))
        return 0
    if args.command == "grade":
        results = Path(args.results)
        rep = report(results)
        if args.check:
            same = json.loads((results / "report.json").read_text(encoding="utf-8")) == rep
            print("report matches" if same else "report differs")
            return 0 if same else 1
        (results / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(rep["result"])
        return 0
    problems = promote(Path(args.results), args.model_family, args.force_scripted)
    if problems:
        print("not promoted:\n  " + "\n  ".join(problems))
        return 1
    print("promoted: the three route profiles are evaluated and policy/registry.lock.json pins them")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
