"""Did the framework hand the model exactly the payload? For every W3a scenario and every seam, with no model.

    uv run prove.py                      # a table: scenario, payload hash, and for each seam whether the recording equals it
    CWA_W3B_IMPL=labs uv run prove.py    # your seams
"""

from __future__ import annotations

import sys

import common
import frameworks
import seam_impl


def prove(name: str, which: str | None = None) -> dict[str, object]:
    request = common.scenario(name)
    document, result = common.assemble_context(request)
    row: dict[str, object] = {"scenario": name, "refused": result.trace["refused"]["reason"] if result.payload is None else None,
                              "payload": common.digest(common.texts_of(result.payload)) if result.payload is not None else None, "seams": {}}
    for seam, run in frameworks.SEAMS.items():
        received = run(request, which)
        if result.payload is None:
            row["seams"][seam] = "no call" if received is None else "CALLED THE MODEL"
        else:
            want = common.digest(frameworks.expected_for(seam, common.texts_of(result.payload)))
            row["seams"][seam] = ("same" if seam not in frameworks.JOINS_SYSTEM else "same, joined") if received is not None and common.digest(received) == want else "DIFFERS"
    return row


def main() -> int:
    which = seam_impl.name()
    bad = 0
    print(f"{'scenario':<24}{'payload texts':<16}" + "".join(f"{s:>22}" for s in frameworks.SEAMS))
    for name in common.scenario_names():
        try:
            row = prove(name, which)
        except NotImplementedError as todo:
            print(f"not written yet: {todo}")
            return 2
        label = f"refused {row['refused']}" if row["refused"] else str(row["payload"])[:12]
        print(f"{name:<24}{label:<16}" + "".join(f"{row['seams'][s]:>22}" for s in frameworks.SEAMS))
        bad += sum(1 for v in row["seams"].values() if v not in ("same", "same, joined", "no call"))
    print(f"\n{'every seam handed the model the payload, and none was called on a refusal' if not bad else str(bad) + ' seam(s) differ'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
