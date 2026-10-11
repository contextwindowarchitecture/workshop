# W1 predict sheet

Name or handle: ______________________  Date: ____________

Predict before you run. Write the result (assembled, refused, rejected) and the reason code or codes you expect, then the actual ones.

## Checkpoint 1. Before and after

- The one function that changed: ______________________
- Reason codes seen: ______________________ and ______________________
- Where the refusal decision was made: ______________________________________________

## Checkpoint 2. The thirteen exercises

| Exercise | Predicted result | Predicted code(s) | Actual result | Actual code(s) | Right? |
| --- | --- | --- | --- | --- | --- |
| 00-baseline | | | | | |
| 01-no-query | | | | | |
| 02-imperative-chunk | | | | | |
| 03-chunk-claims-governing | | | | | |
| 04-chunk-moves-to-instructions | | | | | |
| 05-expired-memory | | | | | |
| 06-stale-state | | | | | |
| 07-budget-pressure | | | | | |
| 08-budget-refusal | | | | | |
| 09-tool-from-mcp | | | | | |
| 10-duplicate-chunk | | | | | |
| 11-evidence-required | | | | | |
| 12-two-batches | | | | | |

Right: ____ of 13. For each miss, the sentence from the specification that explains it:

| Exercise | Requirement | The sentence |
| --- | --- | --- |
| | | |
| | | |
| | | |

## Checkpoint 3. Four questions

- 02: the hash changed, nothing else did, because ______________________________________________
- 07: the survivors were ______________________ and their slots share ______________________
- 11: `request_context` rather than the other two because ______________________________________________
- 12: no trace because ______________________________________________

## Checkpoint 4. Determinism

| Experiment | Digest changed? | Hash changed? |
| --- | --- | --- |
| one character in a body | | |
| assembly_time plus one second | | |
| assembly_time in December | | |

Rows added to the trace in December: ______________________________________________

## Checkpoint 5. The inspector

| Stage / step | Predicted code(s) | Actual code(s) |
| --- | --- | --- |
| basic 01-clean | | |
| basic 02-stale-and-foreign | | |
| basic 03-authority | | |
| basic 04-budget | | |
| basic 05-refusal | | |
| intermediate 01-retrieval | | |
| intermediate 02-overlap | | |
| intermediate 03-memory | | |
| intermediate 04-conflict | | |
| intermediate 05-summary | | |
| intermediate 06-evidence-required | | |

- A candidate-context change that would be a producer bug: ______________________________________________
- A decision that, made differently by one assembler, would be an assembler bug: ______________________________________________
- An outbound-request change that would be an adapter bug: ______________________________________________

## Checkpoint 6. §6.1 against my own items

| My item (from items.cwa.yaml) | Most likely failure | The §6.1 test that catches it |
| --- | --- | --- |
| | | |
| | | |
| | | |
| | | |
