# Capstone C3. Wealth management and triage

One day, in teams of three or four. Everything you did in W2 to W7, applied to a regulated setting with money on the line, where the client can ask for a trade and the system must decide, before any model runs, whether that is even on the table. An acceptance gate instead of a worksheet. Every client, holding and article here is fictional teaching material.

## The brief

Larkbridge Wealth wants its portal assistant rebuilt on CWA. Clients ask about their holdings and charges, ask for orders, and report problems. The assistant must report positions from the custodian ledger, the system of record, even when the market-data vendor says otherwise; queue an order only when the client's mandate and the session's risk screen allow it, and never for more than the ledger holds; triage a fraud report at an urgency the risk screen sets a floor for; keep account identifiers out of every reply; place the stable parts of each request first so the provider's cache can reuse them turn to turn; and leave money movement to people.

[BLUEPRINT.md](BLUEPRINT.md) is the design in the specification's terms, including what changed from the original sketch and why. [DELIVERABLES.md](DELIVERABLES.md) is the list of what your team hands in and the test that checks each item.

## What is given

- `data/`: two clients (advisory and self-directed), the custodian ledger, the vendor's quotes and position estimates, four portal tools, five articles and the intent rules. The vendor shows 1,200 ACME units where the ledger has 1,000 settled.
- `policy/`: two routes (`portfolio`, `triage`), each a route policy, a cache-first profile, instructions and a strict contract; the capability policy with grants by mandate and risk; a routes table with a small and a large tier.
- `app.py`: the orchestrator. It selects the route, freezes a snapshot per attempt, escalates on a protected-content refusal, hands the payload to the drafter unchanged, parses the route's contract, reads the risk level back from the trace, runs the screens, queues actions for confirmation only when they pass, and writes the outcome. It never assembles.
- `cache.py`: the cache measure over a frozen four-turn conversation, under the committed profile and a history-first alternative.
- `evals.py`, `evals/cases/`: six gate cases with scripted drafts and expectations, and the runner that records, grades and promotes.
- `solution/`: a reference. Facilitators have it; teams get it at the end of the day.

## What you build

Four modules in `skeleton/`, each with its contract in its docstring: the route selector; the eight producers, among them the risk screen as state and the capability policy; the freeze with conflict groups and the grant; and the six screens. Then two gate cases of your own, a reviewed placement or policy change with the cache measure as evidence, a recorded suite, and the promotion.

```sh
uv sync
uv run app.py --conversation evals/cases/01-holdings-question/conversation.json --draft evals/cases/01-holdings-question/draft.json
uv run cache.py
CWA_C3_IMPL=skeleton uv run pytest
```

## The six cases

| Case | What happens | What to look at |
| --- | --- | --- |
| 01-holdings-question | The ledger's 1,000 units are reported; the vendor's 1,200 lose the fact group | `conflict_lost` on the vendor estimate; `place_trade` withheld on an advisory account |
| 02-vendor-figure-in-answer | The scripted draft reports 1,200 | `figures_match_ledger` withholds it: the application holds figures to the ledger |
| 03-advisory-sell-request | A sell on an advisory account; the draft queues an order anyway | `cap:place_trade` is `capability_not_allowed` at the producer; `actions_were_offered` withholds the draft |
| 04-self-directed-sell | The same sell on a self-directed account with a clear screen | the tool is offered, the order is within the ledger, queued for confirmation |
| 05-fraud-report | A transfer the client did not make, from a new device | the risk screen writes `critical`; only `open_case` is offered; the triage must be critical |
| 06-pasted-statement | A fees question with a whole statement pasted in | `protected_content_over_budget` on the small tier, escalation, the answer cites the fees article |

## A day

| Time | Block |
| --- | --- |
| 0:00 | The brief, the blueprint, the gate. Run the reference on `03-advisory-sell-request` and `05-fraud-report`, and `cache.py`, before writing anything. |
| 0:30 | Intent and producers. Split the eight producers; the facts on `ledger` and `market-data`, the risk level the capability policy reads, and the grant the freeze carries are the coordination points. |
| 2:30 | The freeze and the first green cases. Replay. `cache.py` under your freeze. |
| 3:30 | Lunch. |
| 4:15 | The screens, the risk level read off the trace, escalation, cache reuse against history-first. |
| 5:30 | Two cases of your own. One reviewed placement or policy change with the measure as evidence. Record, grade, promote. |
| 6:45 | Demo: each team shows one trace that explains a decision a prompt could not have, and one number a prompt could not have produced. |

## What the gate checks

The route contract; the producers and only the producers the route lists; protected client state with no identifiers; the ledger as current state and the vendor estimate as untrusted evidence; the declared conflict decided by precedence; the risk screen as application-written state and as the capability policy's input; the capability policy as the only source of tools; one scored item per paragraph and a refusal when nothing survives; budgets computed and the pasted statement escalating; cache reuse under the committed profile beating history-first; the contracts on parser routes; the six screens as units and in the cases; every attempt replaying byte for byte; every case's expectations.

## What a live run showed

With omlx serving `gpt-oss-20b-MXFP4-Q8` (2026-10-11, `evals/results/gpt-oss-20b-01/`), two of the four live cases passed; `02-vendor-figure-in-answer` and `03-advisory-sell-request` script a bad draft to exercise a guard and are `scripted_only`. The ledger's figure was reported and the pasted statement escalated and was answered. The two that failed are the model's handling of the tool schema: an order with no `client` and an invented `order_type`, and a fraud case opened with arguments the schema does not allow. The action guard validates arguments against the offered tool's schema and withholds the draft, so nothing was queued and the request went to an advisor, which is the designed outcome for an order the system cannot trust. An earlier pass also listed cash as a figure, which the guard now accepts when it is the ledger's cash. No profile was promoted from this run.

With `Qwen3.6-35B-A3B-8bit` on the same server, thinking turned off through `CWA_WORKSHOP_EXTRA_BODY` and the tools visible to the model (`evals/results/qwen3.6-35b-a3b-01/`), all four live cases passed: the order and the case were placed with the schema's arguments and queued for confirmation. Both route profiles are promoted from that report; `policy/registry.lock.json` pins them. A team's own promotion replaces it.

## Closing section, written by the team

Which placement or policy did you change, what did `cache.py` and the stored traces say it would change, and did you ship it? Which decision in your traces would a prompt not have been able to explain? What would you need before running the suite live, and what in the gate could a live model still get wrong?
