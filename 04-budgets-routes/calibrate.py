"""Lab C: how wrong is the estimate tokenizer for your model, and what margin covers it?

    uv run calibrate.py                                  # estimate-utf8/v1 against tiktoken's cl100k_base on this route's texts
    uv run --extra calibrate calibrate.py                # same, installing tiktoken first
    uv run calibrate.py --encoding o200k_base            # another OpenAI encoding
    uv run calibrate.py --stop-rule                      # show the published-id stop rule (R-16)

estimate-utf8/v1 counts UTF-8 bytes divided by four, rounded up. It is portable and needs no vocabulary, and it is
wrong by a model-dependent factor that budget.margin_percent has to cover: the payload fits only when
count * (100 + margin) / 100, rounded up, is at most budget.input. This script counts every text the route renders
with both tokenizers, reports the worst ratio, and recommends the smallest margin that covers it with headroom.

The alternative is to count with the model's own tokenizer, passed to Snapshot.from_json under an id of your own. It
can never be passed under a published id: the trace must mean what it says (R-16). --stop-rule shows both.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

from cwa import Snapshot, assemble

from app import context
from request import Request

TEXTS = [Request(user="u_ada", session="s_cal", asked_at="2026-10-01T10:00:00Z", question=q) for q in (
    "How do I export the whole workspace, including attachments?",
    "Can I get a refund on a monthly plan?",
    "Who can change our billing details?",
    "How do we set up single sign-on with Okta?",
)]


def estimate(text: str) -> int:
    return (len(text.encode("utf-8")) + 3) // 4


class Tiktoken:
    """An application tokenizer: any object with an id and a count(text). Loaded before freezing; assemble() reads nothing else."""

    def __init__(self, encoding: str) -> None:
        import tiktoken

        self.id = f"tiktoken-{encoding}/v1"
        self._enc = tiktoken.get_encoding(encoding)

    def count(self, text: str) -> int:
        return len(self._enc.encode(text))


def payload_texts(document: dict) -> list[str]:
    result = assemble(Snapshot.from_json(document))
    if result.payload is None:
        return []
    rendered = json.loads(result.payload)
    texts = [e["text"] for e in rendered.get("system", [])]
    texts += [m["content"] if isinstance(m["content"], str) else "".join(b["text"] for b in m["content"]) for m in rendered["messages"]]
    return texts


def stop_rule(tok: Tiktoken) -> None:
    document = context.snapshot(TEXTS[0], "account-help")
    document["tokenizer"] = tok.id
    result = assemble(Snapshot.from_json(document, tokenizers={tok.id: tok}))
    print(f"own id {tok.id!r}: assembled, {result.trace['result']['input_tokens']} tokens; the trace names it")
    document["tokenizer"] = "estimate-utf8/v1"
    try:
        Snapshot.from_json(document, tokenizers={"estimate-utf8/v1": tok})
    except ValueError as error:
        print(f"published id 'estimate-utf8/v1' with your tokenizer: stopped before assembly: {error}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--encoding", default="cl100k_base")
    p.add_argument("--stop-rule", action="store_true")
    args = p.parse_args(argv)
    try:
        tok = Tiktoken(args.encoding)
    except ImportError:
        print("tiktoken is not installed: uv run --extra calibrate calibrate.py", file=sys.stderr)
        return 2
    if args.stop_rule:
        stop_rule(tok)
        return 0
    worst, rows = 0.0, []
    for request in TEXTS:
        for text in payload_texts(context.snapshot(request, "account-help")):
            e, t = estimate(text), tok.count(text)
            ratio = t / e if e else 1.0
            worst = max(worst, ratio)
            rows.append((e, t, ratio, text[:50].replace("\n", " ")))
    for e, t, ratio, head in rows:
        print(f"  estimate {e:>5}  {args.encoding} {t:>5}  ratio {ratio:5.3f}  {head}")
    margin = max(0, math.ceil((worst - 1) * 100) + 5)
    print(f"\nworst ratio {worst:.3f}: the estimate undercounts by up to {max(0.0, (worst - 1) * 100):.1f}% on these texts.")
    print(f"recommended budget.margin_percent: {margin} (worst error rounded up, plus 5 points of headroom)")
    print("the routes table currently sets 15; change it if your model's tokenizer needs more, and re-check the scenarios")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
