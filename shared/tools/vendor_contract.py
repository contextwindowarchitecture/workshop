#!/usr/bin/env python3
"""Copy the published CWA contract from a checkout of the specification repository into shared/contract/cwa/, pinned by SHA-256.

    python3 shared/tools/vendor_contract.py                                   # vendor from the sibling checkout, and rewrite shared/contract/cwa.lock.json
    python3 shared/tools/vendor_contract.py --spec <checkout>                 # the same, naming the checkout
    python3 shared/tools/vendor_contract.py --spec <checkout> --check         # exit 1 when shared/contract/cwa/ drifts from the checkout
    python3 shared/tools/vendor_contract.py --verify                          # exit 1 when shared/contract/cwa/ disagrees with its lock

Adapted from assembler-template/scripts/vendor_contract.py. The workshop repository vendors more than an assembler
needs: the normative text, the guides and the examples too, so every lab can read them offline. The sibling
checkout is resolved by shared/siblings.py, so CWA_SIBLINGS_ROOT applies.

The checkout is github.com/contextwindowarchitecture/contextwindowarchitecture, the contract's source; --spec
defaults to ../contextwindowarchitecture beside this repository. The lock records every vendored file's SHA-256,
the repository the checkout's origin remote names (owner/name on GitHub), the commit it came from as spec_commit,
and whether the vendored sources had uncommitted changes there. Vendor from a committed state: a report against a
dirty commit cannot be listed. The port's own suite re-checks the lock natively (docs/setup.md); --verify is
the same check for CI and for a port that has no suite yet. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "shared" / "contract" / "cwa"
LOCK = ROOT / "shared" / "contract" / "cwa.lock.json"
# The specification repository, as owner/name: where --spec looks by default, and the name the lock records for a
# checkout whose origin remote is missing.
SPEC_REPOSITORY = "contextwindowarchitecture/contextwindowarchitecture"
sys.path.insert(0, str(ROOT / "shared"))
from siblings import sibling  # noqa: E402

DEFAULT_SPEC = sibling("contextwindowarchitecture")
# The contract an assembler needs: the license, the schemas, the contract data, the conformance README, the
# cases and rejection cases, and the registry whose lock lets a port test its RFC 8785 digests.
SOURCES = (
    "LICENSE",
    "NOTICE",
    "SPEC.md",
    "CHANGES.md",
    "schema",
    "contract/requirements.json",
    "contract/reasons.json",
    "contract/slot-defaults.json",
    "contract/model.json",
    "contract/assembler-scope.json",
    "conformance/README.md",
    "conformance/cases",
    "conformance/rejections",
    "conformance/registry",
    "guides",
    "examples",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec_files(spec: Path) -> dict[str, Path]:
    """Every file to vendor, keyed by its path relative to the specification checkout, with / separators."""
    files: dict[str, Path] = {}
    for source in SOURCES:
        root = spec / source
        if not root.exists():
            sys.exit(f"{root} does not exist; is {spec} a checkout of {SPEC_REPOSITORY}?")
        paths = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for path in paths:
            files[path.relative_to(spec).as_posix()] = path
    return files


def git(spec: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(spec), *args], capture_output=True, text=True, check=True).stdout.strip()


def repository_of(url: str) -> str:
    """A remote URL as owner/name when it is on GitHub, over HTTPS or SSH; any other URL as given."""
    m = re.match(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else url


def repository(spec: Path) -> str:
    """The repository the checkout's origin remote names, or SPEC_REPOSITORY when it has no origin."""
    try:
        return repository_of(git(spec, "remote", "get-url", "origin"))
    except subprocess.CalledProcessError:
        print(f"note: {spec} has no origin remote, so the lock names {SPEC_REPOSITORY}", file=sys.stderr)
        return SPEC_REPOSITORY


def source(lock: dict) -> str:
    """Where a lock's files came from, as the messages name it: "<repository> <short sha>", marked when dirty."""
    return f"{lock['repository']} {lock['spec_commit'][:7]}{' (dirty)' if lock['dirty'] else ''}"


def vendored_files() -> dict[str, str]:
    """Every file under shared/contract/cwa/ with its SHA-256, keyed by its vendored path."""
    if not VENDOR.exists():
        return {}
    return {p.relative_to(VENDOR).as_posix(): sha256(p) for p in sorted(VENDOR.rglob("*")) if p.is_file()}


def report(problems: list[str]) -> int:
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


def vendor(spec: Path) -> int:
    files = spec_files(spec)
    if VENDOR.exists():
        shutil.rmtree(VENDOR)
    for rel, src in files.items():
        dest = VENDOR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    lock = {
        "repository": repository(spec),
        "spec_commit": git(spec, "rev-parse", "HEAD"),
        "dirty": git(spec, "status", "--porcelain", "--", *SOURCES) != "",
        "files": {rel: sha256(VENDOR / rel) for rel in sorted(files)},
    }
    LOCK.write_text(json.dumps(lock, indent=2) + "\n")
    print(f"vendored {len(files)} files from {source(lock)}")
    return 0


def check(spec: Path) -> int:
    """Drift between shared/contract/cwa/ and the specification checkout, file for file."""
    files = spec_files(spec)
    have = vendored_files()
    problems = [f"missing: {rel}" for rel in files if rel not in have]
    problems += [f"extra: {rel}" for rel in have if rel not in files]
    problems += [f"differs: {rel}" for rel, src in files.items() if rel in have and have[rel] != sha256(src)]
    if not problems:
        print(f"shared/contract/cwa matches {spec}: {len(have)} files")
    return report(problems)


def verify() -> int:
    """Disagreement between shared/contract/cwa/ and shared/contract/cwa.lock.json."""
    have = vendored_files()
    if not LOCK.exists():
        if not have:
            print("nothing vendored yet: run vendor_contract.py --spec <checkout> (docs/setup.md)")
            return 0
        return report([f"{LOCK} does not exist but shared/contract/cwa/ holds {len(have)} files"])
    lock = json.loads(LOCK.read_text())
    if "spec_commit" not in lock or "repository" not in lock:
        return report([f"{LOCK} names no repository and spec_commit: re-vendor with vendor_contract.py --spec <checkout> (docs/setup.md)"])
    problems = [f"missing: {rel}" for rel in lock["files"] if rel not in have]
    problems += [f"unlocked: {rel}" for rel in have if rel not in lock["files"]]
    problems += [f"hash differs: {rel}" for rel, digest in lock["files"].items() if rel in have and have[rel] != digest]
    if not problems:
        print(f"shared/contract/cwa matches its lock: {len(have)} files from {source(lock)}")
    return report(problems)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC,
                        help=f"a checkout of {SPEC_REPOSITORY}; default: ../contextwindowarchitecture beside this repository")
    parser.add_argument("--check", action="store_true", help="report drift from the checkout instead of vendoring")
    parser.add_argument("--verify", action="store_true", help="check shared/contract/cwa/ against its lock; needs no checkout")
    args = parser.parse_args()
    if args.verify:
        return verify()
    spec = args.spec.resolve()
    return check(spec) if args.check else vendor(spec)


if __name__ == "__main__":
    sys.exit(main())
