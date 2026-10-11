"""The screens that run on the draft, outside the model (R-5): no PII, no other customer or order, citations only to
articles that were sent."""

from __future__ import annotations

import re
from dataclasses import dataclass

import common
from common import Request

PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")


@dataclass(frozen=True)
class Decision:
    name: str
    ok: bool
    reason: str


def pii_screen(reply: str) -> Decision:
    for name, pattern in (("phone number", PHONE), ("email address", EMAIL), ("card number", CARD)):
        if pattern.search(reply):
            return Decision("pii_screen", False, f"the reply contains a {name}")
    return Decision("pii_screen", True, "no contact or payment detail in the reply")


def only_this_customer_and_order(reply: str, request: Request) -> Decision:
    lowered = reply.lower()
    for cid, c in common.customers().items():
        if cid != request.customer and (c["name"].lower() in lowered or cid in lowered):
            return Decision("only_this_customer", False, f"the reply mentions another customer ({cid})")
    this_order = common.tickets()[request.ticket]["order"]
    for oid in common.orders():
        if oid != this_order and oid in reply:
            return Decision("only_this_customer", False, f"the reply mentions another order ({oid})")
    return Decision("only_this_customer", True, "the reply names only this customer's ticket and order")


def citations_were_sent(citations: list[str], sent: set[str]) -> Decision:
    missing = [c for c in citations if c not in sent]
    if missing:
        return Decision("citations_were_sent", False, f"cites {missing}, which the request did not contain")
    return Decision("citations_were_sent", True, f"{len(citations)} citation(s), all sent")


def check(reply: str, request: Request, citations: list[str], sent: set[str]) -> list[Decision]:
    return [pii_screen(reply), only_this_customer_and_order(reply, request), citations_were_sent(citations, sent)]
