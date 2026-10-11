"""Whose application runs: your team's in skeleton/ or the reference in solution/. CWA_C2_IMPL=skeleton selects yours."""

from __future__ import annotations

import importlib
import os
from types import ModuleType


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_C2_IMPL", "solution")
    if chosen not in ("skeleton", "solution"):
        raise SystemExit(f"CWA_C2_IMPL must be skeleton or solution, not {chosen!r}")
    return chosen


def module(part: str, explicit: str | None = None) -> ModuleType:
    return importlib.import_module(f"{name(explicit)}.{part}")
