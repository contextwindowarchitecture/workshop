"""Lab A, second half: does the new case catch the defect it was written for?

    uv run verify.py          # the case through the reference assembler (must pass) and through a copy with W8's uncovered defect (must fail)

A case earns its place by failing an implementation that is wrong. The reference passes it; a copy of the reference
with the tie-break applied without permission assembles where the case expects a refusal, and the first difference
says where. Both runs are black-box: the copy is imported under another name from a temporary directory.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import cwa

HERE = Path(__file__).resolve().parent
CASE = HERE / "cases" / "conflict-tiebreak-not-permitted"
UNCOVERED = HERE.parent / "08-assembler-kata" / "defects" / "uncovered.json"
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


def broken_assembler():
    """The installed assembler copied to a temporary package with the uncovered defect applied, imported as cwa_broken."""
    defect = json.loads(UNCOVERED.read_text(encoding="utf-8"))["defects"][0]
    source = Path(cwa.__file__).resolve().parent
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(source, tmp / "cwa_broken", ignore=shutil.ignore_patterns("__pycache__"))
    target = tmp / "cwa_broken" / Path(defect["file"]).relative_to("src/cwa")
    text = target.read_text(encoding="utf-8")
    assert text.count(defect["find"]) == 1, "the installed assembler does not hold the line the defect changes"
    target.write_text(text.replace(defect["find"], defect["replace"]), encoding="utf-8")
    sys.path.insert(0, str(tmp))
    return importlib.import_module("cwa_broken")


def run(module, document: dict):
    return module.assemble(module.Snapshot.from_json(document))


def main() -> int:
    document = json.loads((CASE / "snapshot.json").read_text(encoding="utf-8"))
    expected = json.loads((CASE / "expected.trace.json").read_text(encoding="utf-8"))
    good = run(cwa, document)
    where = first_difference(comparable(good.trace), comparable(expected))
    print(f"reference assembler: {'passes' if where is None and good.payload is None else 'FAILS at ' + str(where)}"
          + f" (refused {good.trace['refused']['reason']})" if good.trace["refused"]["bool"] else " (assembled!)")
    bad = run(broken_assembler(), document)
    where_bad = first_difference(comparable(bad.trace), comparable(expected))
    outcome = f"refused {bad.trace['refused']['reason']}" if bad.trace["refused"]["bool"] else f"assembled, {bad.trace['result']['input_tokens']} tokens, kb:window-1 {next((e['reason'] for e in bad.trace['excluded'] if e['item_id'] == 'kb:window-1'), 'kept')}"
    print(f"with the uncovered defect: {'passes (the case does not catch it)' if where_bad is None else 'FAILS at ' + where_bad}  ({outcome})")
    return 0 if where is None and where_bad is not None else 1


if __name__ == "__main__":
    sys.exit(main())
