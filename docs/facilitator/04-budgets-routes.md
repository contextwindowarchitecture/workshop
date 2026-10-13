# W4 run sheet

Module: [04-budgets-routes/README.md](../../04-budgets-routes/README.md). Half a day self-paced; four hours instructor-led; 90 minutes as a conference cut (part 1, Lab A, Lab D). Model-free. Lab C needs `uv run --extra calibrate` and the network once for tiktoken's encoding file; warm it beforehand.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | Three tiers, three refusals, one margin rule. "Refusal is an outcome, not an error." |
| 10 to 30 | Part 1 | Run the export and the pasted log. Two tables for the log: the small route refusing before any reduction, the large route assembling a fresh snapshot. |
| 30 to 80 | Lab A | Review. At 60 minutes run scenario 05 with `--impl labs --budget 500` on the projector and read the swapped summary aloud next to its paragraph. |
| 80 to 95 | Break | |
| 95 to 135 | Lab B | Routes and escalation. Make each table defend `evidence_required` escalating: is a bigger model the right answer to missing evidence? Sometimes it is only the right answer to a smaller budget. |
| 135 to 165 | Lab C | Calibrate. The surprise is that the estimate is nearly right on English prose and the margin is headroom for other text. |
| 165 to 175 | Break | |
| 175 to 230 | Lab D | Cases. Pairs, predict then run then reveal. |
| 230 to 240 | Close | Which truncation heuristic in their system goes first. |

## Pre-session checks

```sh
cd 04-budgets-routes && uv sync && uv run pytest && uv run scenarios.py --check && uv run summarize.py --check
CWA_W4_IMPL=labs uv run pytest tests/test_lab_a_review.py tests/test_lab_b_routes.py   # 4 fail: the lab files are the starting state
uv run --extra calibrate calibrate.py --stop-rule                                        # tiktoken fetched and working
```

## Checkpoint answers

- **Checkpoint 1.** Small: 2048 less 512 is 1536. Large: 8192 less 1024 is 7168. Both carry a 15% margin. The solution escalates `protected_content_over_budget` and `evidence_required`.
- **Checkpoint 2.** `help:data-export@6#2` (says every plan; Team and Business only), `help:plans@9#3` (swaps annual and monthly prices), `help:refunds@4#1` (monthly plans are not refunded; cancellation takes effect at period end), `help:roles@4#1` (admins cannot change billing). Scenario 05's payload says admins "can change billing"; the paragraph says they cannot unless an Owner makes them a billing admin. 04 records `precompute_summary` because `help:refunds@4#1` and `help:plans@9#3`, both omitted for budget, have no variant: their summaries were rejected, so there was nothing shorter to fall back to.
- **Checkpoint 3.** Any defensible table. The one to push on is `evidence_required`: escalating it to a bigger budget helps only when evidence was omitted for budget (recovery `precompute_summary` or `retrieve_narrower`); when the recovery is `request_context`, nothing was omitted and a bigger model changes nothing.
- **Checkpoint 4.** Worst ratio about 1.005 with `cl100k_base`; recommended margin 6%. On the pasted log (`--conversation`) the ratio is about 1.32 and the recommendation 38%, so the 15% margin is not enough for that request. A published id must always mean its published count, or a trace that names it means nothing (R-16).
- **Checkpoint 5.** `cases.py reveal` has every answer. The commonly missed: margin rounding rounds up; a route's `tier_upgrades` value at or below the slot's default changes nothing, so a protected-by-default task stays protected and the assembly refuses rather than omit it; slot caps apply before budget pressure; `precompute_summary` when the omitted evidence had no variants, `retrieve_narrower` when it had.

## Stumbles

- Participants reject a summary for being shorter or blunter than the paragraph. Only unfaithfulness is a rejection; terseness is the point.
- Participants approve `help:exports-faq@2#0` and reject `help:data-export@6#0`, or the reverse, and are surprised both get the variant. Same text, same hash, one summary.
- Participants write an escalate entry for every refusal code. Ask what the large route does about `conflict_unresolved` or `required_slot_missing`: nothing, and a second attempt that cannot succeed is cost without benefit.
- `--budget` overrides the first attempt only, by design; the escalated attempt uses its route's real budget.
- Cold tiktoken fetch fails offline; the stop-rule demo and the measured numbers in the README stand in.
