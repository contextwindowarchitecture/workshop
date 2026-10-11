#!/usr/bin/env python3
"""Every relative link in the repository's Markdown resolves to a file or directory.

    python3 shared/tools/check_links.py            # exit 1 and list the broken links otherwise
    python3 shared/tools/check_links.py docs 09    # only files whose path starts with these

External links (http, https, mailto) are not fetched. The vendored contract, virtual environments, the kata's scratch
trees and node_modules are skipped. Standard library only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".venv", "node_modules", "__pycache__", "work", ".pristine", ".git", ".scratch"}
SKIP_PREFIXES = ("shared/contract/cwa",)
LINK = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")


def markdown_files(prefixes: list[str]) -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts) or str(rel).startswith(SKIP_PREFIXES):
            continue
        if prefixes and not any(str(rel).startswith(p) for p in prefixes):
            continue
        out.append(path)
    return out


def broken(path: Path) -> list[str]:
    found = []
    for m in LINK.finditer(path.read_text(encoding="utf-8")):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (path.parent / target).exists():
            found.append(target)
    return found


def main(argv: list[str]) -> int:
    files = markdown_files(argv)
    problems = [(path.relative_to(ROOT), t) for path in files for t in broken(path)]
    for rel, target in problems:
        print(f"  {rel}: {target}")
    print(f"{len(files)} markdown file(s), {len(problems)} broken relative link(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
