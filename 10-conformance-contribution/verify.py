"""Lab A, second half: does a case catch the defect it was written for, and which of the eleven does it catch?

    uv run verify.py                                      # the worked example against its defect, tiebreak-without-permission
    uv run verify.py --case my-case --defect threshold-is-strict
    uv run verify.py --case my-case --all-defects         # every defect in W8's manifest and uncovered list: caught or not

A case earns its place by failing an implementation that is wrong. The reference assembler must pass it; a copy of the
reference with the chosen defect applied must fail it, and the first differing field says where. The defects are W8's:
08-assembler-kata/defects/manifest.json holds ten that published cases catch, uncovered.json the ones no published case
reached when the kata was built. Both runs are black-box: each copy is imported under another name from a scratch tree.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import cwa

HERE = Path(__file__).resolve().parent
DEFECTS = HERE.parent / "08-assembler-kata" / "defects"
IGNORED = ("trace_id", "timings")


def comparable(trace: dict) -> dict:
    return {k: v for k, v in trace.items() if k not in IGNORED}


def first_difference(actual, expected, path: str = "") -> str | None:
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


def defects() -> dict[str, dict]:
    """Every defect W8 knows, by id, with where it came from."""
    out = {}
    for name in ("manifest.json", "uncovered.json"):
        for d in json.loads((DEFECTS / name).read_text(encoding="utf-8"))["defects"]:
            out[d["id"]] = {**d, "listed_in": name}
    return out


_counter = [0]


def broken_assembler(defect: dict):
    """The installed assembler copied to a scratch package with one defect applied, imported under a name of its own."""
    _counter[0] += 1
    name = f"cwa_broken_{_counter[0]}"
    source = Path(cwa.__file__).resolve().parent
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(source, tmp / name, ignore=shutil.ignore_patterns("__pycache__"))
    target = tmp / name / Path(defect["file"]).relative_to("src/cwa")
    text = target.read_text(encoding="utf-8")
    if text.count(defect["find"]) != 1:
        raise RuntimeError(f"the installed assembler does not hold the line defect {defect['id']} changes; is the pin the kata's?")
    target.write_text(text.replace(defect["find"], defect["replace"]), encoding="utf-8")
    sys.path.insert(0, str(tmp))
    return importlib.import_module(name)


def run(module, document: dict):
    return module.assemble(module.Snapshot.from_json(document))


def load(case_id: str) -> tuple[dict, dict, Path | None]:
    case = HERE / "cases" / case_id
    document = json.loads((case / "snapshot.json").read_text(encoding="utf-8"))
    expected = json.loads((case / "expected.trace.json").read_text(encoding="utf-8"))
    payload = case / "expected.payload.txt"
    return document, expected, payload if payload.exists() else None


def judge(module, document: dict, expected: dict, payload_path: Path | None) -> str | None:
    """None when the implementation passes the case; else the first differing field (or the payload)."""
    result = run(module, document)
    where = first_difference(comparable(result.trace), comparable(expected))
    if where:
        return where
    if payload_path is None:
        return None if result.payload is None else "/payload (expected a refusal)"
    return None if result.payload == payload_path.read_bytes() else "/payload"


def outcome(module, document: dict) -> str:
    r = run(module, document)
    if r.trace["refused"]["bool"]:
        return f"refused {r.trace['refused']['reason']}"
    return f"assembled, {r.trace['result']['input_tokens']} tokens"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case", default="conflict-tiebreak-not-permitted")
    p.add_argument("--defect", default=None, help="a defect id from W8's manifest or uncovered list (default: the example's)")
    p.add_argument("--all-defects", action="store_true")
    args = p.parse_args(argv)
    document, expected, payload_path = load(args.case)
    known = defects()
    where = judge(cwa, document, expected, payload_path)
    print(f"reference assembler: {'passes' if where is None else 'FAILS at ' + where}  ({outcome(cwa, document)})")
    if where is not None:
        print("a case the reference fails is either wrong or a finding; read the trace before believing either")
        return 1
    chosen = [args.defect] if args.defect else (list(known) if args.all_defects else ["tiebreak-without-permission" if args.case == "conflict-tiebreak-not-permitted" else None])
    if chosen == [None]:
        print("name the defect your case is for: --defect <id>, or --all-defects. Known: " + ", ".join(known))
        return 2
    caught = 0
    for defect_id in chosen:
        if defect_id not in known:
            print(f"unknown defect {defect_id}; known: {', '.join(known)}")
            return 2
        broken = broken_assembler(known[defect_id])
        where_bad = judge(broken, document, expected, payload_path)
        caught += where_bad is not None
        print(f"{defect_id:<42} {known[defect_id]['listed_in']:<15} {'CAUGHT at ' + where_bad if where_bad else 'not caught'}  ({outcome(broken, document)})")
    if args.all_defects:
        print(f"\n{caught} of {len(chosen)} defects caught by {args.case}")
        return 0
    return 0 if caught == len(chosen) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
