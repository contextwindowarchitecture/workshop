"""Fernway, the fictional team task tracker the workshops share, borrowed from the examples repository.

shared/fixtures/ holds the data: nine help-centre articles (eight from examples/01-docs-qa plus exports-faq.md, which
repeats one data-export paragraph word for word and rewords another, so retrieval labs have duplicates to find), the
accounts of two workspaces and three users, and a memory store with expired and revoked rows. This package holds the
code every workshop needs to read them. It has no dependencies.

    import sys; sys.path.insert(0, "<repo>/shared")
    from fernway import corpus, FIXTURES
"""

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
HELP_CENTER = FIXTURES / "help-center"
ACCOUNTS = FIXTURES / "accounts.json"
MEMORIES = FIXTURES / "memories.json"
