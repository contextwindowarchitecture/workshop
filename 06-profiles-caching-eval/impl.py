"""Whose profiles and registry lock the tools read: yours in labs/ or the finished ones in solution/. CWA_W6_IMPL=labs selects yours."""

from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_W6_IMPL", "solution")
    if chosen not in ("labs", "solution"):
        raise SystemExit(f"CWA_W6_IMPL must be labs or solution, not {chosen!r}")
    return chosen


def path(file: str, explicit: str | None = None) -> Path:
    return HERE / name(explicit) / file
