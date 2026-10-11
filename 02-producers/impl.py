"""Which producers to run: yours in labs/ or the finished ones in solution/.

    CWA_W2_IMPL=labs uv run pytest        # test your work
    uv run pytest                         # the solution; what CI runs
    uv run freeze.py --impl labs ...
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_W2_IMPL", "solution")
    if chosen not in ("labs", "solution"):
        raise SystemExit(f"CWA_W2_IMPL must be labs or solution, not {chosen!r}")
    return chosen


def module(lab: str, explicit: str | None = None) -> ModuleType:
    return importlib.import_module(f"{name(explicit)}.{lab}")
