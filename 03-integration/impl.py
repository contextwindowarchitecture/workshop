"""Which application the tests exercise: your migration in after/ or the finished one in solution/.

    CWA_W3_IMPL=after uv run pytest     # your work
    uv run pytest                        # the solution; what CI runs
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_W3_IMPL", "solution")
    if chosen not in ("after", "solution"):
        raise SystemExit(f"CWA_W3_IMPL must be after or solution, not {chosen!r}")
    return chosen


def module(part: str, explicit: str | None = None) -> ModuleType:
    return importlib.import_module(f"{name(explicit)}.{part}")
