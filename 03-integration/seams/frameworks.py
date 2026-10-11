"""Each framework run with a recording model in place of a real one, so the seam can be proven without a model: the
recording is what the framework handed the model, and the payload is what the trace says it should be.

The application decides before the framework starts whether there is anything to send: a refused assembly starts no
run and calls no model (R-17). Each run_* returns what the model received, or None on a refusal.
"""

from __future__ import annotations

import asyncio
from typing import Any

from agents import Agent, RunConfig, Runner
from agents.items import ModelResponse
from agents.models.interface import Model
from agents.run_config import CallModelData, ModelInputData
from agents.usage import Usage
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, wrap_model_call
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph import END, START, MessagesState, StateGraph
from openai.types.responses import ResponseOutputMessage, ResponseOutputText

import common
import seam_impl
from request import Request

ANSWER = "(recorded: no model answered)"


class RecordingModel(Model):
    """An Agents SDK model that records every call and answers with a fixed text."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def get_response(self, system_instructions, input, model_settings, tools, output_schema, handoffs, tracing, *,
                           previous_response_id=None, conversation_id=None, prompt=None) -> ModelResponse:
        self.calls.append({"instructions": system_instructions, "input": list(input) if not isinstance(input, str) else input, "tools": [t.name for t in tools]})
        message = ResponseOutputMessage(id="msg_recorded", role="assistant", status="completed", type="message",
                                        content=[ResponseOutputText(type="output_text", text=ANSWER, annotations=[])])
        return ModelResponse(output=[message], usage=Usage(), response_id=None)

    async def stream_response(self, *args, **kwargs):  # pragma: no cover - the labs never stream
        raise NotImplementedError
        yield


class RecordingChatModel(BaseChatModel):
    """A LangChain chat model that records the messages it is given and answers with a fixed text."""

    calls: list = []

    @property
    def _llm_type(self) -> str:
        return "recording"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.calls.append([(m.type, m.content) for m in messages])
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=ANSWER))])


def _received_agents(call: dict[str, Any]) -> dict[str, Any]:
    items = call["input"] if isinstance(call["input"], list) else [{"role": "user", "content": call["input"]}]
    system = [i["content"] for i in items if i.get("role") == "system"]
    if call["instructions"]:
        system = [call["instructions"], *system]  # whatever instructions returns takes the system role too
    users = [i["content"] for i in items if i.get("role") == "user"]
    return {"system": system, "user": users[-1] if users else "", "tools": call["tools"]}


def _received_chat(call: list[tuple[str, Any]]) -> dict[str, Any]:
    return {"system": [c for t, c in call if t == "system"], "user": [c for t, c in call if t == "human"][-1], "tools": []}


def run_agents_sdk(request: Request, which: str | None = None) -> dict[str, Any] | None:
    """The seam is RunConfig.call_model_input_filter: it runs before every model call and replaces the call's input.
    The agent's own `instructions` must not reach the model, so the filter leaves instructions None."""
    seams = seam_impl.seams(which)
    document, result = common.assemble_context(request)
    if result.payload is None:
        return None
    payload = result.payload

    def seam(data: CallModelData) -> ModelInputData:
        items, instructions = seams.agents_input(payload)
        return ModelInputData(input=items, instructions=instructions)

    model = RecordingModel()
    agent = Agent(name="fernway", instructions="THIS TEXT MUST NEVER REACH THE MODEL", model=model)
    asyncio.run(Runner.run(agent, request.question, run_config=RunConfig(call_model_input_filter=seam, tracing_disabled=True)))
    assert len(model.calls) == 1
    return _received_agents(model.calls[0])


def run_langgraph(request: Request, which: str | None = None) -> dict[str, Any] | None:
    """The seam is the node that turns state into messages. The graph owns order of operations; the node asks the
    assembler for the order of context, and state["messages"] is not the model's input."""
    seams = seam_impl.seams(which)
    document, result = common.assemble_context(request)
    if result.payload is None:
        return None
    payload = result.payload
    model = RecordingChatModel()
    model.calls = []

    def call_model(state: MessagesState):
        return {"messages": [model.invoke(seams.langgraph_messages(payload))]}

    graph = StateGraph(MessagesState)
    graph.add_node("call_model", call_model)
    graph.add_edge(START, "call_model")
    graph.add_edge("call_model", END)
    graph.compile().invoke({"messages": [HumanMessage(request.question)]})
    assert len(model.calls) == 1
    return _received_chat(model.calls[0])


def run_langchain_middleware(request: Request, which: str | None = None) -> dict[str, Any] | None:
    """The same seam in LangChain's create_agent: a wrap_model_call middleware overrides the request's system message
    and messages. The agent's system_prompt must not reach the model; the override replaces it."""
    seams = seam_impl.seams(which)
    document, result = common.assemble_context(request)
    if result.payload is None:
        return None
    payload = result.payload
    model = RecordingChatModel()
    model.calls = []

    @wrap_model_call
    def cwa_seam(req: ModelRequest, handler):
        messages = seams.langgraph_messages(payload)
        system = [m for m in messages if m.type == "system"]
        rest = [m for m in messages if m.type != "system"]
        # create_agent takes one system message; the entries join with the separator the Claude seam also uses.
        joined = type(system[0])("\n\n".join(m.content for m in system)) if system else None
        return handler(req.override(system_message=joined, messages=rest))

    agent = create_agent(model, tools=[], system_prompt="THIS TEXT MUST NEVER REACH THE MODEL", middleware=[cwa_seam])
    agent.invoke({"messages": [HumanMessage(request.question)]})
    assert len(model.calls) == 1
    return _received_chat(model.calls[0])


SEAMS = {"agents-sdk": run_agents_sdk, "langgraph": run_langgraph, "langchain-middleware": run_langchain_middleware}
# Seams whose framework takes one system message: the proof compares against the entries joined with one separator.
JOINS_SYSTEM = {"langchain-middleware"}


def expected_for(seam: str, texts: dict) -> dict:
    return common.joined(texts) if seam in JOINS_SYSTEM else texts
