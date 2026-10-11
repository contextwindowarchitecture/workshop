"""The request both apps answer: who is asking, in which session, what was said before, and the question now.

Shared by before/, after/ and solution/. The application authenticated the user and read the clock once; nothing a
producer or a prompt builder does changes these fields.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "shared"))
from fernway import ACCOUNTS, MEMORIES  # noqa: E402,F401
from fernway import corpus  # noqa: E402,F401


@dataclass(frozen=True)
class Turn:
    role: str  # "user" or "assistant"
    text: str
    at: str


@dataclass(frozen=True)
class Request:
    user: str
    session: str
    asked_at: str
    question: str
    turns: tuple[Turn, ...] = ()
    faults: frozenset[str] = frozenset()  # deliberate bugs a scenario injects, by name

    @property
    def tenant(self) -> str:
        return json.loads(ACCOUNTS.read_text(encoding="utf-8"))["users"][self.user]["workspace"]

    @classmethod
    def load(cls, path: str | Path) -> Request:
        """A conversation file: {"user", "session", "asked_at", "turns": [{"role", "text", "at"}], "question", "faults"?}."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(user=data["user"], session=data["session"], asked_at=data["asked_at"], question=data["question"],
                   turns=tuple(Turn(**t) for t in data.get("turns", [])), faults=frozenset(data.get("faults", [])))


def accounts() -> dict:
    return json.loads(ACCOUNTS.read_text(encoding="utf-8"))


def memories() -> list[dict]:
    return json.loads(MEMORIES.read_text(encoding="utf-8"))["memories"]
