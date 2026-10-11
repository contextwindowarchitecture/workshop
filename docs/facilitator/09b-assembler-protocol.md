# W9 module B run sheet

Module: [09-adapters/b-assembler-protocol/README.md](../../09-adapters/b-assembler-protocol/README.md). Half a day self-paced; three hours instructor-led; 75 minutes as a conference cut (part 1 and the lab). Model-free. The four-way agreement at the end needs the `assembler-demo` sibling built (`pnpm install && pnpm run setup`), which needs Go and Rust; skip it without.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "A runner must not import the assembler." The three exits on one slide. |
| 10 to 30 | Part 1 | The three runs, then the full suite. Open the report and the schema side by side. |
| 30 to 90 | The lab | Thirty lines. The usual first failure is a print statement; the second is the exit 3 sentence. |
| 90 to 100 | Break | |
| 100 to 140 | Part 3 | Compare, the broken expectation, and the four-way agreement if the demo is built. |
| 140 to 150 | Close | Where a disagreement goes: W10. |

## Pre-session checks

```sh
cd 09-adapters/b-assembler-protocol && uv sync && uv run pytest && uv run scenarios.py --check
CWA_W9B_IMPL=labs uv run pytest tests/test_lab_adapter.py     # 6 fail: the stub
```

## Checkpoint answers

- **Checkpoint 1.** fixture-three-slot: exit 0, the JSON object on stdout, nothing on stderr. required-slot-missing: exit 0, payload null, trace with refused true. producer-in-two-batches: exit 2, nothing on stdout, the problem on stderr.
- **Checkpoint 2.** 65 and 25. The except clauses: `SnapshotError` is 2, `UnsupportedComponentError` is 3. Validation runs before component resolution inside `Snapshot.from_json`.
- **Checkpoint 3.** `/included/0/tokens`. Four-way: one hash.

## Stumbles

- Participants print progress to stdout. The harness parses stdout; say it once more.
- Participants read the whole of stdin as text and decode with errors ignored. Non-UTF-8 input is a rejection.
- Participants return 1 on a rejection. The protocol's exits are 0, 2 and 3; anything else is an adapter error.
