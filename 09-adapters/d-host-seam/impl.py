"""Whose producers run: yours in labs/ or the finished port in solution/. CWA_W9D_IMPL=labs selects yours."""

from __future__ import annotations

import importlib
import os
from types import ModuleType


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_W9D_IMPL", "solution")
    if chosen not in ("labs", "solution"):
        raise SystemExit(f"CWA_W9D_IMPL must be labs or solution, not {chosen!r}")
    return chosen


def module(part: str, explicit: str | None = None) -> ModuleType:
    return importlib.import_module(f"{name(explicit)}.{part}")
