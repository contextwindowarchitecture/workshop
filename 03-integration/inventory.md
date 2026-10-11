# W3a inventory

Name or handle: ______________________  Date: ____________

## Step 1. The old prompt, in slots

| Text in `before/app.py` | Slot | Authority | `source` / `source_version` would come from | Exposed to which failure mode |
| --- | --- | --- | --- | --- |
| instructions.md | | | | |
| the account line | | | | |
| "Things I remember about this user" | | | | |
| the five articles | | | | |
| the last six messages | | | | |
| the question | | | | |

"Never" and "always" sentences in `before/instructions.md`, and whether a guard could enforce each:

| Sentence | Enforceable outside the model? | What the guard checks |
| --- | --- | --- |
| | | |
| | | |
| | | |

## Step 4. Two checks, with my own eyes

- Replayed digest and hash for `01-ada-export`: ______________________ / ______________________ (matched the committed trace: yes / no)
- With `relevance` removed from one chunk, the trace recorded: ______________________

## Done. The application conformance list (spec §1)

| Duty | Met by | Open? |
| --- | --- | --- |
| enforces invariants outside the model (R-5) | | |
| writes state itself, never from model output (R-8) | | |
| declares conflict groups (R-11) | | |
| authenticates each producer and binds identity outside the items (R-15) | | |
| makes every external read before freezing; refreezes for a retry (R-12, R-23) | | |
| sets `parser: true` where a downstream parser exists (R-4) | | |
| sets `budget.input` from the model's context limit less `reserved_output` (R-16) | | |
| versions its profiles and deploys only evaluated ones (R-19, R-20) | | |
| hands the payload over unchanged, with no text of its own (§1) | | |
