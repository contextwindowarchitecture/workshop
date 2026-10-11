# W4. Budgets, variants, routes and refusals

Half a day, self-paced, model-free. You leave able to design a route set with budgets, caps, floors and escalation and justify every number, able to explain to a product owner why the system refused rather than answered, and with a review habit for anything shorter that stands in for evidence.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` installs the reference assembler and the OpenAI SDK. Lab C needs `uv run --extra calibrate` for tiktoken, and the network once to fetch an encoding.
- W1. W3a helps: this is that application on two routes.
- Open [worksheet.md](worksheet.md) beside this file.

Conference cut (90 minutes): part 1, Lab A, Lab D.

## The model of fitting

Every slot sits in one of three tiers. **Protected** items render whole or the assembly refuses. **Droppable** items may be omitted. **Compressible** items may be replaced by a precomputed shorter variant or omitted, and only after droppable items are gone. Within that, the route's `fitting_order` says what shortens first; without one, variants come before omission. An item over its own `token_budget`, or a slot over the route's `max_tokens`, is reduced before any budget pressure. A slot with `min_tokens` is a floor nothing reduces below. Every omission is an `over_budget` row; every swap is a `compressed` row naming the variant (R-16, R-18).

Three refusals belong to fitting, and each is an outcome, not an error:

| Refusal | When | Recovery |
| --- | --- | --- |
| `protected_content_over_budget` | the protected items alone do not fit; nothing is reduced first | a bigger route, or less protected content |
| `slot_floor_over_budget` | the payload fits only by breaking a `min_tokens` floor | a bigger route, or a lower floor |
| `evidence_required` | a route that requires evidence has too little left after fitting | `request_context`, `precompute_summary` or `retrieve_narrower`, as the trace says (R-12) |

The count is the declared tokenizer's. `estimate-utf8/v1` is portable and wrong by a model-dependent factor, which `budget.margin_percent` covers: the payload fits when count times (100 plus margin) over 100, rounded up, is at most `budget.input`. An application may count with the model's own tokenizer under an id of its own, and never under a published id (R-16).

## Part 1. One application, two routes (20 minutes)

```sh
uv sync
uv run python -m app.app --conversation scenarios/01-export/conversation.json
uv run python -m app.app --conversation scenarios/03-pasted-log/conversation.json
```

The application in `app/` is W3a's, with [solution/routes.json](solution/routes.json): a small route on a 2048-token model that reserves 512 for the answer, and a large route on an 8192-token model that reserves 1024. `budget.input` is computed from those two numbers, never typed (R-16). Every request starts on the small route. The first conversation fits there. The second pastes a sixty-line worker log into the question; the query is protected, so the small route refuses `protected_content_over_budget` before reducing anything, and the escalate table sends the request to the large route, where a new snapshot is built and assembled (R-12, R-17). Two tables print, one per attempt.

**Checkpoint 1.** In the worksheet: each route's `budget.input` and how it was computed, and the two refusal codes that escalate.

## Lab A. Review the summaries before you commit them (50 minutes)

Under budget pressure, a compressible chunk is replaced by a shorter variant the producer attached before the request (R-18). Here the variants are summaries in [summaries/summaries.json](summaries/summaries.json), one per paragraph, keyed by the SHA-256 of the paragraph, standing in for a model run. Four of the thirty-six say something their paragraph does not.

```sh
uv run review.py                  # every paragraph beside its summary, with your decision
uv run review.py --only plans
```

Edit [labs/reviewed.json](labs/reviewed.json): move each unfaithful summary from `approved` to `rejected` with a one-line reason. The producer attaches a variant only for approved ids ([app/producers.py](app/producers.py), `variants_for`), so an unreviewed summary is a sentence written by one model that another model will read as evidence, and nobody checked.

```sh
CWA_W4_IMPL=labs uv run pytest tests/test_lab_a_review.py
uv run python -m app.app --impl labs --budget 500 --conversation scenarios/05-unreviewed/conversation.json
```

The second command is the point of the lab, run before you finish it: with everything approved and a tight budget, the roles paragraph is swapped for a summary that says admins can change billing. The paragraph says they cannot. The trace shows a faithful swap of a variant that was not. Scenario `05-unreviewed` commits that payload.

One more thing to notice: the exact FAQ copy and the data-export paragraph share a hash, so one summary covers both and approving either id approves the text. And in scenario `04-recovery`, the refusal's recovery action is `precompute_summary` rather than `retrieve_narrower` because one omitted evidence item had no variant, and it had none because its summary was rejected in review. The review decision changed the recovery action.

**Checkpoint 2.** The worksheet's Lab A lines: the four ids, their reasons, and what scenario 05's payload says that its paragraph does not.

## Lab B. Two routes and an escalation table (40 minutes)

Open [labs/routes.json](labs/routes.json). It has both routes and no escalate table. Decide which refusal reasons on the small route should rebuild the request on the large one, write the table, and defend the numbers:

```sh
CWA_W4_IMPL=labs uv run pytest tests/test_lab_b_routes.py
uv run python -m app.app --impl labs --conversation scenarios/03-pasted-log/conversation.json
uv run python -m app.app --impl labs --budget 400 --conversation scenarios/04-recovery/conversation.json
```

Then read the two route policies under [policy/](policy/). They differ only in the history cap. Change something and watch which scenario moves: lower `min_included`, add a `min_tokens` floor on knowledge and squeeze until `slot_floor_over_budget`, reorder `fitting_order` so knowledge is omitted before history is.

**Checkpoint 3.** The escalate table you wrote, one sentence per entry on why that reason and not others, and one route change you made with the scenario it moved.

## Lab C. Calibrate the margin (30 minutes)

```sh
uv run --extra calibrate calibrate.py
uv run --extra calibrate calibrate.py --stop-rule
```

The first counts every text the large route renders with `estimate-utf8/v1` and with tiktoken's `cl100k_base`, prints the worst ratio and recommends a margin. On this corpus the ratios run from 0.82 on the instructions to 1.005 on the account and article text, so the script recommends 6% and the 15% in the routes table is generous for this tokenizer. On code, logs or another language the estimate can undercount by far more, which is why the pasted-log conversation is worth running through the script with `--encoding o200k_base` too. The second shows the two rules for an application tokenizer: under its own id it works and the trace names it; under a published id the assembler stops before assembly, because a trace that says `estimate-utf8/v1` must mean that count (R-16).

**Checkpoint 4.** The worst ratio you measured, the margin you would set for this model, and why a tokenizer can never be passed under a published id.

## Lab D. The budget cases (30 minutes)

The specification ships conformance cases for exactly these rules, vendored under `shared/contract/cwa/conformance/cases/`. Predict each, run it, reveal it:

```sh
uv run cases.py list
uv run cases.py run budget-slot-floor
uv run cases.py reveal budget-slot-floor
```

Work through the `budget-*`, `protected-over-*` and `evidence-*` cases with the worksheet's predict table. The ones most people miss: `budget-margin-rounding`, `budget-tier-lowering-ignored`, `budget-slot-cap-before-pressure`, `evidence-precompute-summary` versus `evidence-retrieve-narrower`.

**Checkpoint 5.** The predict table filled; fifteen or more right of the twenty-five is the bar.

## After this workshop

- Replace one truncation heuristic in production with tiers and precomputed, reviewed variants.
- W5 adds tools to this application. W6 evaluates the profiles both routes still carry as `unevaluated`.

## Covers

R-12, R-16, R-17, R-18; R-23 through the per-attempt snapshots.

## Files

- `app/`: W3a's application on two routes; `routes.py` reads the table, `context.py` freezes per route, `app.py` escalates.
- `labs/`: your review list and routes table. `solution/`: the finished ones, which CI uses. `impl.py`: the `CWA_W4_IMPL` switch.
- `summaries/summaries.json`: the precomputed summaries, keyed by content hash. `summarize.py` regenerates them with a model when one is configured.
- `review.py`, `calibrate.py`, `cases.py`: the lab tools. `policy/`: the two route policies and profiles, and the instructions.
- `scenarios.py`, `scenarios/`, `tests/`: five conversations with every attempt committed, and the tests.
