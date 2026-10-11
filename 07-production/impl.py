"""Whose telemetry attributes and eval cases run: yours in labs/ or the finished ones in solution/. CWA_W7_IMPL=labs selects yours."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_W7_IMPL", "solution")
    if chosen not in ("labs", "solution"):
        raise SystemExit(f"CWA_W7_IMPL must be labs or solution, not {chosen!r}")
    return chosen


def module(part: str, explicit: str | None = None) -> ModuleType:
    return importlib.import_module(f"{name(explicit)}.{part}")


def path(file: str, explicit: str | None = None) -> Path:
    return HERE / name(explicit) / file
