# W2 run sheet

Module: [02-producers/README.md](../../02-producers/README.md). Half a day self-paced; four hours instructor-led; 90 minutes as a conference cut (part 1, Lab A, Lab D). No siblings and no Node: the whole module is this directory plus the vendored contract.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | The seven kinds and their slot gates on one slide. "A producer proposes; the route decides." |
| 10 to 30 | Part 1 | Everyone runs the finished route once and reads the table. Point at the three `[producer]` rows: those travelled into the trace as the producer wrote them. |
| 30 to 90 | Lab A | Retrieval. Stop the room at 60 minutes to show the two `duplicate_content` rows at different stages, then the `--budget 600` squeeze. |
| 90 to 105 | Break | |
| 105 to 145 | Lab B | Memory. Run the leak fault on the projector and ask who caught the bug: the producer or the item's scope. |
| 145 to 175 | Lab C | State. The `--read-at` run. Ask what the application should do when it sees `stale_state`. |
| 175 to 185 | Break | |
| 185 to 225 | Lab D | Negatives. Close on `reused_id`: both items go, and on what `lint.py` cannot see. |
| 225 to 240 | Part 6 and close | Checklist against their own code; the checkpoint 6 section as homework. |

## Pre-session checks

```sh
cd 02-producers && uv sync && uv run pytest && uv run lint.py && uv run variants.py --check
CWA_W2_IMPL=labs uv run pytest tests/test_lab_a.py    # should fail: the stubs raise NotImplementedError
```

## Checkpoint answers

- **Checkpoint 1.** app-policy: `governing`, `verified`, `none`, `verbatim`, because governance must be verified and unmarked to pass the gate (R-10). A prior model turn: `untrusted`, `unverified`, `untrusted_content`, `generated`, because a model's earlier words can never instruct (R-1) and might carry an injection (R-10).
- **Checkpoint 2.** For Ada's export question with the solution: 9 chunks emitted, 1 reported by the producer (`help:exports-faq@2#1`, duplicate of `help:data-export@6#0`), 1 excluded by the assembler as an exact copy (`help:exports-faq@2#0`), 2 below the threshold of 3.0. Every emitted chunk has a lead-sentence variant except one-sentence paragraphs. The lineage is `extracted` because the first sentence was cut from the text, not written about it; `summarised` would claim a rewriting that did not happen. Removing `lineage` adds one `defaults_filled` row per item.
- **Checkpoint 3.** `mem:u_ada:0003` revoked, reported, trace row at stage producer. `mem:u_ada:0001` expired, same. `mem:u_ada:0005` sent and included. `mem:u_ben:0001` under the leak fault: sent by the buggy producer, excluded `out_of_scope` by the assembler, because the item's scope says `u_ben` and the request says `u_ada` (or the reverse, in scenario 03).
- **Checkpoint 4.** Freshness is the read time. A read at 09:50 for a question at 10:00 exceeds the route's 300 seconds, so `stale_state`. The state slots have their own code (R-8); `not_eligible` is the same rule's code everywhere else (R-3).
- **Checkpoint 5.** The codes are as the table says. `claims_protected` and `unmarked` are caught by lint and by the trace; `wrong_slot` likewise; `no_relevance` likewise; `reused_id` is caught by lint only when both items are in the same batch, and by the trace in every case. An item wrong in two ways gets the earlier code in `reasons.json` order: a chunk that is both unmarked and claims protected gets `untrusted_content_unmarked`.
- **Checkpoint 6.** Any real system. The lines teams find hardest: reporting suppressed entries by id, precomputing variants, putting `expires` on every memory, and not filtering by score.

## Stumbles

- Participants filter by relevance in Lab A because it feels wrong to emit a chunk they know will be excluded. Say why not: the trace shows the threshold working only if the item was offered.
- Participants set `freshness` on state to the row's `plan_since` or version date. Freshness is when the row was read.
- Participants give all five negative items the same id and then cannot tell the linter's `duplicate_item_id` noise from the real one. The stub's docstring says to give each its own id.
- `CWA_W2_IMPL` unset means the tests run against the solution and pass. Make sure they set it, or they will think they are done.
- `uv sync` offline fails; warm the cache beforehand.
