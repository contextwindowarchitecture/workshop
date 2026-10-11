# W9 module C run sheet

Module: [09-adapters/c-provider/README.md](../../09-adapters/c-provider/README.md). Half a day self-paced; three hours instructor-led; 60 minutes as a conference cut. Model-free; sending is optional.

## Timing, instructor-led

| Minutes | Part | What you do |
| --- | --- | --- |
| 0 to 10 | Framing | "The adapter adds nothing." The IR's three channels on one slide. |
| 10 to 30 | Part 1 | `send.py` for both renderers; point at the two equal hashes. |
| 30 to 90 | The lab | Four functions. Watch for a separator slipped between blocks. |
| 90 to 100 | Break | |
| 100 to 130 | Part 3 | The Anthropic mapping with and without the breakpoint; diff the texts. |
| 130 to 150 | Close | Which provider each participant will add, and what their snippet generator will show their reviewers. |

## Pre-session checks

```sh
cd 09-adapters/c-provider && uv sync && uv run pytest && uv run payloads.py
CWA_W9C_IMPL=labs uv run pytest -q 2>&1 | tail -1     # the stub fails
```

## Checkpoint answers

- **Checkpoint 1.** System entries become system messages in order; tools entries become function definitions; the one user message stays the one user message; blocks join with nothing between. The equal hashes prove the adapter added, removed and changed no text, so the trace's count and hash describe the request.
- **Checkpoint 2.** Both yes; `max_tokens` is the route's `reserved_output`.
- **Checkpoint 3.** Any block boundary after the stable prefix; the texts do not change at all.

## Stumbles

- Participants merge the system entries into one message "because some servers only honour the first". The demo's chat-completions adapter does that and says so; it is a defensible choice, but the test here wants them separate so the mapping is visible. Discuss rather than overrule.
- Participants put the tool entries' text into the system message. Tools are a channel of their own.
- Participants add "Answer in JSON" or similar to the user message. That is text, and it is the output contract's job, placed by the profile.
