# W11 run sheet

Module: [11-benchmarking/README.md](../../11-benchmarking/README.md). Half a day self-paced; three and a half hours instructor-led; 60 minutes as a conference cut (part 1, Lab A, and Lab C's two tables projected). Model-free. Labs B and C need the `examples` and `benchmark` siblings; the benchmark's committed Domain 2 run is large (its model cache is about half a gigabyte), so clone it before the session or project your own output.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "Two halves: what the assembler did, and what the model did with it. Never one number for both." |
| 10 to 40 | Part 1 | The three kinds of result on one slide. Read two entries of `meaning.py` aloud. |
| 40 to 70 | Lab A | `invariants.py`. Break a trace, watch the `recorded` column, restore it. |
| 70 to 80 | Break | |
| 80 to 140 | Lab B | `bench_read.py`, then `--measure grounding`. Ask the room to pick the model before they see the range column. |
| 140 to 200 | Lab C | `domain2_read.py` beside the published table. Spend ten minutes on the fact-in-payload column alone. |
| 200 to 210 | Break | |
| 210 to 240 | Lab D and close | Everyone writes one expectation. Collect three and ask the room what phrasing each would miss. |

## Pre-session checks

```sh
cd 11-benchmarking && uv sync && uv run invariants.py && uv run pytest
CWA_SIBLINGS_ROOT=.. uv run bench_read.py
CWA_SIBLINGS_ROOT=.. CWA_SIBLING_BENCHMARK=../cwa-extended/benchmark uv run domain2_read.py
```

## Checkpoint answers

- **Checkpoint 1.** An invariant: a bug in the example or the assembler, so fix it and rerun; never report it as a model result. A citation to an unsent article is a construct measure (`grounding`, `cites_what_it_was_sent`), the model's doing.
- **Checkpoint 2.** 164 snapshots at the time of writing, 0 failures. The expected rejection is W1's `12-two-batches` (producer ids in more than one batch). W10's case has no `trace.json` beside it (its expectation is `expected.trace.json`, which the walker does not read), so its `recorded` column is 0/0.
- **Checkpoint 3.** 5,460 of 5,460; $9.44 of $30.00. `claims` (15 to 29 of 30) and `evals` (19 to 58 of 60). Grounding examples: deepseek-v4.1-flash averages 0.996 with a worst repeat of 0.958; llama-3.1-8b averages 0.979 with a worst of 0.958. A gate run once sees one of the ten repeats, and would have passed or failed on which one it got.
- **Checkpoint 4.** `truncate-pinned`: the newest turns that fit with the system prompt kept, which is what a careful conventional application does. Pilot at 8,192: 0.995 against 0.843, a gap of 0.152; published: 0.972 against 0.824, a gap of 0.148. `cwa-state-x` cannot be said to beat it: published +0.009 with interval [−0.025, +0.040]; in the pilot 0.907 against 0.843 with overlapping intervals. `truncate-pinned` had the fact 92% of the time in the pilot (90% published), so a tenth of its probes were lost before the model saw them, and the rest of its errors are the model's.
- **Checkpoint 5.** Any expectation that names a trace row and a phrase for both respecting and ignoring it. The best ones name what the pattern misses.

## Stumbles

- Participants read the measures table before the invariants line. Make them say the invariants line first every time.
- Participants rank models by `conflict` or `excluded`. Those are at the ceiling; point them at `claims`, `evals` and the range column.
- Participants quote the pilot's numbers as the result. The pilot replays a cache at small sizes; the published table is from the recorded sizes. The finding is the same; the digits are not.
- Participants call `cwa-state`'s gain "CWA's". Press: the state was written by the application from what the user said. CWA's part is the protected place every budget keeps. `cwa-state-x` is what the same architecture gives an application whose state comes from the model.
- The `benchmark` sibling is not under the root on most machines. `CWA_SIBLING_BENCHMARK` names it.
