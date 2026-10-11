# W2 worksheet

Name or handle: ______________________  Date: ____________

## Checkpoint 1. Reading the given producers

| Field | app-policy sets it to | chat-session sets it to (a prior model turn) | Why they differ |
| --- | --- | --- | --- |
| authority | | | |
| trust | | | |
| injection_risk | | | |
| lineage | | | |

## Checkpoint 2. Lab A, retrieval

- Chunks emitted: ____  Reported as near-duplicates by my producer: ____  Excluded by the assembler as exact duplicates: ____
- Below the route's threshold: ____ (I did not filter them; the route did.)
- Items with a variant: ____  The variant's lineage, and why it is not `summarised`: ______________________
- With `lineage` removed from my items, `defaults_filled` grew by: ____ rows

## Checkpoint 3. Lab B, memory

| Memory | What my producer did | What the trace shows |
| --- | --- | --- |
| mem:u_ada:0003 | | |
| mem:u_ada:0001 | | |
| mem:u_ada:0005 | | |
| mem:u_ben:0001 under the leak fault | | |

## Checkpoint 4. Lab C, state

- `freshness` on my state items is: ______________________ (not: ______________________)
- Read at 09:50, asked at 10:00, route allows 300 s: the code is ______________________
- Why `stale_state` and not `not_eligible`: ______________________________________________

## Checkpoint 5. Lab D, five wrong items

| Function | Code I expected | Code the trace recorded | Caught by lint.py? |
| --- | --- | --- | --- |
| claims_protected | | | |
| wrong_slot | | | |
| unmarked | | | |
| reused_id | | | |
| no_relevance | | | |

- An item wrong in two ways got the ______________ code, because reasons.json is in ______________ order.

## Checkpoint 6. My own producer

- The tool or store I will wrap: ______________________  Its kind: ______________
- The slot(s) it may address: ______________________
- The checklist lines it will have the hardest time meeting: ______________________________________________
