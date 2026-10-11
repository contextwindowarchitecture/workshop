"""Lab B: a CWA trace as span attributes.

Write attributes_for(trace) until `CWA_W7_IMPL=labs uv run pytest tests/test_lab_b_telemetry.py` passes. The span is
what an on-call engineer sees in Jaeger or Tempo at three in the morning, and what a tracing vendor stores for a year.
Two rules:

1. Everything that identifies and explains the assembly goes in: the profile id and version, the route policy
   version, the snapshot digest (the link back to the store), the payload hash, the input token count and the budget,
   the refusal reason and recovery action if any, the ids of items included, compressed and excluded with each
   exclusion's reason, and one line per conflict group with how it was decided.
2. Nothing a user wrote or that the application knows about a user goes in. No item body, no question, no answer, no
   name. The digest is enough: whoever is allowed to see the content can fetch the snapshot from the store.

Attribute values must be strings, numbers, booleans, or lists of one of those. Prefix every key with `cwa.`.
"""

from __future__ import annotations

from typing import Any


def attributes_for(trace: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Lab B: see the module docstring")
