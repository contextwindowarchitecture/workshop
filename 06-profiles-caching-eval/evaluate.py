"""Lab B and Lab C: measure cache reuse, run the evaluation suite, write the artifact, promote a profile.

    uv run evaluate.py reuse cache-first                 # Lab B: prefix reuse turn to turn, per conversation
    uv run evaluate.py run cache-first                   # Lab C: the structural suite; writes evaluations/<id>-v<n>-<suite>.json
    uv run evaluate.py run cache-first --live            # also ask a model each turn and grade grounding (needs OPENAI_BASE_URL)
    uv run evaluate.py compare                           # every profile's result on one table
    uv run evaluate.py promote cache-first --model-family gpt-oss:20b   # mark it evaluated, pointing at its artifact

The suite is w6-structural/v1. It fixes the item set (evaluations/conversations.json, three conversations of four
turns), renders every turn under the profile with cwa-message-blocks/v1, and measures three things that depend on
placement alone: cache reuse (how much of turn n's payload is a byte prefix of turn n+1's), evidence distance (tokens
between the last article and the query), and input tokens. With --live it also records each turn's answer and grades
whether the article ids the answer cites were in the request. The structural part is deterministic and model-free; the
live part names the model, and a profile is evaluated for a model only when the live part ran on it (R-19).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import impl
from app import context

HERE = Path(__file__).resolve().parent
EVALUATIONS = HERE / "evaluations"
SUITE = "w6-structural/v1"
CITATION = re.compile(r"help:[a-z0-9-]+@\d+#\d+")


def conversations() -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in json.loads((EVALUATIONS / "conversations.json").read_text(encoding="utf-8"))["conversations"]}


def blocks_of(payload: bytes | None) -> list[dict[str, str]]:
    """The user message's blocks under cwa-message-blocks/v1: one {id, text} per placed item, in placement order."""
    if payload is None:
        return []
    rendered = json.loads(payload)
    out = [{"id": f"system:{n}", "text": e["text"]} for n, e in enumerate(rendered.get("system", []))]
    for message in rendered["messages"]:
        content = message["content"]
        out += content if isinstance(content, list) else [{"id": "user", "text": content}]
    return out


def common_prefix_bytes(a: bytes, b: bytes) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def reuse(profile: dict[str, Any], conversation: dict[str, Any]) -> dict[str, Any]:
    """Turn to turn: how many leading blocks of turn n reappear unchanged at the head of turn n+1, and how many bytes."""
    renders = []
    for request in context.turns_of(conversation):
        result = context.assemble(context.snapshot(request, profile))
        renders.append((result.payload or b"", blocks_of(result.payload), result.trace))
    pairs = []
    for (pa, ba, ta), (pb, bb, tb) in zip(renders, renders[1:]):
        shared = 0
        for x, y in zip(ba, bb):
            if x["id"] != y["id"] or x["text"] != y["text"]:
                break
            shared += 1
        pairs.append({"blocks_shared": shared, "blocks_in_earlier": len(ba), "bytes_shared": common_prefix_bytes(pa, pb), "bytes_in_earlier": len(pa)})
    block_ratio = sum(p["blocks_shared"] for p in pairs) / max(1, sum(p["blocks_in_earlier"] for p in pairs))
    byte_ratio = sum(p["bytes_shared"] for p in pairs) / max(1, sum(p["bytes_in_earlier"] for p in pairs))
    return {"conversation": conversation["id"], "pairs": pairs, "block_reuse": round(block_ratio, 3), "byte_reuse": round(byte_ratio, 3),
            "tokens": [t["result"]["input_tokens"] if t["result"] else None for _, _, t in renders]}


def evidence_distance(trace: dict[str, Any]) -> int | None:
    """Tokens between the last rendered article and the query: how far the model reads back from the question."""
    included = trace["included"]
    articles = [n for n, r in enumerate(included) if r["slot"] == "evidence.knowledge"]
    query = next((n for n, r in enumerate(included) if r["slot"] == "interaction.query"), None)
    if not articles or query is None:
        return None
    return sum(r["tokens"] for r in included[articles[-1] + 1: query])


def run(profile: dict[str, Any], live: bool, model: str | None) -> dict[str, Any]:
    per = []
    grounded = []
    for conversation in conversations().values():
        measured = reuse(profile, conversation)
        distances = []
        for request in context.turns_of(conversation):
            result = context.assemble(context.snapshot(request, profile))
            distances.append(evidence_distance(result.trace))
            if live and result.payload:
                import provider
                reply = provider.send(provider.request_for(result.payload, model or provider.model(), context.BUDGET["reserved_output"])) or ""
                sent = {r["item_id"] for r in result.trace["included"] if r["slot"] == "evidence.knowledge"}
                cited = set(CITATION.findall(reply))
                grounded.append({"turn": request.question[:40], "cited": sorted(cited), "all_cited_were_sent": cited <= sent, "answer": reply})
        measured["evidence_distance_tokens"] = distances
        per.append(measured)
    result = {
        "block_reuse": round(sum(m["block_reuse"] for m in per) / len(per), 3),
        "byte_reuse": round(sum(m["byte_reuse"] for m in per) / len(per), 3),
        "mean_evidence_distance_tokens": round(sum(d for m in per for d in m["evidence_distance_tokens"] if d is not None) / max(1, sum(1 for m in per for d in m["evidence_distance_tokens"] if d is not None)), 1),
        "mean_input_tokens": round(sum(t for m in per for t in m["tokens"] if t) / sum(1 for m in per for t in m["tokens"] if t), 1),
        "grounded_answers": (f"{sum(1 for g in grounded if g['all_cited_were_sent'])}/{len(grounded)}" if grounded else None),
    }
    return {"suite": SUITE, "profile": {"id": profile["id"], "version": profile["version"]}, "route_policy_version": profile["route_policy_version"],
            "renderer": context.BLOCKS, "tokenizer": "estimate-utf8/v1", "date": date.today().isoformat(),
            "live": {"ran": live, "model": model if live else None, "answers": grounded}, "result": result, "per_conversation": per}


def summarize(result: dict[str, Any]) -> str:
    """The result as the one line the profile's evaluation object carries (the schema wants a string); the artifact holds the numbers."""
    return (f"block_reuse {result['block_reuse']}; byte_reuse {result['byte_reuse']}; evidence_distance_tokens {result['mean_evidence_distance_tokens']}; "
            f"mean_input_tokens {result['mean_input_tokens']}; grounded_answers {result['grounded_answers'] or 'not run'}")


def artifact_path(profile: dict[str, Any]) -> Path:
    return EVALUATIONS / f"{profile['id']}-v{profile['version']}-{SUITE.replace('/', '-')}.json"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["reuse", "run", "compare", "promote"])
    p.add_argument("profile", nargs="?")
    p.add_argument("--live", action="store_true")
    p.add_argument("--model", help="the model the live part asks (default: CWA_WORKSHOP_MODEL)")
    p.add_argument("--model-family", help="promote: the model family the profile is evaluated for")
    p.add_argument("--impl", choices=["labs", "solution"], default=None)
    args = p.parse_args(argv)
    table = context.profiles(args.impl)
    if args.command == "compare":
        print(f"{'profile':<18}{'block reuse':>12}{'byte reuse':>12}{'evidence dist':>15}{'mean tokens':>13}  status")
        for pid, profile in table.items():
            r = run(profile, False, None)["result"]
            print(f"{pid:<18}{r['block_reuse']:>12.3f}{r['byte_reuse']:>12.3f}{r['mean_evidence_distance_tokens']:>15.1f}{r['mean_input_tokens']:>13.1f}  {profile['evaluation']['status']}")
        return 0
    profile = table[args.profile]
    if args.command == "reuse":
        for conversation in conversations().values():
            m = reuse(profile, conversation)
            print(f"{conversation['id']}: block reuse {m['block_reuse']}, byte reuse {m['byte_reuse']}, tokens {m['tokens']}")
            for n, pair in enumerate(m["pairs"], start=1):
                print(f"   turn {n} -> {n + 1}: {pair['blocks_shared']}/{pair['blocks_in_earlier']} leading blocks unchanged, {pair['bytes_shared']}/{pair['bytes_in_earlier']} leading bytes")
        return 0
    if args.command == "run":
        import provider
        if args.live and not provider.configured():
            print("--live needs OPENAI_BASE_URL", file=sys.stderr)
            return 2
        record = run(profile, args.live, args.model or (provider.model() if args.live else None))
        path = artifact_path(profile)
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(record["result"], indent=2))
        print(f"artifact: {path.relative_to(HERE)}")
        return 0
    # promote
    path = artifact_path(profile)
    if not path.exists():
        print(f"no artifact for {args.profile} v{profile['version']}: run the suite first", file=sys.stderr)
        return 1
    if not args.model_family:
        print("promote needs --model-family: a profile is evaluated for a concrete model (R-19)", file=sys.stderr)
        return 1
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["profile"] != {"id": profile["id"], "version": profile["version"]}:
        print("the artifact is for another profile or version", file=sys.stderr)
        return 1
    file = impl.path("profiles.json", args.impl)
    document = json.loads(file.read_text(encoding="utf-8"))
    for entry in document["profiles"]:
        if entry["id"] == profile["id"] and entry["version"] == profile["version"]:
            if entry["model_family"] != args.model_family:
                entry["version"] += 1  # a new model target is a new version; evaluation alone keeps it (R-20)
            entry["model_family"] = args.model_family
            entry["evaluation"] = {"status": "evaluated", "suite": SUITE, "date": record["date"], "result": summarize(record["result"]), "artifact": str(path.relative_to(HERE))}
            promoted = entry
    file.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{profile['id']} v{promoted['version']} is evaluated for {args.model_family} on {SUITE}; now lock the registry: uv run registry.py lock")
    if not record["live"]["ran"]:
        print("note: the live part did not run, so the artifact's grounded_answers is null; the structural result is what this promotion rests on")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
