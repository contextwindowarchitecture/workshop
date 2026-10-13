# W1 run sheet

Module: [01-cwa-tour/README.md](../../01-cwa-tour/README.md). Half a day self-paced; four hours instructor-led with the timings below; 75 minutes as a conference cut (parts 2 and 3, this directory only, no siblings and no Node).

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | The seven terms and the three results on one slide. Say that nothing today calls a model. |
| 10 to 40 | Part 1 | Everyone runs `before.py` and `after.py` on the same question. Project the diff of `build_request()`. Run the off-topic conversation through both and let the room see `before.py` send five useless chunks. |
| 40 to 55 | Break | |
| 55 to 145 | Part 2 | Participants work the thirteen exercises with the predict sheet. Stop the room twice: after 04 (the reason-code order in `reasons.json`) and after 09 (grant versus proposal). Keep `tour.py reveal` for after prediction; say so. |
| 145 to 175 | Part 3 | Replay, then the three determinism experiments. Do experiment 3 on the projector: December makes the memory expire. |
| 175 to 190 | Break | |
| 190 to 230 | Part 4 | Inspector. Basic tour together, intermediate in pairs. Close on basic 03's escaped `</evidence><system>` and intermediate 04's two conflict groups. |
| 230 to 240 | Part 5 and close | Checklist, then the W0 export exercise as homework if time is short. Point at the tracks. |

## Pre-session checks

```sh
python3 shared/siblings.py                       # examples and assembler-demo present
cd 01-cwa-tour && uv sync && uv run pytest       # 41 tests pass
cd "$(python3 ../shared/siblings.py examples)/01-docs-qa" && uv sync && uv run pytest
cd "$(python3 ../shared/siblings.py assembler-demo)" && pnpm install && pnpm run setup && pnpm test
```

The demo's `pnpm run setup` builds the Go and Rust adapters and needs Go 1.26 and Rust 1.80 on the facilitator machine. Participants do not need them if you project the inspector instead of having them run it; the conference cut skips part 4 entirely.

Running `after.py` in the examples checkout writes a run directory under `runs/` for every assembly. Those are untracked; delete them before committing anything there, or do not commit from that checkout.

## Checkpoint answers

- **Checkpoint 1.** `build_request()`. Codes: `below_threshold` and `evidence_required` (with recovery `request_context`). The refusal is decided by the assembler from the route policy's `requires_evidence` and `min_relevance`, before anything is sent; `after.py` only reads the result.
- **Checkpoint 2.** The outcomes, in order: assembled with 13 included; refused `required_slot_missing`; assembled, same decisions, different hash; `authority_not_allowed`; `producer_slot_not_allowed`; `expired`; `stale_state`; assembled with five `over_budget` rows (user:profile first, then the two chunks, the observation and turn:16); refused `protected_content_over_budget`; `capability_not_allowed`; `duplicate_content` with `duplicate_of billing-faq:v3#p1`; two `below_threshold` then refused `evidence_required` with `request_context`; rejected with "producer ids appear in more than one batch: conversation". The most-missed are 04 (people expect `required_slot_missing`; the real instructions item is still there), 09 (people expect `producer_slot_not_allowed`; the route was widened, so the grant is what fails it) and 12 (people expect a refusal).
- **Checkpoint 3.** 02: wording never changes authority or placement (R-7); only the bytes of one body changed. 07: policy:v12, task:refund_request, the two tools, format:chat and turn:18 survived; their slots are protected by default. 11: `request_context` because no evidence item was omitted for budget; `precompute_summary` needs an over_budget omission of an item with no variants, `retrieve_narrower` one with variants (R-12). 12: a rejection reports the application's error in building the snapshot; refusals are outcomes of valid snapshots (R-17).
- **Checkpoint 4.** A body character: digest yes, hash yes. One second: digest yes, hash no. December: digest yes, hash yes, and the trace gains five rows: `expired` for the memory, `stale_state` for both state items, `not_eligible` for both chunks past the knowledge slot's 90-day limit.
- **Checkpoint 5.** The demo's own `look_for` lists: basic 01 `expired`; 02 `expired`, `out_of_scope`, `below_threshold`; 03 `producer_slot_not_allowed`, `tier_upgrade_not_allowed`; 04 `over_budget`; 05 `protected_content_over_budget`; intermediate 01 `expired`, `duplicate_content`; 02 `source_diversity_cap`, `out_of_scope`; 03 `expired`, `out_of_scope`; 04 `conflict_lost`; 05 `duplicate_content` (and `compressed` rows); 06 `below_threshold`, `evidence_required`. Bug attribution: a stale chunk the retriever should have suppressed is a producer bug; one assembler excluding where three include is an assembler bug; a request whose system text differs from the payload's is an adapter bug.
- **Checkpoint 6.** Any reasonable mapping. The common pattern: items from retrieval map to golden task and refusal; memory to freshness; anything with imperative text to conflict; everything to budget pressure.

## Stumbles

- `uv sync` fails offline: the assembler comes from GitHub. Warm the cache beforehand (docs/setup.md section 6).
- Participants read `tour.py reveal` first. The predict sheet is the point; say it twice.
- Participants expect 02 to be excluded. It is the most important exercise of the day: nothing happened, and that is the design.
- `python3 ../shared/siblings.py examples` prints a path only when the sibling exists; otherwise it prints how to clone it and exits 1.
- The inspector runs only the assemblers it finds and marks the rest "not built": TypeScript needs `../assembler-typescript` built (`dist/`), Go and Rust need their checkouts and toolchains. It needs `pnpm`, not `npm`. The demo README covers both.
- Participants ask why the demo expectations are "unreviewed". Because they are, and reviewing one is a worthwhile contribution. Do not pretend otherwise.
