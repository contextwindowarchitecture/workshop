#!/usr/bin/env python3
"""Two rules every participant-facing file obeys: never assemble, never patch an assembler's output.

Both rules come from the examples repository. Assembly belongs to a conformant assembler, so workshop code calls
`assemble(snapshot)` and nothing else decides what the model reads; and a payload is handed to the provider exactly
as rendered, so nothing concatenates, inserts into or rewrites it after assembly. The lint is deliberately crude: it
flags the patterns that most often mean one of the rules is being broken, and a file that needs one of them for a
good reason names the reason on the same line with `# cwa-lint: allow`.

    python3 shared/tools/lint_no_assemble.py          # every .py under the workshop directories
    python3 shared/tools/lint_no_assemble.py 03       # one workshop

Standard library only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKSHOP_GLOBS = ("[0-9][0-9]-*", "capstones/*")
ALLOW = "# cwa-lint: allow"

# (pattern, what it usually means)
RULES = (
    (re.compile(r"\bsystem_prompt\s*(\+=|=\s*f?[\"'].*\{)"), "a prompt string is being built by hand; emit items into slots instead"),
    (re.compile(r"\bpayload\s*(\+=|\.replace\(|\.format\()"), "the rendered payload is being changed after assembly"),
    (re.compile(r"\bpayload\[[\"']messages[\"']\]\.(append|insert|extend)\("), "a message is being added to the rendered payload"),
    (re.compile(r"\bpayload\[[\"']system[\"']\]\s*(\+=|=)"), "the rendered system text is being changed after assembly"),
    (re.compile(r"\bdef\s+assemble\s*\("), "participant code defines its own assemble(); use the assembler's"),
    (re.compile(r"\bimport\s+tiktoken\b.*fixture-|tokenizer\s*=\s*[\"'](estimate-utf8|fixture-whitespace)/v1[\"'].*\bdef\b"), "an application tokenizer under a published id (R-16)"),
)


def files(prefixes: list[str]) -> list[Path]:
    out: list[Path] = []
    for pattern in WORKSHOP_GLOBS:
        for top in sorted(ROOT.glob(pattern)):
            rel = top.relative_to(ROOT).as_posix()
            if prefixes and not any(rel.startswith(p) for p in prefixes):
                continue
            for path in sorted(top.rglob("*.py")):
                if any(part in {".venv", "node_modules", "__pycache__"} for part in path.parts):
                    continue
                out.append(path)
    return out


def main(argv: list[str]) -> int:
    problems = 0
    for path in files(argv):
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ALLOW in line:
                continue
            for rule, meaning in RULES:
                if rule.search(line):
                    problems += 1
                    print(f"{path.relative_to(ROOT)}:{n}: {meaning}\n    {line.strip()}")
    print(f"{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
