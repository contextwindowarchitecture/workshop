"""The seam in each framework: the function that turns an assembled payload into the input the framework's model call
takes, adding no text of its own. Everything the framework does after that is the framework's.

    agents_input(payload)           OpenAI Agents SDK: the input list for RunConfig(call_model_input_filter=...), instructions None
    langgraph_messages(payload)     LangGraph / LangChain: the messages a call_model node (or a wrap_model_call middleware) sends
    claude_agent_options(payload)   Claude Agent SDK: system_prompt and the prompt string, the two places the SDK takes text
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

SYSTEM_SEPARATOR = "\n\n"


def agents_input(payload: bytes) -> tuple[list[dict[str, Any]], None]:
    """Each system entry becomes a system item and the one user message a user item; `instructions` is None, because
    whatever the agent's instructions callable returns takes the system role, which only governance may take."""
    rendered = json.loads(payload)
    items = [{"role": "system", "content": e["text"]} for e in rendered.get("system", [])]
    items += [{"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else "".join(b["text"] for b in m["content"])}
              for m in rendered["messages"]]
    return items, None


def langgraph_messages(payload: bytes) -> list[BaseMessage]:
    """One SystemMessage per system entry, then the user message. The node ignores state["messages"] as the model's
    input: the snapshot already holds the history it admitted, as interaction.history items."""
    rendered = json.loads(payload)
    messages: list[BaseMessage] = [SystemMessage(e["text"]) for e in rendered.get("system", [])]
    for m in rendered["messages"]:
        content = m["content"] if isinstance(m["content"], str) else "".join(b["text"] for b in m["content"])
        messages.append(HumanMessage(content))
    return messages


def claude_agent_options(payload: bytes, reserved_output: int) -> dict[str, Any]:
    """The SDK takes text in two places: ClaudeAgentOptions.system_prompt and the prompt given to query(). The system
    entries join with one separator, the only text added, and the user message is the prompt. Tools stay with the
    host's allowed_tools, enforced outside the model (R-5); the payload's tool entries are not handed over here."""
    rendered = json.loads(payload)
    system = SYSTEM_SEPARATOR.join(e["text"] for e in rendered.get("system", []))
    prompt = rendered["messages"][0]["content"]
    return {"system_prompt": system, "prompt": prompt if isinstance(prompt, str) else "".join(b["text"] for b in prompt),
            "max_turns": 1, "allowed_tools": [], "separator": SYSTEM_SEPARATOR}
