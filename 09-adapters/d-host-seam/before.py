"""What the triage agent gets today: the pinned agent definition, the constant prompt, and the one tool result it then
reads for itself, in which a maintainer, a drive-by commenter, fullsend's own earlier comment and an instruction hidden
in the issue body all arrive together, with nothing marking whose words may direct it.

    uv run before.py
"""

from __future__ import annotations

import briefing


def page(r: dict) -> str:
    iss = r["issue"]
    lines = [f"# {r['agent']['name']}: what the agent gets today", "",
             f"Agent definition: {r['agent']['source']} at {r['agent']['sha']}, pinned in .fullsend/config.yaml.",
             "Prompt: Run the agent task", "",
             f"Everything else the agent reads for itself. `gh issue view {iss['number']} --comments` returns one result:", "",
             f"title:\t{iss['title']}", f"state:\t{iss['state']}", f"author:\t{iss['author']}", f"labels:\t{', '.join(iss['labels'])}", "--", iss["body"]]
    for c in r["comments"]:
        lines += ["--", f"{c['author']} • {c['created_at']}", c["body"]]
    lines += ["", "No source today for: the duplicate candidates, the earlier run's conclusion, the requester's permission."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(page(briefing.read()), end="")
