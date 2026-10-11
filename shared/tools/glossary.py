#!/usr/bin/env python3
"""Write docs/glossary.md from the website's glossary, so every workshop shares the site's definitions.

    python3 shared/tools/glossary.py            # rewrite docs/glossary.md from the website sibling
    python3 shared/tools/glossary.py --check    # exit 1 when docs/glossary.md is stale

The source is site/glossary.json in the website repository: 49 terms, each with a plain definition, the spec's own
sentence, the page that shows it, and related terms. Standard library only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))
from siblings import require  # noqa: E402

OUT = ROOT / "docs" / "glossary.md"
SITE = "https://contextwindowarchitecture.io/"


def render(entries: list[dict]) -> str:
    lines = [
        "# Glossary",
        "",
        "Generated from the website's `site/glossary.json` by `shared/tools/glossary.py`. Do not edit by hand; "
        "re-run the script after the website changes. Each entry gives the plain meaning, then the specification's "
        "own words, then where the site shows it.",
        "",
    ]
    for e in sorted(entries, key=lambda e: e["term"].lower()):
        lines.append(f"## {e['term']}")
        lines.append("")
        lines.append(e["plain"].strip())
        if e.get("spec"):
            lines.append("")
            lines.append(f"> {e['spec'].strip()}")
        where = e.get("where") or {}
        if where.get("page"):
            anchor = f"#{where['anchor']}" if where.get("anchor") else ""
            label = where.get("label") or where["page"]
            lines.append("")
            lines.append(f"Where: [{label}]({SITE}{where['page']}{anchor})")
        if e.get("related"):
            lines.append("")
            lines.append("Related: " + ", ".join(f"`{r}`" for r in e["related"]))
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    source = require("website") / "site" / "glossary.json"
    text = render(json.loads(source.read_text(encoding="utf-8")))
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"{OUT.relative_to(ROOT)} is stale; run shared/tools/glossary.py")
            return 1
        print(f"{OUT.relative_to(ROOT)} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
