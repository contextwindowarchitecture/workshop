#!/usr/bin/env python3
"""Every link into contextwindowarchitecture.io names a page the site has and an anchor that page shows.

    python3 shared/tools/check_site_links.py            # against the website sibling, the checkout the site deploys from
    python3 shared/tools/check_site_links.py --live     # against the deployed site, fetched over HTTPS
    python3 shared/tools/check_site_links.py docs 06    # only files whose path starts with these

The pages render in the browser, so an anchor counts when a reader lands on it:

- an element id in the page's HTML; templated ids such as {{ g.id }} do not count on their own;
- #glossary or #glossary/<term> on any page that loads the glossary panel, for each term in site/glossary.json;
- #R-<n> on spec.html, one for each entry in the page's RULES list, which the page numbers in order;
- #assemble/<system>, alone or with /blob or /no-query, on assembler.html, for each system in the simulator's UCS list.

An anchor a page only redirects fails: index.html sends #assemble, #harness and the spec's old anchors to other pages,
and a link that relies on that has gone stale. The message names the page that holds the anchor now. If the site
changes how it builds one of these anchors, the check stops with a message saying which, rather than passing.

Every text file in the repository is scanned except the vendored contract, virtual environments and the kata's scratch
trees. Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))
from siblings import require  # noqa: E402

HOST = "contextwindowarchitecture.io"
URL = re.compile(r"https?://contextwindowarchitecture\.io(?:/[^\s)\"'<>\]`|]*)?")
SUFFIXES = {".md", ".py", ".html", ".svg", ".json", ".yaml", ".yml", ".toml", ".txt"}
SKIP_PARTS = {".venv", "node_modules", "__pycache__", "work", ".pristine", ".git", ".scratch", ".pytest_cache"}
SKIP_PREFIXES = ("shared/contract/cwa",)
STATIC_ID = re.compile(r'\bid="([^"{}\s]+)"')
PAGE_LINK = re.compile(r'href="\./([A-Za-z0-9_-]+\.html)')


class SiteChanged(Exception):
    """The site no longer builds an anchor the way this check expects."""


class Site:
    """The site's files, from the website sibling or over HTTPS, read once each."""

    def __init__(self, live: bool):
        self.live = live
        self.root = None if live else require("website")
        self._files: dict[str, str | None] = {}
        self._anchors: dict[str, set[str]] = {}

    def read(self, path: str) -> str | None:
        if path not in self._files:
            self._files[path] = self._fetch(path) if self.live else self._local(path)
        return self._files[path]

    def _local(self, path: str) -> str | None:
        file = self.root / path
        return file.read_text(encoding="utf-8") if file.is_file() else None

    def _fetch(self, path: str) -> str | None:
        try:
            with urllib.request.urlopen(f"https://{HOST}/{path}", timeout=20) as reply:
                return reply.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def pages(self) -> list[str]:
        """The HTML pages the home page links to, and the home page."""
        return sorted({"index.html", *PAGE_LINK.findall(self.read("index.html") or "")})

    def anchors(self, page: str) -> set[str]:
        if page not in self._anchors:
            self._anchors[page] = self._build(page, self.read(page) or "")
        return self._anchors[page]

    def _build(self, page: str, html: str) -> set[str]:
        found = set(STATIC_ID.findall(html))
        if "site/glossary.js" in html:
            terms = json.loads(self.read("site/glossary.json") or "[]")
            found |= {"glossary"} | {f"glossary/{t['id']}" for t in terms}
        if page == "spec.html":
            found |= {f"R-{n}" for n in range(1, len(list_entries(html, "RULES", page)) + 1)}
        if page == "assembler.html":
            for label in re.findall(r'^ {4}label: "([^"]+)"', list_block(html, "UCS", page), re.MULTILINE):
                slug = re.sub(r"[^a-z0-9]+", "-", label.lower())
                found |= {f"assemble/{slug}", f"assemble/{slug}/blob", f"assemble/{slug}/no-query"}
        return found


def list_block(html: str, name: str, page: str) -> str:
    start = html.find(f"const {name} = [")
    end = html.find("\n];", start)
    if start < 0 or end < 0:
        raise SiteChanged(f"{page} has no `const {name} = [` list; teach check_site_links.py how it builds its anchors now")
    return html[start:end]


def list_entries(html: str, name: str, page: str) -> list[str]:
    return re.findall(r"^  [\[{]", list_block(html, name, page), re.MULTILINE)


def text_files(prefixes: list[str]) -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if path.suffix not in SUFFIXES or not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in rel.parts) or str(rel).startswith(SKIP_PREFIXES):
            continue
        if prefixes and not any(str(rel).startswith(p) for p in prefixes):
            continue
        out.append(path)
    return out


def problem(site: Site, url: str) -> str | None:
    parts = urlsplit(url.rstrip(".,;:"))
    page = parts.path.lstrip("/")
    if page == "" or page.endswith("/"):
        page += "index.html"
    if site.read(page) is None:
        return f"no page {page}"
    anchor = parts.fragment
    if not anchor or not page.endswith(".html") or anchor in site.anchors(page):
        return None
    elsewhere = [p for p in site.pages() if p != page and anchor in site.anchors(p)]
    return f"no anchor #{anchor} on {page}" + (f"; it is on {', '.join(elsewhere)}" if elsewhere else "")


def main(argv: list[str]) -> int:
    live = "--live" in argv
    site = Site(live)
    files = text_files([a for a in argv if not a.startswith("--")])
    links, problems = 0, []
    try:
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                for m in URL.finditer(line):
                    links += 1
                    found = problem(site, m.group(0))
                    if found:
                        problems.append(f"  {path.relative_to(ROOT)}:{number}: {m.group(0)}: {found}")
    except SiteChanged as e:
        print(e)
        return 1
    for line in problems:
        print(line)
    source = f"https://{HOST}" if live else str(site.root)
    print(f"{len(files)} file(s), {links} link(s) to the site, {len(problems)} broken (checked against {source})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
