"""Lab 1, solved: LlamaIndex hits to a retrieval producer batch."""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from common import Batch, Request, batch, item, jaccard, policy


def adapt(hits: list[NodeWithScore], request: Request) -> Batch:
    threshold = policy("assembly.json")["retrieval"]["near_duplicate_jaccard"]
    kept: list[dict] = []
    excluded: list[dict] = []
    for hit in hits:
        node, text = hit.node, hit.node.get_content()
        meta = node.metadata  # the provenance is here only because ingestion put it here
        twin = next((k for k in kept if k["body"] != text and jaccard(k["body"], text) >= threshold), None)
        if twin is not None:
            excluded.append({"item_id": node.node_id, "reason": "duplicate_content", "stage": "producer", "duplicate_of": twin["id"]})
            continue
        kept.append(item(
            id=node.node_id, slot="evidence.knowledge", source=f"help-center:{meta['article']}",
            source_version=str(meta["version"]), authority="reference_only", trust="verified", freshness=meta["updated"],
            relevance=round(float(hit.score or 0.0), 3), lineage="verbatim", injection_risk="untrusted_content", body=text,
        ))
    return batch("help-center-search", "retrieval", kept, excluded)
