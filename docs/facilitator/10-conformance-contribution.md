# W10 run sheet

Module: [10-conformance-contribution/README.md](../../10-conformance-contribution/README.md). Half a day self-paced; three and a half hours instructor-led; 60 minutes as a conference cut (part 1 and Lab A through `verify.py`). Model-free. Lab B needs the `contextwindowarchitecture` sibling; without it, show `check.py`'s output from your own run and skip to Lab C.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "The specification is data; the prose is written from it." Show `requirements.json` and the generated markers in `SPEC.md`. |
| 10 to 40 | Part 1 | Open `conflict-fact` together. Walk `f-freshness`, `f-tie`, `f-precedence`. Ask what the corpus does not have before you say it. |
| 40 to 130 | Lab A | `generate.py`, `verify.py`, the three variations. The second variation (same instant) is the moment: the case stops isolating the defect. |
| 130 to 140 | Break | |
| 140 to 185 | Lab B | `spec_check.py`, then the two deliberate breakages in the scratch copy. |
| 185 to 230 | Lab C | Read the three templates aloud. Everyone writes the `CHANGES.md` bullet first; collect three and compare. Then the spec-change argument. |
| 230 to 240 | Close | Who is opening what, and where it goes (issue first when meaning changes). |

## Pre-session checks

```sh
cd 10-conformance-contribution && uv sync && uv run generate.py --check && uv run verify.py && uv run pytest
CWA_SIBLINGS_ROOT=.. uv run spec_check.py      # 66 cases, 25 rejections, ok (counts move as the spec adds cases)
```

## Checkpoint answers

- **Checkpoint 1.** `f-tie` escalates and is surfaced: two leaders, same producer, same instant, no `freshness_tiebreak`. For the clock to decide it, the policy would need `freshness_tiebreak: true` and one leader strictly later. A refusal has no `expected.payload.txt`; R-17 says a refused assembly has no rendered payload.
- **Checkpoint 2.** `/conflicts/0/decided_by` (`freshness` where `escalated` was expected). With the defect the group resolves, `kb:window-1` is `conflict_lost`, and assembly goes ahead at 33 tokens. `f-tie` never caught it because its leaders share an instant, so the defective branch finds no strictly newest leader and escalates anyway. Variation 2: passes (the case no longer isolates). Variation 3: `resolution: surfaced`, assembled with both members marked; it still catches the defect, at the same field, but now the payload differs too.
- **Checkpoint 3.** `66 cases, 25 rejections, 26 requirements, 35 reason codes` then `ok` at the pin this module was built against. The wrong digest is caught by "snapshot_digest does not match the normalized snapshot"; the stray payload by "refusal has an expected.payload.txt". The table goes into `conformance/generators/conflicts.py`.
- **Checkpoint 4.** Any draft that names the gap, says no rule changes, and lists what each listed assembler did. Common first proposals from this repository: `evaluation.result` as an object (the worked example), `recovery.detail` structure, a reason code for a producer that reports no `excluded` list at all.

## Stumbles

- Participants write the expected trace by running the reference and pasting. Ask them how that case could ever fail the reference.
- Participants put `freshness_tiebreak: false` in the policy and expect a different outcome from leaving it out. The schema allows both; the rule reads the value, so they are the same case. Good moment for the "schema allows, rule decides" distinction.
- Participants edit `SPEC.md` in the scratch copy. Show the generated markers and `check.py --write`.
- `spec_check.py` with an old sibling checkout prints a different count. The count is not the point; `ok` is.
