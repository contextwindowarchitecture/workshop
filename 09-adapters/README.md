# W9. Adapters

Status: modules A, B and C ready; module D planned.

This directory is scaffolded so the catalog layout is visible. The objectives, goals, outcomes and calls to action are in the plan, [section 3, W9](../docs/plan/workshops.md); the module will carry them here when it is written, with numbered checkpoints, a `scenarios/` folder of committed snapshots, traces and payloads, and a `scenarios.py --check` that CI runs without a model.

What will be here:

- a-tool-to-producer/: wrapping a retriever, a memory table and an MCP server so they emit batches (ready: [a-tool-to-producer/](a-tool-to-producer/))
- b-assembler-protocol/: the stdin and exit-code protocol and the harness compare (ready: [b-assembler-protocol/](b-assembler-protocol/))
- c-provider/: cwa-messages/v1 to an OpenAI-compatible request, proven by hash (ready: [c-provider/](c-provider/))
- d-host-seam/: permission becomes authority, with fullsend as the worked example
