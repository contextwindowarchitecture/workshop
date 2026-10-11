# W8 run sheet

Module: [08-assembler-kata/README.md](../../08-assembler-kata/README.md). A full day self-paced; six hours instructor-led; two hours as a conference cut (parts 1 and 2 with four defects). Needs the `assembler-python` sibling at its pin and uv; no model, no Node.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 15 | Framing | "Four assemblers exist; the goal is contributors." The pipeline on one slide. Build the kata on the projector and run `status`: ten-ish failures. |
| 15 to 45 | Part 1 | The stages and their modules, from DESIGN.md. The four exits. One case directory opened and read aloud. |
| 45 to 150 | Part 2, first half | Repairs. Insist on the failing test before the fix; walk the room and ask to see the red run. |
| 150 to 165 | Break | |
| 165 to 270 | Part 2, second half | The harder ones: string ordering (UTF-16), the margin rounding, and the two defects that share `admission-reasons`. |
| 270 to 315 | Lunch or long break | |
| 315 to 375 | Part 3 | `check`, the port's own suite, `status.json`, the listing. Then the uncovered defect, as the bridge to W10. |
| 375 to 390 | Close | Which of the four repositories each participant will open an issue in. |

## Pre-session checks

```sh
python3 shared/siblings.py                                   # assembler-python present
cd 08-assembler-kata && uv run pytest                        # the manifest matches the pin and every defect still breaks a case (about a minute)
python3 kata.py build && python3 kata.py status              # ten defects injected, 18 cases failing
```

The first `uv sync` inside `work/` fetches the assembler's dependencies; warm the cache offline.

## Checkpoint answers

- **Checkpoint 1.** snapshot.py; admission.py; conflicts.py; supersede.py; dedupe.py; diversity.py; fitting.py and model.py; render/; trace.py. Exits: assembled, refused, rejected, stopped on a published tokenizer or renderer id.
- **Checkpoint 2.** `kata.py reveal <case>` after each repair. The cases reached by two defects: `admission-reasons` (expiry boundary and the missing scope key). Expect the string-ordering defect to take longest: the failing case is `ordering-astral-ids`, and the fix is one encoding name.
- **Checkpoint 3.** The report test (`test_report.py`), the status test (`test_status.py`) and the conformance suite with its `PENDING` set. Any requirement row from `status.json`. For the uncovered defect: a fact group with two leaders from the top producer, different freshness, and `freshness_tiebreak` absent or false, whose expected trace is `escalated` and whose route says surface or refuse.

## Stumbles

- Participants fix by pattern-matching the expected trace without reading the requirement. Ask them which sentence of the spec their fix implements.
- Participants edit `.pristine/`. Rebuild with `kata.py build`; nothing of theirs is lost if they kept their tests outside, and that is the lesson about keeping notes.
- Participants fix two defects and see a case still failing. `kata.py hint` says when a case is reached by two.
- Bytecode after a same-length edit within the same second: the port's AGENTS.md warns about it; delete `__pycache__` when a correct fix seems not to take.
- `kata.py check` is the conformance gate only; the contributor's gate is the port's full `uv run pytest`, which also wants the regenerated report.
