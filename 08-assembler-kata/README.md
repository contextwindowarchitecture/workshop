# W8. Inside the assembler: the repair kata

A full day, self-paced, model-free. You leave able to read a conformance report and the normative order of reason codes and know exactly which stage is wrong, having changed the reference assembler under its own test discipline, and ready to open a real pull request against one of the four implementations.

## Before you start

- Python 3.11 or later and [uv](https://docs.astral.sh/uv/). The `assembler-python` sibling must be checked out at its pinned release; `python3 ../shared/siblings.py` says whether it is.
- W1. W2 helps for the vocabulary of admission.
- Open [worksheet.md](worksheet.md) beside this file.

Conference cut (two hours): parts 1 and 2 with the first four defects.

## The form

Four assemblers exist, in Python, TypeScript, Go and Rust, and all pass the published cases. The goal of this module is not a fifth; it is contributors to the four. So the kata is a repair: a copy of the Python reference with ten one-line defects injected, each in a different stage, each breaking at least one published conformance case. You find each by reading the case and the normative text, fix it, and prove the fix with the report. Nothing here is a toy: the copy is the real assembler, the cases are the real cases, and the discipline is the port's own `AGENTS.md`.

```sh
python3 kata.py build        # copy the sibling at its pin into work/, inject, install
python3 kata.py status       # 65 cases, 25 rejections, and which fail
```

`work/` is ignored by git and rebuilt from the sibling checkout, so the assembler's source is never duplicated in this repository and the kata survives re-vendoring. `.pristine/` is the unmodified copy, for `kata.py diff`.

## Part 1. The pipeline and the four exits (30 minutes)

Read the port's `docs/DESIGN.md` far enough to name the stages in order and the modules that hold them: validate and snapshot checks (`snapshot.py`), admit (`admission.py`), conflicts (`conflicts.py`), supersede, dedupe, diversity (their own modules), refusals and fitting (`fitting.py`, `model.py`), render (`render/`), trace (`trace.py`). Then the four exits: assembled, refused, rejected, stopped on a published-id override. Then the shape of a case: `snapshot.json` in, `expected.payload.txt` and `expected.trace.json` out, and the pass rule, byte for byte and field for field.

**Checkpoint 1.** The worksheet's stage table, module per stage.

## Part 2. Ten repairs (four to five hours)

```sh
python3 kata.py status
```

Each failing case names its rules and describes what it checks. Work one case at a time:

1. Read the case directory under `work/conformance/cases/<id>/`: the snapshot, the expected trace, the expected payload. Run it alone: `cd work && uv run pytest tests/test_conformance.py -k <id>`.
2. Read the requirement the case cites in `work/conformance/README.md` and `SPEC.md`. The README is normative where the spec leaves an algorithm open.
3. Locate the stage. `python3 kata.py hint <id>` names it when you are stuck; it never names the line.
4. Write the smallest test that states the behaviour and fails, in the port's own style under `work/tests/`. Then fix, then run the full suite. That is the port's red, green, refactor, and it is not optional here: a contributor who cannot show the failing test does not get the merge.
5. `python3 kata.py status` again. Some cases are reached by two defects and pass only when both are fixed; the hint says so.
6. Only after the case passes, `python3 kata.py reveal <id>` to compare your fix with the line that was changed.

The ten, by stage: tokenizer, deduplication, supersession, source diversity, render order, string ordering, fitting's margin, and three in admission. Two share a case.

**Checkpoint 2.** The worksheet's repair log: case, stage, the test you wrote, the line you changed. Ten rows.

## Part 3. The contributor's finish (60 minutes)

```sh
python3 kata.py check
cd work && uv run python -m cwa.conformance > conformance-report.json && uv run pytest
```

A clean report is not the end. The port's own suite has a test that fails while the committed report is stale, a test that rejects a `status.json` claim for a requirement whose cases fail, and a `PENDING` set that only shrinks. Read `work/AGENTS.md` in full now that you have worked under it, then `status.json`: which requirements are claimed `implemented`, which `boundary-checked`, and what evidence each cites. Read the specification repository's `implementations/python.json` to see what a listing claims and does not.

Then the thing the kata found that no case covers. Open [defects/uncovered.json](defects/uncovered.json): a one-line change to the conflict tie-break that every published case still passes. That is a gap in the suite, not in the assembler, and it is where W10 starts.

**Checkpoint 3.** The worksheet's last section: the three tests that gate a contribution, what `status.json` claims for one requirement you touched, and the case you would write for the uncovered defect.

## After this workshop

- Pick an open issue in one of the four assembler repositories and work it the way you worked the kata.
- W10 writes the missing case in the specification repository's generators and runs all four assemblers against it.
- File a case-problem issue for any published case whose expectation you can show is wrong.

## Covers

Every assembler-scope requirement through the cases; R-2, R-7, R-9, R-13, R-16, R-21, R-22, R-24, R-25, R-26 directly.

## Files

- `kata.py`: build, status, hint, reveal, check, diff, and the authors' verify-manifest.
- `defects/manifest.json`: the ten defects, each with the stage, the rules, the wrong line, the right line, why, and the cases it breaks. `defects/uncovered.json`: the eleventh, which no case reaches.
- `tests/`: the manifest matches the sibling at its pin and every defect still breaks a case.
- `work/`, `.pristine/`: built, ignored.
