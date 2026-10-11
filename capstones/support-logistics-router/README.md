# Capstone C2. Customer support and logistics router

One day, in teams of three or four. Everything you did in W2 to W7, applied to a new domain, a new dataset and a different shape of application, with an acceptance gate instead of a worksheet.

## The brief

Northwind Outdoors, an online outdoor-gear retailer, wants its web-chat support assistant rebuilt on CWA. Customers write about returns, damaged items and deliveries. The assistant must answer from policy, from the ticket and the order as the system of record, and from what support has already told this customer. It must route each message to the right policy, fit a small model's budget and escalate to a larger one when it cannot, never leak a customer's contact details or another customer's business, and hand the ticket's next stage to the application rather than deciding it itself.

[BLUEPRINT.md](BLUEPRINT.md) is the design in the specification's terms, including what changed from the original sketch and why. [DELIVERABLES.md](DELIVERABLES.md) is the list of what your team hands in and the test that checks each item.

## What is given

- `data/`: five policy articles, three customers, four orders, three tickets, five CRM notes with hand-written summaries, and the intent rules. One refund paragraph appears word for word in two articles; one CRM note contradicts the order record; one customer's notes hold her phone number.
- `policy/`: three routes (`returns`, `damaged`, `general`), each a route policy and a profile, a shared output contract, and a routes table with a small and a large tier and an escalate table.
- `app.py`: the orchestrator. It classifies, routes, freezes a snapshot per attempt, escalates on refusal, hands the payload to the drafter unchanged, parses the output contract, runs the screens, and writes the ticket's next stage. It calls the modules you write and never assembles.
- `evals.py`, `evals/cases/`: six gate cases with scripted drafts and expectations, and the runner that records, grades and promotes.
- `solution/`: a reference. Facilitators have it; teams get it at the end of the day.

## What you build

Four modules in `skeleton/`, each with its contract in its docstring: the intent classifier, the seven producers, the freeze with conflict groups, and the three screens. Then two gate cases of your own, a reviewed change to one route policy, a recorded suite, and the promotion.

```sh
uv sync
uv run app.py --conversation evals/cases/01-return-jacket/conversation.json --draft evals/cases/01-return-jacket/draft.json          # the reference
uv run app.py --impl skeleton --conversation evals/cases/01-return-jacket/conversation.json --draft evals/cases/01-return-jacket/draft.json
CWA_C2_IMPL=skeleton uv run pytest
```

## A day

| Time | Block |
| --- | --- |
| 0:00 | The brief, the blueprint, the gate. Run the reference once on the pasted-thread case and the PII case. |
| 0:30 | Intent and producers. Split the seven producers across the team; the facts on `orders-db` and `crm-notes` are the coordination point. |
| 2:30 | The freeze and the first green cases. Replay. |
| 3:30 | Lunch. |
| 4:15 | Screens, escalation, the leak case, variants under a squeezed budget. |
| 5:30 | Two cases of your own. One reviewed policy change with a what-if note. Record, grade, promote. |
| 6:45 | Demo: each team shows one trace that explains a decision a prompt could not have. |

## What the gate checks

The contract between intent and route; the producers and only the producers the route lists; state written by the application, protected and current; no contact details in any payload; CRM notes as memory with reviewed variants and their own scope; the declared fact conflict decided by producer precedence; the identical refund paragraph deduplicated across two articles; a CRM leak caught by scope; budgets computed from the model limits and the pasted thread escalating; variants used before notes are omitted; the output contract placed on a parser route; the PII screen withholding a draft; citations that must have been sent; the other-customer screen; every attempt replaying byte for byte; every case's expectations.

## Closing section, written by the team

Which route policy did you change, what did the stored traces say it would change, and did you ship it? Which decision in your traces would a prompt not have been able to explain? What would you need before running the suite live, and what in the gate could a live model still get wrong?
