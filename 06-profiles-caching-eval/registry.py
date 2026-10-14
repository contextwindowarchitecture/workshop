"""Lab D: the registry lock and the deployment gate (R-19, R-20).

    uv run registry.py lock              # write <impl>/registry.lock.json from the profiles and the route policy
    uv run registry.py check             # load the registry: every digest matches, or the reason it does not
    uv run registry.py deploy cache-first   # what a deployment gets: an evaluated profile, or a refusal

A profile's digest covers everything but its evaluation object, so changing its placement without a version bump
changes it. Promotion sets model_family, which the digest covers, so it writes the next version of the profile (R-20):
lock after promoting. A route policy's digest covers the whole policy. The lock never rewrites an entry; a new version
is a new entry. A deployment asks for a profile with deployment=True and gets only an
evaluated one.
"""

from __future__ import annotations

import argparse
import json
import sys

from cwa.registry import Registry, RegistryError, lock, profile_digest

import impl
from app import context


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["lock", "check", "deploy", "digest"])
    p.add_argument("profile", nargs="?")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    args = p.parse_args(argv)
    profiles = list(context.profiles(args.impl).values())
    policies = [context.route_policy()]
    path = impl.path("registry.lock.json", args.impl)
    if args.command == "lock":
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        try:
            pinned = lock(profiles, policies, existing=existing) if existing else lock(profiles, policies)
        except RegistryError as error:
            print("cannot lock:\n  " + "\n  ".join(error.problems), file=sys.stderr)
            return 1
        path.write_text(json.dumps(pinned, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(impl.HERE)}: {len(pinned['profiles'])} profile(s), {len(pinned['route_policies'])} route polic(y/ies)")
        return 0
    if args.command == "digest":
        for profile in profiles:
            print(f"{profile['id']} v{profile['version']}  {profile_digest(profile)}  [{profile['evaluation']['status']}]")
        return 0
    if not path.exists():
        print(f"{path.relative_to(impl.HERE)} does not exist; run registry.py lock", file=sys.stderr)
        return 1
    try:
        registry = Registry.from_json(json.loads(path.read_text(encoding="utf-8")), profiles, policies)
    except RegistryError as error:
        print("the registry does not load:\n  " + "\n  ".join(error.problems), file=sys.stderr)
        return 1
    if args.command == "check":
        print("the registry loads: every profile and policy matches its pinned digest")
        return 0
    profile = next(pr for pr in profiles if pr["id"] == args.profile)
    try:
        got = registry.profile(profile["id"], profile["version"], deployment=True)
    except RegistryError as error:
        print("deployment refused:\n  " + "\n  ".join(error.problems))
        return 1
    print(f"deployment gets {got['id']} v{got['version']}, evaluated for {got['model_family']} on {got['evaluation']['suite']} ({got['evaluation']['date']}), artifact {got['evaluation']['artifact']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
