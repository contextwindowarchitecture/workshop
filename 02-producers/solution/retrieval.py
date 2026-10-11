"""Lab A, solved: the help-center-search producer, kind retrieval, slot evidence.knowledge."""

from __future__ import annotations

import json

from common import DATA, Batch, Request, batch, bm25, content_hash, item, jaccard, policy


def variants_for(text: str) -> list[dict]:
    """The precomputed shorter forms of this text, looked up by content hash (R-18). Written ahead of time by
    variants.py; a producer never writes a variant during a request."""
    table = json.loads((DATA / "variants.json").read_text(encoding="utf-8"))
    return [dict(v) for v in table.get(content_hash(text), [])]


def help_center_search(request: Request) -> Batch:
    settings = policy("assembly.json")["retrieval"]
    kept: list[dict] = []
    excluded: list[dict] = []
    for chunk, score in bm25(request.question)[: settings["top_k"]]:
        # Rerank is the producer's stage; dropping a near-duplicate is reported, never silent (R-13). Exact copies
        # are left for the route's dedupe: exact, so the trace shows both decisions side by side (R-24).
        twin = next((k for k in kept if k["body"] != chunk.text
                     and jaccard(k["body"], chunk.text) >= settings["near_duplicate_jaccard"]), None)
        if twin is not None:
            excluded.append({"item_id": chunk.id, "reason": "duplicate_content", "stage": "producer", "duplicate_of": twin["id"]})
            continue
        kept.append(item(
            id=chunk.id, slot="evidence.knowledge", source=f"help-center:{chunk.article}", source_version=chunk.version,
            authority="reference_only", trust="verified", freshness=chunk.updated, relevance=score,
            lineage="verbatim", injection_risk="untrusted_content", body=chunk.text,
            variants=[{"id": f"{chunk.id}~{v['suffix']}", "body": v["body"], "method": v["method"], "lineage": v["lineage"]}
                      for v in variants_for(chunk.text)],
        ))
    return batch("help-center-search", "retrieval", kept, excluded)
