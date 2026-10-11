"""Lab 1: wrap the LlamaIndex retriever as the help-center-search producer.

The tool is tools/llama_retriever.py and you do not change it. `retrieve(question, top_k)` returns LlamaIndex's
NodeWithScore objects: `hit.score`, `hit.node.node_id`, `hit.node.get_content()`, `hit.node.metadata` (a dict with
article, title, version, updated). Write adapt() until `CWA_W9A_IMPL=labs uv run pytest tests/test_lab_retriever.py`
passes and `uv run run.py --impl labs --user u_ada "How do I export the whole workspace, including attachments?"`
shows your chunks admitted.

An adapter's duties, in order (guides/producers.md, R-13, R-10, R-18):

1. One item per hit, never a merged blob. Fields: id = the node id; slot evidence.knowledge; authority
   reference_only; trust verified; lineage verbatim; injection_risk untrusted_content (the help centre is yours and
   the text is still data); body = the node's content.
2. Provenance from the tool's own identifiers. source = f"help-center:{metadata['article']}" so an article's
   chunks share a source and the route's max_per_source can see them; source_version = the metadata version, as a
   string; freshness = the metadata's updated. If the metadata were missing, the adapter could not make a conformant
   item, and that is a finding about the ingestion pipeline, not something to paper over.
3. relevance = the hit's score, rounded to 3 places. Do not filter by it. Note that this retriever ranks the
   exports FAQ's word-for-word copy above the data-export original; the route's dedupe will keep the higher-ranked
   one, and the trace will show you which.
4. Drop near-duplicates you can see and report each one: compare with the items you have kept using
   `common.jaccard`; at or above the route's near_duplicate_jaccard (policy/assembly.json) and not identical, do not
   emit it, and add {"item_id", "reason": "duplicate_content", "stage": "producer", "duplicate_of": <kept id>}
   to excluded. Identical bodies stay in: the route sets dedupe: exact (R-24).
5. Return common.batch("help-center-search", "retrieval", items, excluded). The application binds the identity.
"""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from common import Batch, Request


def adapt(hits: list[NodeWithScore], request: Request) -> Batch:
    raise NotImplementedError("Lab 1: see the module docstring")
