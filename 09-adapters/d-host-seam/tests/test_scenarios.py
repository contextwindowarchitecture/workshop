from __future__ import annotations

import scenarios


def test_the_committed_scenario_is_what_the_solution_builds_now():
    assert [f for n in scenarios.names() for f in scenarios.stale(n)] == []
