"""Whose seams run: yours in labs_seams.py or the reference in solution_seams.py. CWA_W3B_IMPL=labs selects yours.

(The modules are flat and the selector is not called impl.py because W3a's impl.py, solution/ and scenarios.py sit one
directory up and share the import path: the seams build on W3a's application.)
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType


def name(explicit: str | None = None) -> str:
    chosen = explicit or os.environ.get("CWA_W3B_IMPL", "solution")
    if chosen not in ("labs", "solution"):
        raise SystemExit(f"CWA_W3B_IMPL must be labs or solution, not {chosen!r}")
    return chosen


def seams(explicit: str | None = None) -> ModuleType:
    return importlib.import_module(f"{name(explicit)}_seams")
