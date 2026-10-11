# W9 module A worksheet

Name or handle: ______________________  Date: ____________

## Checkpoint 1. The finished route

- The producer that put the tools in front of the model: ______________________
- Superseded: ______________ by ______________, because both share the source ______________________________

## Checkpoint 2. Lab 1, the retriever

- Hits returned by LlamaIndex: ____  Items emitted: ____  Reported as near-duplicates: ____
- The two identical chunks: ______________________ and ______________________. The route kept ______________________ because ______________________________________________
- The field my adapter could not have produced if the node metadata were missing: ______________________

## Checkpoint 3. Lab 2, the memory table

| | `02-memory-reported` | `03-memory-silent-fault` |
| --- | --- | --- |
| included items | | |
| producer-stage rows | | |
| anything wrong in the trace? | | |

- To catch the silent bug, a reviewer would have to read: ______________________________________________

## Checkpoint 4. Lab 3, the MCP server

- Specs emitted as items got the code ______________________. With the route widened to list `governance.capabilities` for the adapter they would get ______________________.
- With ids `cap:<name>` instead of `mcp-cap:<name>`, the result was: ______________________________________________
- As Ben, the tool not offered: ______________________, reported at stage ______________ by ______________________

## Checkpoint 5. My own adapter

| | |
| --- | --- |
| The tool and what it returns natively | |
| Producer kind and slot(s) | |
| `id` comes from | |
| `source` and `source_version` come from | |
| `freshness` comes from | |
| the score comes from (or none) | |
| what it will report as suppressed | |
| what it cannot know, and who must be told | |
