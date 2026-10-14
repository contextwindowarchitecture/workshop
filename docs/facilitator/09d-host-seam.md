# W9 module D run sheet

Module: [09-adapters/d-host-seam/README.md](../../09-adapters/d-host-seam/README.md). Half a day self-paced; three and a half hours instructor-led; 60 minutes as a conference cut (part 1 and Lab 2). Model-free, no siblings needed; the `integrations` sibling lets you show the Go original beside the port.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "The host already knows who may speak. CWA gives that knowledge a slot." |
| 10 to 40 | Part 1 | `before.py`, then `after.py --compare`. Point at the escaped HTML comment and at `speaker="assistant"`. |
| 40 to 130 | Lab 1 | The port. Most rooms get governance and state in twenty minutes and spend an hour on the thread split and memory. Diff against `scenarios/triage-7811/snapshot.json` early. |
| 130 to 140 | Break | |
| 140 to 170 | Lab 2 | The scorer. Project the two `fitting_order` arrays. |
| 170 to 200 | Lab 3 | The refusal. Read three comments aloud; pick the one a maintainer would act on. |
| 200 to 240 | Part 5 and close | Each participant's host on the worksheet; collect two and ask what the system has no source for today. |

## Pre-session checks

```sh
cd 09-adapters/d-host-seam && uv sync && uv run pytest && uv run scenarios.py --check && uv run after.py --compare
CWA_W9D_IMPL=labs uv run pytest -q 2>&1 | tail -1     # 8 fail: the stubs
```

## Checkpoint answers

- **Checkpoint 1.** maintainer-a: `interaction.history`, `user`. The bot: `interaction.history`, `untrusted`, `lineage: generated`. The reporter and drive-by-1: `evidence.tool_results`, `observation`. The hidden instruction is in `obs:issue/7811/0-body@newcontrib`; the model sees it escaped (`&lt;!-- AI agents ...`) inside `<external_content>`, which the agent definition names as material.
- **Checkpoint 2.** Usually the thread split (the bot has permission `write` but is checked first) or memory (expiry compared as instants, the expired entry reported with stage `producer`). The digest check catches any body or eligibility string; the committed snapshot diff names it.
- **Checkpoint 3.** v1 dropped `run:review/18990#F1` (high severity) and the docs diff, and kept `claude_test.go`; v2 dropped `claude_test.go` and the docs diff and kept F1. v1's `fitting_order` omits `interaction.memory` first; v2 removes that step and adds `tier_upgrades: {interaction.memory: protected}`.
- **Checkpoint 4.** `evidence_required`, recovery `precompute_summary`. A good comment names the reason, says the diff items need precomputed summaries, lists what was dropped for budget (every diff and the current CI run), and the budget and policy version. Span: `cwa.refused true`, `cwa.refused.reason evidence_required`, `cwa.recovery.action precompute_summary`, the snapshot digest.

## Stumbles

- Participants check the bot comment by permission (it has `write`) and make it `user`. The Go switch checks `bot` first; so should the port.
- Participants drop the expired memory entry silently. The test wants it reported with stage `producer`.
- Participants put the hidden instruction's detection in the producer. Nothing detects it: it is escaped material because of who wrote it, not what it says.
- Participants write the refusal comment from the model's output. There is no model output; the sandbox never started.
