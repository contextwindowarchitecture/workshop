# W9 module A. Tool-to-producer adapters

Half a day, self-paced, model-free. You leave with three adapters you wrote, each turning what a tool you already run returns into a conformant producer batch without changing the tool, and a pattern for wrapping the next one.

## Before you start

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/). `uv sync` here installs the reference assembler, LlamaIndex with its BM25 retriever, and the MCP SDK. No model, no key, no sibling repository.
- Finish W2, or know what a batch, an item and the eight stages are. This module assumes you can write a producer; it is about what changes when the data comes from a tool you do not control.
- Open [worksheet.md](worksheet.md) beside this file.

Conference cut (75 minutes): part 1 and Lab 3.

## What an adapter is

Most teams already have a retriever, a vector store, a memory layer, a CRM client, a feature store or an MCP server. None of them emits items. An adapter sits between the tool and the snapshot and turns the tool's native output into a producer batch, leaving the tool alone. Its duties are the producer's duties, applied to data it did not shape:

1. **One item per thing**, in the right slot, with the authority that slot takes. A merged blob is never an item (R-13).
2. **Provenance from the tool's own identifiers.** `source` and `source_version` come from what the tool knows: a document and its version, a table row and its id, a tool call and its arguments, a server and its version. When the tool does not carry them, the adapter cannot invent them, and that is a finding about the pipeline.
3. **Scores passed through, never used to filter.** The route's threshold decides, so the trace shows it (R-13).
4. **Suppressions reported.** Anything the adapter drops is an `excluded` row with a reason, and anything it never saw because of how it queried the tool is invisible to everyone downstream (R-9, R-14).
5. **The injection marker** on everything that came from outside governance (R-10, R-15).
6. **Variants, if any, precomputed** and looked up, never written during the request (R-18).
7. **Identity left to the application.** The adapter fills the batch; the application stamps `producer: {id, kind}` and the route decides which slots that identity may fill (R-15).

Three tools are given in `tools/`, and you do not edit them: a LlamaIndex BM25 retriever over the Fernway help centre, a SQLite memory table loaded from the Fernway fixture, and an MCP server of Fernway account and status data driven through the official SDK over stdio.

## Part 1. The finished route (20 minutes)

```sh
uv sync
uv run run.py --user u_ada --calls account,status,status "Is there an incident in our region right now?"
```

Six producers ran: the route's instructions, the capability policy, and the three adapters plus the conversation. Read the table from the top. Three tools render in the `tools` channel, offered by the capability policy, not by the MCP adapter. Two observations are included and one is excluded as `superseded`: the status was polled twice and the route's `supersede: source` kept the newer poll (R-25). The memory store reported an expired and a revoked memory at stage `producer`. Eight chunks fell below the threshold: none of the help centre answers an incident question.

Run it again with `--payload` and find the two observations inside the user message, each in its own `<observation>` wrapper, with `obs:3` saying the incident is resolved and `obs:2` nowhere.

**Checkpoint 1.** In the worksheet: which producer put the tools in front of the model, and which item was superseded by which.

## Lab 1. A retriever you already run (50 minutes)

Open [labs/retriever_adapter.py](labs/retriever_adapter.py). The tool is `tools/llama_retriever.py`: LlamaIndex's `BM25Retriever`, returning `NodeWithScore` objects. The provenance an item needs is in the node metadata only because ingestion put it there. Your adapter finds it, packages one item per hit, reports near-duplicates and leaves exact copies for the route.

```sh
CWA_W9A_IMPL=labs uv run pytest tests/test_lab_retriever.py
uv run run.py --impl labs --user u_ada --calls "" "How do I export the whole workspace, including attachments?"
```

Something this retriever does that W2's did not: it ranks the exports FAQ's word-for-word copy above the data-export original. Your adapter passes the scores through, so the route's `dedupe: exact` keeps the higher-ranked copy and excludes the original with `duplicate_of help:exports-faq@2#0`. The trace is right and the outcome is still worth a look: a stale FAQ is what the model will cite. That is a finding about the help centre, visible only because nothing was filtered on the way in.

**Checkpoint 2.** The worksheet's Lab 1 lines, including which of the two identical chunks the route kept and why.

## Lab 2. A memory table you already run (40 minutes)

Open [labs/memory_adapter.py](labs/memory_adapter.py). The tool is a SQL table with `expires` and `revoked_by` columns. The natural query, `WHERE revoked_by IS NULL AND expires > ?`, is the bug this lab is about: it drops the rows a memory producer must report, before any Python can report them.

```sh
CWA_W9A_IMPL=labs uv run pytest tests/test_lab_memory.py
uv run run.py --impl labs --user u_ada --calls "" "Which identity provider do we use?"
uv run run.py --impl labs --user u_ada --calls "" --fault silent-sql "Which identity provider do we use?"
```

Compare the two traces. The included lists are identical. The first has two rows at stage `producer`, `expired` and `revoked`; the second has none. Nothing in the second trace is wrong, and nothing in it tells you two memories went missing. That is the breach admission cannot see, and the reason the producer conformance claim rests on the producer's word. The committed scenarios `02-memory-reported` and `03-memory-silent-fault` are these two runs.

**Checkpoint 3.** The worksheet's Lab 2 lines: what differs between the two traces, and what a reviewer of your adapter would have to read to catch the bug.

## Lab 3. An MCP server you already run (60 minutes)

Open [labs/mcp_adapter.py](labs/mcp_adapter.py). The tool is `tools/fernway_mcp.py`, a real MCP server over stdio, and `tools/mcp_client.py` runs one session for you: the server's info, its tool specifications, and a result per scripted call with an `observed_at` the application assigned. Your adapter does two things, and the separation is the lesson.

`proposals(specs)` hands the server's tool specifications to the capability policy unchanged. The policy in [capability_policy.py](capability_policy.py), driven by [policy/capabilities.json](policy/capabilities.json), decides which tools this user's role is offered, pins each input schema by SHA-256, uses its own description, reports every declined proposal as `capability_not_allowed`, and writes the grant into the snapshot (R-15). An MCP adapter proposes. It never emits a capability.

`observations(info, results, request)` turns each call result into an `evidence.tool_results` item whose `source` is the call itself, so a repeated call is superseded, whose `source_version` is the server's version, and whose body carries the result or the error. An error is an observation too.

```sh
CWA_W9A_IMPL=labs uv run pytest tests/test_lab_mcp.py
uv run run.py --impl labs --user u_ada --calls account,status,status "Is there an incident in our region right now?"
uv run run.py --impl labs --user u_ben "Who are the billing admins?"
uv run run.py --impl labs --user u_ada --fault specs-as-items "What plan are we on?"
```

The second command runs as Ben, a Member. The policy grants `list_members` to Owners and Admins, so `cap:list_members` is reported `capability_not_allowed` at stage producer and only two tools render. The third command makes the mistake the lab exists to show: the adapter emits the specifications as `governance.capabilities` items of its own. Every one is excluded as `producer_slot_not_allowed`, because the route lists only `evidence.tool_results` for this producer. Had the route listed `governance.capabilities` for it too, the code would be `capability_not_allowed`, because the grant does not name them (R-15). Either way the model never sees them. One more variant to try by hand: give the adapter's items the same ids as the policy's, `cap:<name>`, and watch `duplicate_item_id` take out the policy's grants as well (R-2). An adapter that collides with the policy's ids does real damage.

**Checkpoint 4.** The worksheet's Lab 3 lines: the two codes and the one route change that switches between them, and what the id collision did.

## Part 5. The pattern (20 minutes)

Write the adapter for one tool in your own system as a stub with a docstring like the three in `labs/`: the tool's native output, the slot and authority, where each of `id`, `source`, `source_version`, `freshness` and the score will come from, what the adapter will report as suppressed, and what it cannot know. Then run W2's [checklist](../../02-producers/checklist.md) over the stub.

**Checkpoint 5.** The stub, in the worksheet or beside it.

## After this module

- W3 migrates a whole application. The adapters you wrote here are its producers.
- Module B of W9 wraps an assembler instead of a tool; module C wraps a provider; module D a host.
- Contribute an adapter for a library the examples do not cover yet, to `examples` or `assembler-demo`.

## Covers

R-1, R-2, R-9, R-10, R-13, R-14, R-15, R-18, R-24, R-25. The committed scenarios are the answer key: `01-retriever` shows the copy outranking the original and the route keeping the copy, `02` and `03` differ only in what the trace can see, `04` shows supersession, `05` the adapter's specs excluded, `06` a Member not offered a tool.

## Files

- `labs/`: the three adapter stubs. `solution/`: finished versions, which CI tests. `impl.py`: the `CWA_W9A_IMPL` switch.
- `tools/`: the three wrapped tools and the MCP client helper. Given, not edited.
- `capability_policy.py` and `policy/capabilities.json`: the only producer of `governance.capabilities`.
- `common.py`, `fixed.py`, `run.py`, `policy/`: the surrounding application.
- `scenarios.py`, `scenarios/`, `tests/`: the regression check and the answer key.
