#!/usr/bin/env python3
"""The lab: put the reference assembler behind the adapter protocol, so any harness can drive it as a black box.

Write main() until `CWA_W9B_IMPL=labs uv run pytest tests/test_lab_adapter.py` passes and
`uv run harness.py conformance --impl labs` reports every case passed and every rejection rejected.

The protocol (assembler-template/PORTING.md, step 5; conformance/README.md, Running a case):

- Read the snapshot's bytes from stdin. Decode as UTF-8 and parse as JSON; a failure there is a rejection.
- Exit 0 when the assembler assembled or refused. Write exactly one JSON object to stdout:
  {"payload": <base64 of the payload bytes, or null on a refusal>, "trace": <the trace as JSON>}.
- Exit 2 when the snapshot is rejected before assembly (cwa.SnapshotError). Write the problems to stderr, nothing to
  stdout.
- Exit 3 when an otherwise valid snapshot names a tokenizer or renderer this assembler does not provide
  (cwa.UnsupportedComponentError, with .component and .id). stderr must read exactly
  "<component> <id> is not provided", for example "renderer cwa-message-blocks/v2 is not provided".
- Never print anything else to stdout. The harness parses it; a stray log line is a failed case.

Snapshot.from_json(document) validates first and resolves components after, so a snapshot that breaks its schema is
rejected even when it also names a missing component. The three exits are the three kinds of outcome a black-box
runner must tell apart, and the base64 is what keeps the payload's bytes exact through a text channel.
"""

from __future__ import annotations

import sys


def main() -> int:
    raise NotImplementedError("labs/adapter.py: see the module docstring")


if __name__ == "__main__":
    sys.exit(main())
