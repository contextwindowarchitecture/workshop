"""Precompute a summary of every help-centre paragraph, keyed by content hash, before any request (R-18).

    uv run summarize.py --check                 # every paragraph has a summary in summaries/summaries.json
    OPENAI_BASE_URL=... uv run summarize.py     # rewrite summaries.json with a model's summaries (then review them!)

Without an endpoint this script does not write anything: the committed summaries.json is a hand-checked stand-in for
one model run, and four of its entries are deliberately unfaithful so Lab A has something to find. With an endpoint it
asks the model for a one-sentence summary of each paragraph and writes the table; the review list is yours to redo,
because a new summary is an unreviewed summary. The key is the SHA-256 of the paragraph, so an unchanged paragraph
keeps its entry through re-chunking and an edited paragraph has none until this runs again.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import provider
from request import corpus

OUT = Path(__file__).resolve().parent / "summaries" / "summaries.json"
PROMPT = ("Summarise the following help-centre paragraph in one sentence of at most 30 words. State only what the "
          "paragraph states. Do not add, generalise or soften anything.\n\n")


def main(argv: list[str]) -> int:
    table = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    missing = [c for c in corpus.chunks() if hashlib.sha256(c.text.encode("utf-8")).hexdigest() not in table]
    if "--check" in argv:
        print(f"{len(table)} summaries; {len(missing)} paragraph(s) without one" + ("" if not missing else ": " + ", ".join(c.id for c in missing)))
        return 1 if missing else 0
    if not provider.configured():
        print("no OPENAI_BASE_URL: the committed summaries.json stands in for a model run. Set the endpoint to regenerate it.")
        return 2
    model = provider.model()
    for chunk in corpus.chunks():
        key = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        reply = provider.send({"model": model, "messages": [{"role": "user", "content": PROMPT + chunk.text}], "max_tokens": 120})
        table[key] = {"suffix": "summary", "body": (reply or "").strip(), "method": f"model-summary:{model}", "lineage": "summarised"}
        print(f"{chunk.id}: {table[key]['body']}")
    OUT.write_text(json.dumps(dict(sorted(table.items())), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}; now review every entry (uv run review.py) before approving any")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
