"""Phase 6 orchestrator — 4 queries × 3 formats."""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from phase4.agent_b import count_tokens
from phase6.fetcher import fetch_as_doc
from phase6.formatter import FORMATTERS
from phase6.coordinator import synthesize, synthesize_explicit
from phase6.queries import QUERIES

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results", "phase6_results.json")
RESULTS_PATH_EXPLICIT = os.path.join(os.path.dirname(__file__), "results", "phase6_results_explicit.json")
FORMATS = ["evolved", "acf", "json"]


def _fetch_parallel(sources: list[str]) -> list[dict]:
    docs = [None] * len(sources)
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_as_doc, src): i for i, src in enumerate(sources)}
        for fut in as_completed(futures):
            docs[futures[fut]] = fut.result()
    return docs


def run(swarm: bool = False, explicit: bool = False) -> list[dict]:
    all_results = []

    for query in QUERIES:
        qid = query["id"]
        question = query["question"]
        sources = query["sources"]
        expected_facts = query["expected_facts"]

        print(f"\nQuery {qid}: {question[:70]}...")

        docs = _fetch_parallel(sources)
        query_results = {"query_id": qid, "question": question, "formats": {}}

        for i_fmt, fmt in enumerate(FORMATS):
            if explicit and i_fmt > 0:
                time.sleep(3)  # ~3 parallel calls per batch; pace to stay under 50 RPM (Tier 1)
            formatter_fn = FORMATTERS[fmt]
            summaries = [
                {"content": formatter_fn(doc), "a_tokens": count_tokens(formatter_fn(doc)), "source": src}
                for doc, src in zip(docs, sources)
            ]

            if explicit:
                result = synthesize_explicit(summaries, question, expected_facts, model="claude-haiku")
                label = fmt.upper()
                print(
                    f"  [{label:<7}] fetcher_tokens={result['per_fetcher_tokens']:>4}  "
                    f"total_ctx={result['total_context_tokens']:>5}  "
                    f"acc={result['accuracy']:.2f}  "
                    f"sub_ms={result['sub_agent_latency_ms']}  "
                    f"synth_ms={result['synthesis_latency_ms']}"
                )
            else:
                result = synthesize(summaries, question, expected_facts,
                                    model="kimi-k2.5", swarm=swarm)
                label = fmt.upper()
                print(
                    f"  [{label:<7}] fetcher_tokens={result['per_fetcher_tokens']:>4}  "
                    f"total_ctx={result['total_context_tokens']:>5}  "
                    f"acc={result['accuracy']:.2f}  "
                    f"{result['latency_ms']}ms"
                )

            query_results["formats"][fmt] = result

        all_results.append(query_results)

    _print_summary(all_results, explicit=explicit)
    _save(all_results, explicit=explicit)
    return all_results


def _print_summary(results: list[dict], explicit: bool = False) -> None:
    print("\n" + "=" * 70)
    print(f"{'FORMAT':<10} {'AVG CTX TOKENS':>15} {'AVG ACC':>9} {'COMPOUNDING':>12}")
    print("-" * 70)

    fmt_totals: dict[str, dict] = {fmt: {"ctx": 0, "acc": 0.0} for fmt in FORMATS}
    n = len(results)

    for qr in results:
        for fmt in FORMATS:
            r = qr["formats"][fmt]
            fmt_totals[fmt]["ctx"] += r["total_context_tokens"]
            fmt_totals[fmt]["acc"] += r["accuracy"]

    json_avg_ctx = fmt_totals["json"]["ctx"] / n if n else 1

    for fmt in FORMATS:
        avg_ctx = fmt_totals[fmt]["ctx"] / n
        avg_acc = fmt_totals[fmt]["acc"] / n
        compounding = round(avg_ctx / json_avg_ctx, 3) if json_avg_ctx else 1.0
        print(f"{fmt.upper():<10} {avg_ctx:>15.0f} {avg_acc:>9.2f} {compounding:>12.3f}x")

    print("=" * 70)
    evolved_ctx = fmt_totals["evolved"]["ctx"] / n
    json_ctx = fmt_totals["json"]["ctx"] / n
    if json_ctx:
        savings = round((1 - evolved_ctx / json_ctx) * 100, 1)
        mode_label = "explicit 3-agent" if explicit else "standard"
        print(f"[{mode_label}] Evolved saves {savings}% context tokens vs JSON across {n} queries.")


def _save(results: list[dict], explicit: bool = False) -> None:
    path = RESULTS_PATH_EXPLICIT if explicit else RESULTS_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--swarm", action="store_true", help="Kimi swarm mode (standard run only)")
    parser.add_argument("--explicit", action="store_true", help="Explicit 3-agent topology (Claude Haiku)")
    args = parser.parse_args()
    run(swarm=args.swarm, explicit=args.explicit)
