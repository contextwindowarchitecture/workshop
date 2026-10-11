#!/usr/bin/env python3
"""Lab solved: the reference assembler behind the adapter protocol.

Snapshot bytes on stdin. Exit 0 with {"payload": base64 or null, "trace": {...}} on stdout when assembled or refused.
Exit 2 when the snapshot is rejected before assembly, the problems on stderr. Exit 3 when an otherwise valid snapshot
names a tokenizer or renderer this assembler does not provide, with exactly "<component> <id> is not provided" on
stderr. Nothing else is printed to stdout, ever: the harness parses it.
"""

from __future__ import annotations

import base64
import json
import sys

from cwa import Snapshot, SnapshotError, UnsupportedComponentError, assemble


def main() -> int:
    raw = sys.stdin.buffer.read()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"not a JSON document: {error}", file=sys.stderr)
        return 2
    try:
        result = assemble(Snapshot.from_json(document))
    except SnapshotError as error:
        print("; ".join(error.problems), file=sys.stderr)
        return 2
    except UnsupportedComponentError as error:
        print(f"{error.component} {error.id} is not provided", file=sys.stderr)
        return 3
    payload = base64.b64encode(result.payload).decode("ascii") if result.payload is not None else None
    sys.stdout.write(json.dumps({"payload": payload, "trace": result.trace}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
