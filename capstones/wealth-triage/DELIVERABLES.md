# Deliverables and the gate

Work in `skeleton/`. The orchestrator `app.py`, the evals `evals.py`, the cache measure `cache.py`, the data and the policy files are given; your team writes four modules against the contracts in their docstrings.

| # | Deliverable | Where | Gate |
| --- | --- | --- | --- |
| 1 | Route selector | `skeleton/intent.py` | `test_intent_selects_the_route_before_assembly` |
| 2 | Eight producers, two with facts, one the risk screen, one the capability policy | `skeleton/producers.py` | the producer tests, the conflict test, the risk and capability tests |
| 3 | The freeze with conflict groups and the grant | `skeleton/context.py` | every test that runs a case, and the cache test |
| 4 | Six screens | `skeleton/guards.py` | the guard tests, cases 02, 03 and 05 |
| 5 | A reviewed placement or route policy change | `policy/<route>/profile.json` or `route-policy.json` (version bump) | `cache.py` before and after, and your what-if note in the README's closing section |
| 6 | Two more gate cases | `evals/cases/<name>/{conversation,draft,expect}.json` | `test_every_case_passes_its_expectations` |
| 7 | A recorded suite, graded | `evals/results/<label>/` | `evals.py run --impl skeleton --label <team>` |
| 8 | Promotion and lock | `policy/*/profile.json`, `policy/registry.lock.json` | `evals.py promote ... --force-scripted`, then a live run if a model is available |

Run the gate:

```sh
CWA_C3_IMPL=skeleton uv run pytest
CWA_C3_IMPL=skeleton uv run cache.py
uv run evals.py run --impl skeleton --label team-a
uv run evals.py promote evals/results/team-a --model-family <model> --force-scripted
```

Definition of done: the gate is green against `skeleton/`, the suite report says every case passed, both route profiles are evaluated with the report as artifact, each at the next version because promotion names a model family (R-20), and `policy/registry.lock.json` pins them. If a model is available, the live suite replaces the scripted one before promotion.
