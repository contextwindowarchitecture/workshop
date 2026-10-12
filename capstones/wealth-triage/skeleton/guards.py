"""Your screens, run on the parsed draft outside the model (R-5):

    actions_were_offered(actions, granted) -> Decision       every action's tool is in the set the final request offered (cap ids without "cap:") and its arguments match that tool's input_schema in data/tools.json
    trade_guard(actions, request) -> Decision                a place_trade names this client, and a sell is of a held symbol for no more than the ledger's units
    figures_match_ledger(figures, request) -> Decision       every stated position is a ledger holding with the ledger's units; a CASH entry is the ledger's cash
    no_account_identifiers(text) -> Decision                 no IBAN, acct_ number or card number in the reply
    urgency_covers_risk(urgency, risk) -> Decision           urgency is one of low/normal/high/critical and not below the risk screen's floor
                                                             (low -> low, elevated -> high, critical -> critical)
    citations_were_sent(citations, sent) -> Decision         every cited paragraph id was in the final request
    check(parsed, request, route, sent, granted, risk) -> list[Decision]   citations, offered and identifiers on both routes; trade and
                                                             figures on portfolio; urgency on triage

A failing decision makes the orchestrator withhold the draft and route the request to an advisor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from common import Request


@dataclass(frozen=True)
class Decision:
    name: str
    ok: bool
    reason: str


def actions_were_offered(actions: list[dict[str, Any]], granted: set[str]) -> Decision:
    raise NotImplementedError("skeleton/guards.py: actions_were_offered")


def trade_guard(actions: list[dict[str, Any]], request: Request) -> Decision:
    raise NotImplementedError("skeleton/guards.py: trade_guard")


def figures_match_ledger(figures: list[dict[str, Any]], request: Request) -> Decision:
    raise NotImplementedError("skeleton/guards.py: figures_match_ledger")


def no_account_identifiers(text: str) -> Decision:
    raise NotImplementedError("skeleton/guards.py: no_account_identifiers")


def urgency_covers_risk(urgency: str, risk: str) -> Decision:
    raise NotImplementedError("skeleton/guards.py: urgency_covers_risk")


def citations_were_sent(citations: list[str], sent: set[str]) -> Decision:
    raise NotImplementedError("skeleton/guards.py: citations_were_sent")


def check(parsed: dict[str, Any], request: Request, route: str, sent: set[str], granted: set[str], risk: str) -> list[Decision]:
    actions = parsed.get("actions") or []
    text = parsed.get("answer") or parsed.get("summary") or ""
    decisions = [citations_were_sent(parsed.get("citations", []), sent), actions_were_offered(actions, granted), no_account_identifiers(text)]
    if route == "portfolio":
        decisions += [trade_guard(actions, request), figures_match_ledger(parsed.get("figures") or [], request)]
    else:
        decisions.append(urgency_covers_risk(parsed.get("urgency", ""), risk))
    return decisions
