"""Resolve the sibling repositories the workshops depend on.

The workshops do not vendor the examples, the assemblers or the website. They expect them checked out beside this
repository, the way assembler-demo and the viability benchmark do, so each repository keeps growing on its own:

    <root>/
      workshop/                     this repository
      contextwindowarchitecture/    the specification; its contract is vendored into shared/contract/
      assembler-python/             the reference assembler, at the tag shared/contract/pins.json names
      assembler-demo/               the inspector, the adapters, the MCP servers
      examples/                     Fernway, the help-center bot and agent the labs build on
      website/                      the pages W0 and W6 use; serve it locally or use the live site
      integrations/                 the fullsend seam W9 module D studies

The root defaults to the parent of this repository. Set CWA_SIBLINGS_ROOT to an absolute or relative path to put the
siblings anywhere else; a relative path is resolved against the current working directory. Standard library only.

    from siblings import sibling, root
    sibling("examples") / "01-docs-qa"

    python3 shared/siblings.py            # print the root and which siblings are present
    python3 shared/siblings.py examples   # print one sibling's path, exit 1 when it is missing
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV = "CWA_SIBLINGS_ROOT"
PINS = REPO / "shared" / "contract" / "pins.json"

# Every sibling a workshop names, and the one line setup.md shows for it.
SIBLINGS = {
    "contextwindowarchitecture": "the specification, source of shared/contract/",
    "assembler-python": "the reference assembler",
    "assembler-demo": "inspector, adapters, MCP servers, scenarios",
    "examples": "Fernway: 01-docs-qa to 05-production and bench",
    "website": "the pages W0 and W6 use (optional: the live site works too)",
    "integrations": "the fullsend seam (W9 module D only)",
}


def root() -> Path:
    """The directory the siblings live in."""
    override = os.environ.get(ENV)
    if override:
        return Path(override).expanduser().resolve()
    return REPO.parent


def sibling(name: str) -> Path:
    """The path a sibling would have, whether or not it is checked out."""
    if name not in SIBLINGS:
        raise KeyError(f"{name!r} is not a sibling this repository names: {', '.join(SIBLINGS)}")
    return root() / name


def require(name: str) -> Path:
    """The path of a sibling that must exist, or a SystemExit that says how to get it."""
    path = sibling(name)
    if not path.is_dir():
        pin = pins().get(name, {}).get("ref", "")
        at = f" at {pin}" if pin else ""
        sys.exit(
            f"{name} is not checked out at {path}{at}.\n"
            f"  git clone git@github.com:contextwindowarchitecture/{name}.git {path}\n"
            f"or set {ENV} to the directory that holds it. See docs/setup.md."
        )
    return path


def pins() -> dict:
    """The tag or commit each sibling should be at, from shared/contract/pins.json."""
    if not PINS.exists():
        return {}
    return json.loads(PINS.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if argv:
        print(require(argv[0]))
        return 0
    print(f"siblings root: {root()}  ({ENV}={'set' if os.environ.get(ENV) else 'unset'})")
    status = 0
    for name, what in SIBLINGS.items():
        path = sibling(name)
        present = path.is_dir()
        print(f"  {'ok     ' if present else 'missing'}  {name:28} {what}")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
