# W10 run sheet

Module: [10-conformance-contribution/README.md](../../10-conformance-contribution/README.md). Half a day self-paced; three and a half hours instructor-led; 60 minutes as a conference cut (part 1 and part 2). Model-free. Lab B needs the `contextwindowarchitecture` sibling; without it, show `check.py`'s output from your own run and skip to Lab C.

The module does not depend on the published corpus having a gap. Participants pick one of W8's eleven defects and write the case that isolates it; the worked example happens to be the one defect that was uncovered when the module was written. If the corpus has since caught up, say so in the framing and point at Part 4: the comparison with the published case is part of the lesson.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "The specification is data; the prose is written from it." Show `requirements.json` and the generated markers in `SPEC.md`. |
| 10 to 40 | Part 1 | Open `conflict-fact` together. Walk `f-freshness`, `f-tie`, `f-precedence`. |
| 40 to 70 | Part 2 | `generate.py`, `verify.py`, `--all-defects`. Dwell on "catches 1 of 11": specific is the second thing a case must be. |
| 70 to 80 | Break | |
| 80 to 155 | Lab A | Each participant picks a defect from the manifest. Spread them: no two neighbours on the same one. The usual stall is a table that intends what the defect does instead of what the rule says; the reference failing is the tell. |
| 155 to 185 | Lab B | `spec_check.py --case`, the two deliberate breakages, then the manifest's `breaks` list: who is covered already, and how the published case compares. |
| 185 to 230 | Lab C | Read the three templates aloud. Everyone writes the `CHANGES.md` bullet or the case-problem sentence first; collect three and compare. Then the spec-change argument. |
| 230 to 240 | Close | Who is opening what, and where it goes (issue first when meaning changes). |

## Pre-session checks

```sh
cd 10-conformance-contribution && uv sync && uv run generate.py --check && uv run verify.py --all-defects && uv run pytest
CWA_SIBLINGS_ROOT=.. uv run spec_check.py      # ok (the counts move as the spec adds cases)
```

If `spec_check.py` says the spec already has a case named `conflict-tiebreak-not-permitted`, the corpus has caught up: run it with `--case` on a renamed copy (`uv run generate.py --id tiebreak-example`) and use the fact in the framing.

## Checkpoint answers

- **Checkpoint 1.** `f-tie` escalates and is surfaced: two leaders, same producer, same instant, no `freshness_tiebreak`. For the clock to decide it, the policy would need `freshness_tiebreak: true` and one leader strictly later. A refusal has no `expected.payload.txt`; R-17 says a refused assembly has no rendered payload.
- **Checkpoint 2.** `/conflicts/0/decided_by` (`freshness` where `escalated` was expected). The example catches 1 of 11.
- **Checkpoint 3.** Any defect from the manifest with a case that the reference passes, the defect fails, and at most two or three others trip. Good first picks: `threshold-is-strict` (one item at exactly `min_relevance`), `expired-is-exclusive` (a memory item expiring at the assembly instant), `history-renders-by-id` (two turns whose id order and time order disagree). Harder: `strings-order-by-utf8` (needs an id outside the Basic Multilingual Plane), `margin-rounds-down` (needs a budget at the rounding edge).
- **Checkpoint 4.** `ok` with the count one higher than the vendored corpus. The wrong digest is caught by "snapshot_digest does not match the normalized snapshot"; the stray payload by "refusal has an expected.payload.txt". For the ten manifest defects the `breaks` list names the published cases; the comparison usually finds the published case reaches the defect among several other decisions, and the participant's isolates it.
- **Checkpoint 5.** Any draft that names the gap or the comparison, says whether a rule changes, and lists what each listed assembler did.

## Stumbles

- Participants write the expected trace by running the reference and pasting. Ask them how that case could ever fail the reference.
- Participants pick a defect whose rule they have not read, then write a table that encodes the defect's behaviour. The reference fails their case; that is the signal to read the rule.
- Participants put `freshness_tiebreak: false` in the policy and expect a different outcome from leaving it out. The schema allows both; the rule reads the value, so they are the same case.
- Participants edit `SPEC.md` in the scratch copy. Show the generated markers and `check.py --write`.
- Two participants pick the same defect and compare cases: let them. Two cases for one defect that differ in what else they trip is the "specific" lesson taught twice.
