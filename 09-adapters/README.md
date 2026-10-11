# W9. Adapters

Status: planned. Not yet written.

This directory is scaffolded so the catalog layout is visible. The objectives, goals, outcomes and calls to action are in the plan, [section 3, W9](../docs/plan/workshops.md); the module will carry them here when it is written, with numbered checkpoints, a `scenarios/` folder of committed snapshots, traces and payloads, and a `scenarios.py --check` that CI runs without a model.

What will be here:

- a-tool-to-producer/: wrapping a retriever, a memory table and an MCP server so they emit batches
- b-assembler-protocol/: the stdin and exit-code protocol and the harness compare
- c-provider/: cwa-messages/v1 to an OpenAI-compatible request, proven by hash
- d-host-seam/: permission becomes authority, with fullsend as the worked example
