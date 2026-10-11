"""Write data/variants.json: a shorter form of every chunk, computed ahead of time and keyed by content hash (R-18).

    uv run variants.py            # rewrite data/variants.json
    uv run variants.py --check    # exit 1 when it is stale

Assembly never calls a model, so anything shorter an item might be swapped for has to exist before the request. Here
the shorter form is the chunk's first sentence, which is an extraction, not a summary, so its lineage is `extracted`.
A real producer would precompute model-written summaries the same way, review them, and store them under the same
key; W4 does that. The key is the SHA-256 of the body, so an edited paragraph gets no variant until it is recomputed,
and an unchanged paragraph keeps its variant through any re-chunking.
"""

from __future__ import annotations

import json
import re
import sys

from common import DATA, chunks, content_hash

OUT = DATA / "variants.json"
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def lead_sentence(text: str) -> str | None:
    sentences = _SENTENCE_END.split(text.strip())
    return sentences[0] if len(sentences) > 1 else None  # a one-sentence chunk has nothing shorter


def table() -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for chunk in chunks():
        lead = lead_sentence(chunk.text)
        if lead:
            out[content_hash(chunk.text)] = [{"suffix": "lead", "body": lead, "method": "lead-sentence", "lineage": "extracted"}]
    return dict(sorted(out.items()))


def main(argv: list[str]) -> int:
    text = json.dumps(table(), indent=2, ensure_ascii=False) + "\n"
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("data/variants.json is stale; run uv run variants.py", file=sys.stderr)
            return 1
        print("data/variants.json is current")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(DATA.parent)}: {len(table())} variants")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
