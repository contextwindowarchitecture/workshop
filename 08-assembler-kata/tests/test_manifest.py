"""The kata builds against the sibling at its pin, and every injected defect still breaks a published case.

The second test injects each defect alone into a scratch copy and runs the conformance suite; it needs the sibling,
uv and a minute. Both are skipped when the sibling is not checked out.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "shared"))
import kata  # noqa: E402
from siblings import sibling  # noqa: E402

SRC = sibling("assembler-python")
needs_sibling = pytest.mark.skipif(not SRC.is_dir(), reason="assembler-python is not checked out beside this repository")


def test_the_manifest_is_well_formed():
    data = kata.manifest()
    ids = [d["id"] for d in data["defects"]]
    assert len(ids) == 10 and len(set(ids)) == 10
    for d in data["defects"]:
        assert d["find"] != d["replace"] and d["stage"] and d["rules"] and d["why"] and d["breaks"], d["id"]
    stages = {d["stage"] for d in data["defects"]}
    assert {"tokenizer", "deduplication", "supersession", "source diversity", "render", "string ordering", "fitting", "admission"} <= stages


@needs_sibling
def test_every_target_line_exists_exactly_once_in_the_sibling():
    for d in kata.manifest()["defects"]:
        text = (SRC / d["file"]).read_text(encoding="utf-8")
        assert text.count(d["find"]) == 1, f"{d['id']}: {d['file']} at this pin does not hold the target line once"


@needs_sibling
def test_each_defect_alone_breaks_the_cases_the_manifest_says(tmp_path):
    scratch = tmp_path / "scratch"
    kata.copy_tree(SRC, scratch)
    subprocess.run(["uv", "sync", "--quiet"], cwd=scratch, check=True)
    assert kata.failing(kata.conformance(scratch)) == ([], []), "the pristine assembler must pass"
    for d in kata.manifest()["defects"]:
        path = scratch / d["file"]
        original = path.read_text(encoding="utf-8")
        kata.inject(scratch, d)
        for cache in scratch.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
        cases, _ = kata.failing(kata.conformance(scratch))
        path.write_text(original, encoding="utf-8")
        assert sorted(cases) == d["breaks"], d["id"]
