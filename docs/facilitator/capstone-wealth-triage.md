# Capstone C3 run sheet

Kit: [capstones/wealth-triage/README.md](../../capstones/wealth-triage/README.md). One day, teams of three or four. Model-free throughout; a live drafter is optional at the end. Teams must have done W2, W3a, W5 and W6; W4 and W7 help. Every client, holding and article is fictional.

## Running the day

- Open with the brief and the blueprint, then run the reference on `03-advisory-sell-request` and `05-fraud-report`, and `cache.py`. The room should see a tool withheld before any model ran, a risk screen setting a floor, and a number about placement, before writing anything.
- Hand out `skeleton/` only. `solution/` is yours until the demo.
- Three coordination points, say all three at the start: the fact `position.ACME` asserted by `ledger` and by `market-data`; the risk level, computed once in `risk_level()` and used both by `risk_screen` (as state) and by `capability_policy` (as a gate); and the grant the freeze puts in the snapshot's `capabilities` member.
- The cache measure is the day's distinctive moment. Make teams run `cache.py` under their own freeze, then move one slot in the profile and run it again. The number moves; the trace explains why.
- The two cases each team writes are where the thinking shows. Push for one that breaks something: a sell of more units than the ledger holds, a reply that quotes an IBAN, a dispute triaged as fraud, a question with no article behind it.
- The demo question is fixed: one trace that explains a decision a prompt could not have, and one number a prompt could not have produced.

## Pre-session checks

```sh
cd capstones/wealth-triage && uv sync && uv run pytest && uv run scenarios.py --check && uv run cache.py
CWA_C3_IMPL=skeleton uv run pytest -q 2>&1 | tail -1     # fails: the stubs raise NotImplementedError
```

## Where teams get stuck

- Putting the vendor's position in `state.task` beside the ledger's. Both are protected there, the group cannot exclude either, and it escalates and refuses. The estimate is an observation; the ledger is the record.
- Computing the risk level twice, differently. One function, called by both producers.
- Granting `place_trade` by mandate alone. The policy's `max_risk` is part of the grant; case 05's client is self-directed and still gets no trading tool.
- Reading the ledger too late in the day. The morning batch is 08:30; the route ages `state.task` at an hour, and a request after 09:30 sees `stale_state` and a moot conflict. Say so when teams write their own cases.
- Making the trade guard check the vendor's units. The guard holds to the ledger because the route did.
- Lowering `min_relevance` until every question retrieves something. Show case 06's fraud paragraph under the cap and ask what a threshold is for.
- Expecting cache reuse of 100%. The articles and the query change every turn by design; the measure is the stable prefix, not the whole payload.

## After the day

Collect each team's closing section. The placement change and its measure, the decision a prompt could not explain, and what a live model could still get wrong are the capstone's real output.
