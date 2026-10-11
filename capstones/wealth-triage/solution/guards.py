"""The screens that run on the parsed draft, outside the model (R-5): every action was offered, a trade stays within
the ledger, stated figures are the ledger's, no account identifier leaks, urgency never undercuts the risk screen, and
citations name paragraphs that were sent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import common
from common import Request

IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b")
ACCOUNT = re.compile(r"\bacct_\d+\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
URGENCY = ["low", "normal", "high", "critical"]
RISK_TO_URGENCY = {"low": "low", "elevated": "high", "critical": "critical"}


@dataclass(frozen=True)
class Decision:
    name: str
    ok: bool
    reason: str


def actions_were_offered(actions: list[dict[str, Any]], granted: set[str]) -> Decision:
    for a in actions:
        if a.get("tool") not in granted:
            never = common.capabilities_policy().get("never", {})
            why = f": {never[a['tool']]}" if a.get("tool") in never else ""
            return Decision("actions_were_offered", False, f"the draft calls {a.get('tool')}, which was not offered on this route{why}")
    return Decision("actions_were_offered", True, f"{len(actions)} action(s), all offered")


def trade_guard(actions: list[dict[str, Any]], request: Request) -> Decision:
    acct = common.ledger()["accounts"][request.account]
    held = {p["symbol"]: p["units"] for p in acct["positions"]}
    for a in actions:
        if a.get("tool") != "place_trade":
            continue
        args = a.get("arguments", {})
        if args.get("client") != request.client:
            return Decision("trade_guard", False, "the order names another client")
        if args.get("side") == "sell":
            if args.get("symbol") not in held:
                return Decision("trade_guard", False, f"the order sells {args.get('symbol')}, which the ledger does not hold")
            if not isinstance(args.get("quantity"), int) or args["quantity"] > held[args["symbol"]]:
                return Decision("trade_guard", False, f"the order sells {args.get('quantity')} {args.get('symbol')}; the ledger holds {held[args['symbol']]} settled units")
    return Decision("trade_guard", True, "every order is this client's and within the ledger's settled units")


def figures_match_ledger(figures: list[dict[str, Any]], request: Request) -> Decision:
    acct = common.ledger()["accounts"][request.account]
    held = {p["symbol"]: p["units"] for p in acct["positions"]}
    for f in figures:
        if f.get("symbol") not in held:
            return Decision("figures_match_ledger", False, f"the answer states a position in {f.get('symbol')}, which the ledger does not hold")
        if f.get("units") != held[f["symbol"]]:
            return Decision("figures_match_ledger", False, f"the answer states {f.get('units')} units of {f['symbol']}; the ledger holds {held[f['symbol']]}")
    return Decision("figures_match_ledger", True, f"{len(figures)} stated position(s), all the ledger's")


def no_account_identifiers(text: str) -> Decision:
    for name, pattern in (("IBAN", IBAN), ("account number", ACCOUNT), ("card number", CARD)):
        if pattern.search(text):
            return Decision("no_account_identifiers", False, f"the reply contains an {name}" if name == "IBAN" else f"the reply contains a {name}")
    return Decision("no_account_identifiers", True, "no account identifier in the reply")


def urgency_covers_risk(urgency: str, risk: str) -> Decision:
    floor = RISK_TO_URGENCY.get(risk, "low")
    if urgency not in URGENCY:
        return Decision("urgency_covers_risk", False, f"urgency {urgency!r} is not one of {URGENCY}")
    if URGENCY.index(urgency) < URGENCY.index(floor):
        return Decision("urgency_covers_risk", False, f"urgency {urgency} is below the risk screen's floor {floor} (risk {risk})")
    return Decision("urgency_covers_risk", True, f"urgency {urgency} is at or above the risk screen's floor {floor}")


def citations_were_sent(citations: list[str], sent: set[str]) -> Decision:
    missing = [c for c in citations if c not in sent]
    if missing:
        return Decision("citations_were_sent", False, f"cites {missing}, which the request did not contain")
    return Decision("citations_were_sent", True, f"{len(citations)} citation(s), all sent")


def check(parsed: dict[str, Any], request: Request, route: str, sent: set[str], granted: set[str], risk: str) -> list[Decision]:
    actions = parsed.get("actions") or []
    text = parsed.get("answer") or parsed.get("summary") or ""
    decisions = [citations_were_sent(parsed.get("citations", []), sent), actions_were_offered(actions, granted), no_account_identifiers(text)]
    if route == "portfolio":
        decisions += [trade_guard(actions, request), figures_match_ledger(parsed.get("figures") or [], request)]
    else:
        decisions.append(urgency_covers_risk(parsed.get("urgency", ""), risk))
    return decisions
