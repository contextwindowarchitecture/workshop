# Capstone C2 run sheet

Kit: [capstones/support-logistics-router/README.md](../../capstones/support-logistics-router/README.md). One day, teams of three or four. Model-free throughout; a live drafter is optional at the end. Teams must have done W2 and W3a; W4 to W7 help.

## Running the day

- Open with the brief and the blueprint, then run the reference once on `04-pasted-thread` and `05-pii-in-draft` so the room sees escalation and a withheld draft before writing anything.
- Hand out `skeleton/` only. `solution/` is yours until the demo; teams that read it early learn less, and the gate does not care how they got there.
- The coordination point in every team is the facts: `orders-db` and `crm-notes` both assert `delivery_status:o_7781`, and the freeze turns that into a conflict group. Say it at the start; teams that split producers without agreeing on it lose an hour.
- The two cases each team writes are where the thinking shows. Push for one that breaks something: a draft citing an article that was shed, a message that no intent rule matches, a note with no summary.
- For the policy change, insist on the what-if habit from W7 even though this kit has no store: run the suite before and after and compare the reports.
- The demo question is fixed: show one trace that explains a decision a prompt could not have. The conflict group, the escalation and the scope leak are the usual answers; a team that shows the dedupe across two articles has read the trace carefully.

## Pre-session checks

```sh
cd capstones/support-logistics-router && uv sync && uv run pytest && uv run scenarios.py --check
CWA_C2_IMPL=skeleton uv run pytest -q 2>&1 | tail -1     # fails: the stubs raise NotImplementedError
```

## Where teams get stuck

- Putting the customer's phone or email in the `state.user` body "for the callback". The gate test on contact details fails; ask what the model needs to answer and whether a phone number is it.
- Filtering CRM notes to the current order. The notes are memory about the customer, not the order; the route and the scope decide, and the conflict needs the contradicting note present.
- Making `crm_notes` emit history instead of memory. The blueprint's table says why not.
- Writing the intent classifier to also pick the budget tier. Tier is the orchestrator's, from the routes table; intent picks the route.
- Expecting the guards to run on the raw draft. They run on the parsed `reply`; a draft that is not the contract's JSON is a contract failure, handled before the screens.
- `citations_were_sent` failing on a correct-looking draft because the cited paragraph was deduplicated: the refund sentence exists in two articles and only one survives. That is the gate working, and a good demo moment.

## After the day

Collect each team's closing section. The three questions there, the policy change and its evidence, the decision a prompt could not explain, and what a live model could still get wrong, are the capstone's real output.
