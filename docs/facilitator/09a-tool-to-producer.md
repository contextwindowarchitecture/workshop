# W9 module A run sheet

Module: [09-adapters/a-tool-to-producer/README.md](../../09-adapters/a-tool-to-producer/README.md). Half a day self-paced; four hours instructor-led; 75 minutes as a conference cut (part 1 and Lab 3). Everything runs in this directory: no model, no siblings, no Node. `uv sync` installs LlamaIndex and the MCP SDK, which takes a minute on a warm cache and longer cold.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | The seven adapter duties on one slide. "The tool does not change; the adapter carries provenance the tool already has." |
| 10 to 30 | Part 1 | Everyone runs the finished route with `account,status,status`. Point at the three tools in the `tools` channel and ask which producer put them there. Then `obs:2 superseded_by obs:3`. |
| 30 to 80 | Lab 1 | Retriever. At 70 minutes show the stale FAQ copy winning the dedupe and ask whether the trace is wrong (it is not) and what is (the help centre). |
| 80 to 95 | Break | |
| 95 to 135 | Lab 2 | Memory. Project the two traces side by side. Ask the room to find the bug in the second one. They cannot. That is the point. |
| 135 to 195 | Lab 3 | MCP. Run as Ben first, then the specs-as-items fault, then the id collision by hand. |
| 195 to 205 | Break | |
| 205 to 240 | Part 5 and close | Everyone writes the stub for one tool of their own. Collect two and read them aloud against the checklist. |

## Pre-session checks

```sh
cd 09-adapters/a-tool-to-producer && uv sync && uv run pytest && uv run scenarios.py --check
CWA_W9A_IMPL=labs uv run pytest tests/test_lab_retriever.py    # should fail: the stubs raise NotImplementedError
uv run python tools/fernway_mcp.py < /dev/null                   # the server starts and exits cleanly
```

The MCP server is a subprocess of the test run; a venue that blocks subprocess spawning or stdio pipes will break Lab 3 and scenarios 04 to 06.

## Checkpoint answers

- **Checkpoint 1.** The capability policy (`capability-policy`, kind `capability_policy`). `obs:2` is superseded by `obs:3`; both have source `mcp:fernway-accounts/get_service_status?region=EU`.
- **Checkpoint 2.** Eight hits, seven items, one near-duplicate reported (`help:exports-faq@2#1`, duplicate of `help:exports-faq@2#0`, which this retriever ranks first). The identical chunks are `help:exports-faq@2#0` and `help:data-export@6#0`; the route kept the FAQ copy because dedupe keeps the highest-ranked item by the slot's fitting rank and the FAQ scored higher. Without node metadata the adapter could not produce `source_version` or `freshness` (and `source` only by parsing the id).
- **Checkpoint 3.** Included lists identical. Scenario 02 has `expired` and `revoked` rows at stage producer; 03 has none. Nothing in 03's trace is wrong. A reviewer would have to read the adapter's SQL, which is why the checklist line "every suppressed entry is reported" is a code-review line and not a trace line.
- **Checkpoint 4.** `producer_slot_not_allowed`; widened, `capability_not_allowed`. With colliding ids, both the adapter's items and the policy's grants are excluded `duplicate_item_id`, so no tool renders at all. As Ben, `cap:list_members` is `capability_not_allowed` at stage producer, reported by the capability policy.
- **Checkpoint 5.** Any real tool. The rows that most often come back empty are `source_version` and "what it cannot know"; both are the conversation to have with whoever owns the tool.

## Stumbles

- Participants filter hits by score in Lab 1, or dedupe the exact copy themselves. Both hide a decision the trace is supposed to show.
- Participants put the live-only WHERE clause in the non-silent path because it is faster. Ask them where the expired rows went.
- Participants emit a tool spec as a `governance.capabilities` item "to be helpful". That is the fault the lab injects on purpose; let the assembler answer them.
- `CWA_W9A_IMPL` unset runs the solution. Check that they set it.
- Cold `uv sync` with LlamaIndex can take minutes. Warm caches before the session (docs/setup.md section 6).
