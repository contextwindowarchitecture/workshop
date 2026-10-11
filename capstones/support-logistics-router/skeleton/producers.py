"""Your producers. The route policies list them with their kinds and slots:

    support_policy(route) -> batch              policy: governance.instructions and governance.output_contract (parser route)
    customer_state(request) -> batch            state: state.user, protected by the route; no contact details in the body
    ticket_state(request, route) -> batch       state: state.task, the ticket's stage and flags, written by the application
    orders_db(request) -> (batch, facts)        state: state.task, the order's status; asserts delivery_status:<order>
    crm_notes(request) -> (batch, facts)        memory: interaction.memory, every note with its summary as a variant,
                                                expires 180 days after the note, scope the note's own customer; a note
                                                with a "fact" asserts it; honour the crm-ignores-customer fault;
                                                redact phone numbers and email addresses from bodies (lineage redacted)
    kb_search(request, top_k) -> batch          retrieval: evidence.knowledge, one scored item per paragraph
    web_chat(request) -> batch                  interaction: history and query

common.py has the data loaders, the corpus and item()/batch(). W2, W3a and W9 module A are the references.
"""

from __future__ import annotations

from typing import Any

from common import Request

Facts = dict[str, str]


def support_policy(route: str) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: support_policy")


def customer_state(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: customer_state")


def ticket_state(request: Request, route: str) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: ticket_state")


def orders_db(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("skeleton/producers.py: orders_db")


def crm_notes(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("skeleton/producers.py: crm_notes")


def kb_search(request: Request, top_k: int) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: kb_search")


def web_chat(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: web_chat")
