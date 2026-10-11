"""Your producers. The route policies list them with their kinds and slots:

    advice_policy(route) -> batch                   policy: governance.instructions and governance.output_contract (parser route)
    client_state(request) -> batch                  state: state.user, mandate, risk tier, KYC; protected by the route; no account identifiers
    ledger(request) -> (batch, facts)               state: state.task, settled positions and cash from the custodian; asserts position.ACME
    risk_level(request) -> (level, signals)         the deterministic risk screen: device, amounts of 5,000 or more, moving money; critical when
                                                    a new device meets another signal, elevated on any signal, else low
    risk_screen(request) -> batch                   state: state.task, the level and its signals as application-written state
    market_data(request) -> (batch, facts)          retrieval: evidence.tool_results, the vendor's quotes and its position estimate, which asserts
                                                    position.ACME and loses to the ledger
    kb_search(request, top_k) -> batch              retrieval: evidence.knowledge, one scored item per paragraph
    capability_policy(request) -> (batch, grant)    capability_policy: the portal's proposed tools granted by mandate and risk level, the rest
                                                    reported capability_not_allowed; the grant names the allowed ids
    chat_session(request) -> batch                  interaction: history and query

common.py has the data loaders, the corpus and item()/batch(). W2, W5, W6 and W9 module A are the references.
"""

from __future__ import annotations

from typing import Any

from common import Request

Facts = dict[str, str]


def advice_policy(route: str) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: advice_policy")


def client_state(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: client_state")


def ledger(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("skeleton/producers.py: ledger")


def risk_level(request: Request) -> tuple[str, list[str]]:
    raise NotImplementedError("skeleton/producers.py: risk_level")


def risk_screen(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: risk_screen")


def market_data(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("skeleton/producers.py: market_data")


def kb_search(request: Request, top_k: int) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: kb_search")


def capability_policy(request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    raise NotImplementedError("skeleton/producers.py: capability_policy")


def chat_session(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: chat_session")
