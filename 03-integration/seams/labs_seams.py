"""Your seams. Each turns a cwa-messages/v1 payload into one framework's model input and adds no text of its own.

    agents_input(payload) -> (items, None)                   items: [{"role": "system", "content": ...} per system entry, then the user message]
    langgraph_messages(payload) -> [SystemMessage..., HumanMessage]
    claude_agent_options(payload, reserved_output) -> {"system_prompt", "prompt", "max_turns", "allowed_tools", "separator"}

frameworks.py plugs these into the Agents SDK's RunConfig(call_model_input_filter=...), a LangGraph call_model node and a
LangChain wrap_model_call middleware, each with a recording model in place of a real one, and prove.py compares what the
model received with common.texts_of(payload). solution_seams.py is the reference.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage


def agents_input(payload: bytes) -> tuple[list[dict[str, Any]], None]:
    raise NotImplementedError("labs/seams.py: agents_input")


def langgraph_messages(payload: bytes) -> list[BaseMessage]:
    raise NotImplementedError("labs/seams.py: langgraph_messages")


def claude_agent_options(payload: bytes, reserved_output: int) -> dict[str, Any]:
    raise NotImplementedError("labs/seams.py: claude_agent_options")
