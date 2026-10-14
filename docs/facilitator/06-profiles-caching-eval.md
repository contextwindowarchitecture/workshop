# W6 run sheet

Module: [06-profiles-caching-eval/README.md](../../06-profiles-caching-eval/README.md). Half a day self-paced; four hours instructor-led; 90 minutes as a conference cut (part 1 and Lab B). Model-free; the live part of Lab C is optional and needs an OpenAI-compatible endpoint.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 15 | Framing | "CWA takes no position on where items go." The six-step protocol on one slide. Show the Placement page's [evaluation protocol](https://contextwindowarchitecture.io/evidence.html#evaluate) once. |
| 15 to 35 | Part 1 | `profiles.py diff` on the projector: same items, three hashes. |
| 35 to 80 | Lab B | Reuse. Have them predict which profile reuses most before running `compare`. Then the cache-reuse test in `tests/test_reuse.py`, read aloud. |
| 80 to 95 | Break | |
| 95 to 155 | Lab C | Evaluate and promote. Stop at 140: what did the structural suite measure, and what can only a model settle? If an endpoint exists, one `--live` run on the projector. |
| 155 to 165 | Break | |
| 165 to 195 | Lab D | Lock, deploy, tamper, read the refusal. |
| 195 to 210 | Close | What their own route's profile says about evaluation today: almost always nothing. |

## Pre-session checks

```sh
cd 06-profiles-caching-eval && uv sync && uv run pytest && uv run scenarios.py --check
CWA_W6_IMPL=labs uv run pytest tests/test_lab_c_evaluation.py tests/test_lab_d_registry.py   # fail: nothing promoted, no lock yet
uv run evaluate.py compare
```

## Checkpoint answers

- **Checkpoint 1.** policy-first: instructions, account, articles, memory, history, query. evidence-first: instructions, articles, account, memory, history, query. cache-first: instructions, account, memory, history, articles, query. Same items, different hashes.
- **Checkpoint 2.** Block reuse about 0.26, 0.09 and 0.57. Under cache-first the shared blocks on export-then-roles are 5, 7, 9: everything before the articles is stable or append-only, and history renders in the order said (R-7). Under policy-first it is 3 every turn: the first article changes with the question. Evidence distance 87, 127 and 0 tokens.
- **Checkpoint 3.** cache-first v2, promoted from v1 because naming a model family is a new model target (R-20); the artifact is still `evaluations/cache-first-v1-w6-structural-v1.json`, the run that evaluated it; whatever model family they named. The live part adds the only thing that matters in the end: whether the answers are grounded and correct for that model with the articles that far from the instructions.
- **Checkpoint 4.** `deploy cache-first` returns it with its suite, date and artifact; `deploy policy-first` is refused as unevaluated (R-19). The tampered profile fails to load with a digest mismatch for that id and version (R-20).

## Stumbles

- Participants read block reuse as a quality score. It is a cost score; the evidence-distance column is the trade.
- Participants promote with no `--model-family` and get refused. Good; that is R-19 working.
- Participants edit `solution/` by mistake. Every tool takes `--impl labs`; say it at the start.
- The evaluation object's `result` is a string by schema; the numbers live in the artifact. `evaluate.py promote` does this; a hand-written evaluation object with a dict fails the lock.
- Byte reuse looks low next to block reuse because the serialized payload's key order puts the user blocks first and the system entry last; the provider-relevant number is the block count.
