"""Adapt a payload and, when an endpoint is configured, send it; always show the exact outbound request and its hash.

    uv run send.py                        # cwa-messages/v1 payload: the request, the two hashes, sent if OPENAI_BASE_URL is set
    uv run send.py --blocks               # the cwa-message-blocks/v1 payload instead
    uv run send.py --impl labs            # your adapter
    uv run send.py --snippet              # print the SDK snippet instead
    uv run send.py --anthropic --breakpoint-after turn:17   # part 3: the Messages API mapping, with a cache breakpoint
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import impl
import payloads


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--blocks", action="store_true")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    p.add_argument("--snippet", action="store_true")
    p.add_argument("--anthropic", action="store_true", help="the Messages API mapping in solution/provider.py, on the blocks payload")
    p.add_argument("--breakpoint-after", metavar="ITEM_ID", help="with --anthropic: a cache breakpoint on that item's block")
    args = p.parse_args(argv)
    if args.anthropic:
        return anthropic(os.environ.get("CWA_WORKSHOP_MODEL", "local-model"), args.breakpoint_after)
    provider = impl.module(args.impl)
    result = payloads.rendered(payloads.BLOCKS if args.blocks else payloads.MESSAGES)
    model = os.environ.get("CWA_WORKSHOP_MODEL", "local-model")
    try:
        request = provider.to_request(result.payload, model, payloads.reserved_output())
    except NotImplementedError as todo:
        print(f"not written yet: {todo}")
        return 2
    if args.snippet:
        print(provider.snippet(request))
        return 0
    sent, read = provider.digest(provider.texts_of_request(request)), provider.digest(provider.texts_of(result.payload))
    print(json.dumps(request, indent=2, ensure_ascii=False)[:1500] + ("\n..." if len(json.dumps(request)) > 1500 else ""))
    print(f"\npayload sha256 (trace)     {result.trace['result']['hash']}\ntexts the model reads      {read}\ntexts the request carries  {sent}\n"
          + ("same texts: the adapter added nothing" if sent == read else "DIFFERENT: the adapter changed or added text"))
    if not os.environ.get("OPENAI_BASE_URL"):
        print("\n(no OPENAI_BASE_URL set: not sent)")
        return 0
    from openai import OpenAI
    client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ.get("OPENAI_API_KEY", "none"))
    response = client.chat.completions.create(**request)
    print("\nanswer:", response.choices[0].message.content)
    return 0



def anthropic(model: str, breakpoint_after: str | None) -> int:
    """Part 3: the blocks payload for the Messages API, with or without a breakpoint. The breakpoint is structure, so the
    texts the request carries hash the same either way; diff two runs and only the cache_control marker differs."""
    from solution import provider as reference
    result = payloads.rendered(payloads.BLOCKS)
    request = reference.to_anthropic_request(result.payload, model, payloads.reserved_output(), breakpoint_after)
    print(json.dumps(request, indent=2, ensure_ascii=False))
    carried = [entry["text"] for entry in request.get("system", [])]
    carried += [json.dumps(tool, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for tool in request.get("tools", [])]
    carried += ["".join(block["text"] for block in message["content"]) for message in request["messages"]]
    read, sent = reference.digest(reference.texts_of(result.payload)), reference.digest(carried)
    marked = [b for m in request["messages"] for b in m["content"] if "cache_control" in b]
    print(f"\nbreakpoint                 {'on ' + str(len(marked)) + ' block' if marked else 'none'}"
          f"\ntexts the model reads      {read}\ntexts the request carries  {sent}\n"
          + ("same texts: the breakpoint added nothing" if sent == read else "DIFFERENT: the mapping changed or added text"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
