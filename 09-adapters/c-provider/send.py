"""Adapt a payload and, when an endpoint is configured, send it; always show the exact outbound request and its hash.

    uv run send.py                        # cwa-messages/v1 payload: the request, the two hashes, sent if OPENAI_BASE_URL is set
    uv run send.py --blocks               # the cwa-message-blocks/v1 payload instead
    uv run send.py --impl labs            # your adapter
    uv run send.py --snippet              # print the SDK snippet instead
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
    args = p.parse_args(argv)
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
