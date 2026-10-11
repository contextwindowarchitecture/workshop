"""The help centre as retrievable chunks, with a dependency-free BM25 and a word-overlap measure.

Each article starts with a front matter block (id, title, version, updated) and every paragraph after it is one chunk.
A chunk id names the article, its version and the paragraph, so an edited article gets new ids and a cited id always
means the text it was cited for. Scoring is plain BM25 with ties broken by id, so the same question gives the same
order on every machine and committed scenarios hold everywhere.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from fernway import HELP_CENTER


@dataclass(frozen=True)
class Chunk:
    id: str  # help:<article>@<version>#<paragraph>
    article: str
    title: str
    version: str
    updated: str
    text: str


def front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a leading `---` block of `key: value` lines from the body that follows it."""
    head, sep, body = text.partition("\n---\n")
    if not text.startswith("---\n") or not sep:
        raise ValueError("expected a --- front matter block")
    fields: dict[str, str] = {}
    for line in head.splitlines()[1:]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, body.strip()


@cache
def chunks(directory: Path = HELP_CENTER, prefix: str = "help") -> tuple[Chunk, ...]:
    """prefix names the corpus in every chunk id: help:<article>@<version>#<n> for the Fernway help centre."""
    found = []
    for path in sorted(directory.glob("*.md")):
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        for index, paragraph in enumerate(p.strip() for p in body.split("\n\n") if p.strip()):
            found.append(Chunk(f"{prefix}:{meta['id']}@{meta['version']}#{index}", meta["id"], meta["title"],
                               meta["version"], meta["updated"], paragraph))
    return tuple(found)


_WORD = re.compile(r"[a-z0-9]+")


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def bm25(question: str, k1: float = 1.5, b: float = 0.75, directory: Path = HELP_CENTER, prefix: str = "help") -> list[tuple[Chunk, float]]:
    """Every chunk scored against the question, best first, ties broken by id. Any directory of front-matter articles works."""
    docs = [(chunk, words(chunk.text)) for chunk in chunks(directory, prefix)]
    n = len(docs)
    avg = sum(len(terms) for _, terms in docs) / n
    df: dict[str, int] = {}
    for _, terms in docs:
        for term in set(terms):
            df[term] = df.get(term, 0) + 1
    query = words(question)
    scored = []
    for chunk, terms in docs:
        score = 0.0
        for term in set(query):
            tf = terms.count(term)
            if not tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(terms) / avg))
        scored.append((chunk, round(score, 3)))
    return sorted(scored, key=lambda pair: (-pair[1], pair[0].id))


def jaccard(a: str, b: str) -> float:
    """Word-set overlap. 1.0 means the same words."""
    x, y = set(words(a)), set(words(b))
    return len(x & y) / len(x | y) if x | y else 1.0
