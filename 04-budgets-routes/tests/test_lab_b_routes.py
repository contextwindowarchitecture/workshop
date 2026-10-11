"""Lab B: the routes table and escalation. CWA_W4_IMPL=labs checks yours."""

from __future__ import annotations

from app import app, routes
from tests.conftest import conversation


def test_budget_input_is_computed_from_the_model_limit(which):
    for route in routes.table(which)["routes"]:
        entry = routes.table(which)["routes"][route]
        assert routes.budget(route, which)["input"] == entry["model_context_limit"] - entry["reserved_output"]


def test_the_pasted_log_refuses_on_the_small_route_and_escalates(which):
    made = app.attempts(conversation("03-pasted-log"), which=which)
    assert made[0][0] == "account-help-small" and made[0][2].refused
    assert made[0][2].trace["refused"]["reason"] == "protected_content_over_budget"
    assert len(made) == 2, "the escalate table must send protected_content_over_budget to the large route"
    assert made[1][0] == "account-help" and not made[1][2].refused
    assert made[0][1]["route_policy"]["version"] != made[1][1]["route_policy"]["version"], "each attempt is its own snapshot"


def test_evidence_required_also_escalates(which):
    made = app.attempts(conversation("04-recovery"), which=which, budget_input=400)
    assert made[0][2].trace["refused"]["reason"] == "evidence_required"
    assert len(made) == 2 and not made[-1][2].refused


def test_a_refusal_with_no_escalation_stops(which):
    made = app.attempts(conversation("03-pasted-log"), route="account-help", which=which, budget_input=200)
    assert len(made) == 1 and made[0][2].refused
