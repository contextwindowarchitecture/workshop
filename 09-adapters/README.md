# W9. Adapters

Four modules, each a half day taught on its own, each with its own README, worksheet, numbered checkpoints and run sheet in [docs/facilitator/](../docs/facilitator/). Each has a `scenarios.py --check` that CI runs without a model. The objectives behind them are in the plan, [section 3, W9](../docs/plan/workshops.md).


- [a-tool-to-producer/](a-tool-to-producer/): wrapping a retriever, a memory table and an MCP server so they emit batches
- [b-assembler-protocol/](b-assembler-protocol/): the stdin and exit-code protocol and the harness compare
- [c-provider/](c-provider/): cwa-messages/v1 to an OpenAI-compatible request, proven by hash
- [d-host-seam/](d-host-seam/): permission becomes authority, with fullsend as the worked example
