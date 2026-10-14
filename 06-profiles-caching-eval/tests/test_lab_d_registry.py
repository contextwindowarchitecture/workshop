"""Lab D: the lock and the deployment gate. CWA_W6_IMPL=labs checks yours."""

from __future__ import annotations

import copy
import json

import pytest
from cwa.registry import Registry, RegistryError, lock, profile_digest

import impl
from app import context


def registry(which):
    path = impl.path("registry.lock.json", which)
    assert path.exists(), "run registry.py lock"
    profiles = list(context.profiles(which).values())
    return Registry.from_json(json.loads(path.read_text(encoding="utf-8")), profiles, [context.route_policy()]), profiles


def test_the_lock_loads_and_pins_every_profile_and_the_policy(which):
    reg, profiles = registry(which)
    pinned = json.loads(impl.path("registry.lock.json", which).read_text(encoding="utf-8"))
    assert {(p["id"], p["version"]) for p in profiles} <= {(p["id"], p["version"]) for p in pinned["profiles"]}  # earlier versions stay pinned
    assert reg.route_policy("account-help", "w6/v1")["version"] == "w6/v1"


def test_a_deployment_gets_only_the_evaluated_profile(which):
    reg, profiles = registry(which)
    for profile in profiles:
        if profile["evaluation"]["status"] == "evaluated":
            assert reg.profile(profile["id"], profile["version"], deployment=True)["id"] == profile["id"]
        else:
            with pytest.raises(RegistryError):
                reg.profile(profile["id"], profile["version"], deployment=True)


def test_evaluation_does_not_change_the_digest_but_placement_does(which):
    profile = next(iter(context.profiles(which).values()))
    evaluated = copy.deepcopy(profile)
    evaluated["evaluation"] = {"status": "evaluated", "suite": "x", "date": "2026-01-01", "result": {}, "artifact": "y"}
    assert profile_digest(evaluated) == profile_digest(profile)
    moved = copy.deepcopy(profile)
    moved["placement"].reverse()
    assert profile_digest(moved) != profile_digest(profile)


def test_content_changed_under_an_unchanged_version_is_refused(which):
    pinned = json.loads(impl.path("registry.lock.json", which).read_text(encoding="utf-8"))
    profiles = list(context.profiles(which).values())
    tampered = copy.deepcopy(profiles)
    tampered[0]["placement"].reverse()
    with pytest.raises(RegistryError):
        Registry.from_json(pinned, tampered, [context.route_policy()])
    with pytest.raises(RegistryError):
        lock(tampered, [context.route_policy()], existing=pinned)
