"""Lab A: the help-center-search producer. Kind retrieval, slot evidence.knowledge.

Fill in help_center_search() until `CWA_W2_IMPL=labs uv run pytest tests/test_lab_a.py` passes and
`uv run freeze.py --impl labs --user u_ada "How do I export the whole workspace, including attachments?"` shows your chunks admitted.

What a conformant retrieval producer does (guides/producers.md, R-13, R-18, R-10):

1. Retrieve and rerank before assembly. `common.bm25(request.question)` returns every chunk with its score, best
   first; take the route's top_k from policy/assembly.json.
2. Package one item per chunk. Never a merged blob. Each item needs the eight required fields (id, slot, source,
   source_version, authority, freshness, trust, body), the score in `relevance`, authority `reference_only`,
   lineage `verbatim`, and `injection_risk: untrusted_content`, because retrieved text is data even when the
   help centre is yours. `source` is the document (`help-center:<article>`), so chunks of one article share it and
   the route's max_per_source can see them. `common.item(...)` fills the policy fields you do not set.
3. Drop your own near-duplicates and report each one. Compare a candidate with the chunks you have already kept
   using `common.jaccard`; when the overlap is at or above the route's near_duplicate_jaccard but the bodies are not
   identical, do not emit it. Add `{"item_id": <dropped id>, "reason": "duplicate_content", "stage": "producer",
   "duplicate_of": <kept id>}` to the batch's `excluded` list. Leave exact copies in: the route sets dedupe: exact
   and the assembler will exclude them (R-24), and the trace will show both decisions side by side.
4. Attach precomputed variants. data/variants.json maps the SHA-256 of a body (`common.content_hash`) to shorter
   forms written ahead of time by variants.py. Each variant on an item needs its own `id` (use
   f"{chunk.id}~{suffix}"), `body`, `method` and `lineage`. A producer never writes a variant during a request.
5. Return `common.batch("help-center-search", "retrieval", items, excluded)`.

Do not filter by score. min_relevance is the route's rule; your job is to put the score on the item.
"""

from __future__ import annotations

from common import Batch, Request


def help_center_search(request: Request) -> Batch:
    raise NotImplementedError("Lab A: see the module docstring")
