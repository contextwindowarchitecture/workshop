"""The committed proof: for each W3a scenario, the hash of the payload's texts and what each seam's recording model
received, so a framework upgrade that changes what reaches the model fails the build.

    uv run scenarios.py --check
    uv run scenarios.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import common
import frameworks

PROOF = Path(__file__).parent / "scenarios" / "proof.json"


def names() -> list[str]:
    return ["proof"]


def build() -> bytes:
    out = {}
    for name in common.scenario_names():
        request = common.scenario(name)
        _, result = common.assemble_context(request)
        payload = common.digest(common.texts_of(result.payload)) if result.payload is not None else None
        out[name] = {"payload_texts": payload, "refused": result.trace["refused"]["reason"] if payload is None else None,
                     "received": {seam: (common.digest(r) if (r := run(request, "solution")) is not None else None) for seam, run in frameworks.SEAMS.items()}}
    return (json.dumps(out, indent=2) + "\n").encode("utf-8")


def stale(name: str) -> list[str]:
    return [] if PROOF.exists() and PROOF.read_bytes() == build() else ["proof.json"]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    args = p.parse_args(argv)
    if args.write:
        PROOF.parent.mkdir(exist_ok=True)
        PROOF.write_bytes(build())
        print("wrote scenarios/proof.json")
        return 0
    if stale("proof"):
        print("stale: scenarios/proof.json (run uv run scenarios.py --write, then review the diff)", file=sys.stderr)
        return 1
    print("1 scenario(s) are current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
