"""The retriever you already run: LlamaIndex's BM25Retriever over the Fernway help centre.

This is the tool being wrapped, not the lab. It knows nothing about CWA. It returns what LlamaIndex returns, a list
of NodeWithScore, each with a node id, a score, the paragraph text and whatever metadata was attached at ingestion.
A real pipeline looks like this: the provenance an item needs (article, version, updated) is there only because
someone put it in the node metadata when the index was built, and the adapter's first job is to find it.
"""

from __future__ import annotations

import sys
from functools import cache
from pathlib import Path

from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.retrievers.bm25 import BM25Retriever

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from fernway.corpus import chunks  # noqa: E402


@cache
def nodes() -> tuple[TextNode, ...]:
    return tuple(TextNode(
        id_=chunk.id, text=chunk.text,
        metadata={"article": chunk.article, "title": chunk.title, "version": chunk.version, "updated": chunk.updated},
        excluded_embed_metadata_keys=["article", "version", "updated"],
        excluded_llm_metadata_keys=["article", "title", "version", "updated"],
    ) for chunk in chunks())


@cache
def _retriever() -> BM25Retriever:
    return BM25Retriever.from_defaults(nodes=list(nodes()), similarity_top_k=len(nodes()))


def retrieve(question: str, top_k: int) -> list[NodeWithScore]:
    """The top_k hits, best first. Every node is scored and the order is settled by score then id, so equal scores
    resolve the same way on every machine."""
    hits = _retriever().retrieve(question)
    hits.sort(key=lambda hit: (-(hit.score or 0.0), hit.node.node_id))
    return hits[:top_k]
