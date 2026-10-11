"""Your screens, run on the parsed draft outside the model (R-5):

    pii_screen(reply) -> Decision                       no phone number, email address or card number in the reply
    only_this_customer_and_order(reply, request)        no other customer's name or id, no other order id
    citations_were_sent(citations, sent) -> Decision    every cited article id was in the final request
    check(reply, request, citations, sent) -> list[Decision]

A failing decision makes the orchestrator withhold the draft and route the ticket to an agent."""

from __future__ import annotations

from dataclasses import dataclass

from common import Request


@dataclass(frozen=True)
class Decision:
    name: str
    ok: bool
    reason: str


def pii_screen(reply: str) -> Decision:
    raise NotImplementedError("skeleton/guards.py: pii_screen")


def only_this_customer_and_order(reply: str, request: Request) -> Decision:
    raise NotImplementedError("skeleton/guards.py: only_this_customer_and_order")


def citations_were_sent(citations: list[str], sent: set[str]) -> Decision:
    raise NotImplementedError("skeleton/guards.py: citations_were_sent")


def check(reply: str, request: Request, citations: list[str], sent: set[str]) -> list[Decision]:
    return [pii_screen(reply), only_this_customer_and_order(reply, request), citations_were_sent(citations, sent)]
