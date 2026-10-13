# The application before CWA

`app.py` is the Fernway account assistant as teams usually write it: one function pastes the instructions, the account line, every memory on file, the five best-scoring help-centre paragraphs and the last six messages into one request. Do not edit this directory. It is the "before" you diff against at the end, and `tests/test_before.py` asserts its failure modes so the contrast stays honest.

Run it:

```sh
uv run python -m before.app --user u_ada "How do I export the whole workspace, including attachments?"
uv run python -m before.app --conversation scenarios/02-ben-plan-conflict/conversation.json
uv run python -m before.app --conversation scenarios/03-off-topic/conversation.json
```

What to notice, with W0's failure modes beside you:

| Failure mode | Where it is in `build_request()` |
| --- | --- |
| Memory that never expires | `memories()` is filtered by user and nothing else: expired and revoked memories go in |
| Stale-as-current | Ben's remembered "Team plan" and the account's "Business plan" sit in the same string with equal standing |
| Instruction-shaped evidence | a help-centre paragraph with an imperative in it would be pasted next to the instructions |
| Displacement under budget | the last six messages, whatever their size; the articles, whatever the budget |
| Missing trigger | the question is the last user message, by convention only |
| Redundant re-reading | the articles change with every question and sit in the system string ahead of the conversation, so everything after them is new to a prompt cache on every call |
| Authority inversion | the account line, the memories and the articles are pasted into the system message, so each carries the instructions' standing |

And what it cannot do: say what it sent, say what it left out, replay a request, or refuse when the help centre has nothing to say. The off-topic conversation sends five irrelevant paragraphs and hopes.
