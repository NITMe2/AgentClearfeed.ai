"""Phase 7 orchestrator — runs champion / ACF / JSON comparison over real A2A transport."""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase4.agent_b import count_tokens, grade_answer, COST_PER_1M
from phase4.formatters import acf, json_fmt, champion
from server.parser import load_documents
from test_harness.queries import QUERIES
from phase7.agent_a_client import send_to_agent_b

FORMATS = {
    "champion": champion,
    "acf": acf,
    "json": json_fmt,
}

DOCS_DIR = Path(__file__).resolve().parents[1] / "server" / "documents"
RESULTS_FILE = Path(__file__).resolve().parent / "results" / "phase7_results.json"

# Phase 4 Haiku baseline for reference
P4_BASELINE = {
    "champion": {"a_tokens": 298, "b_tokens": 338, "total": 636, "accuracy": 1.00, "data_loss": 0.00, "latency_ms": 4092, "cost_usd": 0.000509},
    "acf":      {"a_tokens": 394, "b_tokens": 434, "total": 828, "accuracy": 0.89, "data_loss": 0.11, "latency_ms": 3128, "cost_usd": 0.000663},
    "json":     {"a_tokens": 446, "b_tokens": 486, "total": 932, "accuracy": 0.89, "data_loss": 0.11, "latency_ms": 1860, "cost_usd": 0.000746},
}


def start_agent_b() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "phase7.agent_b_server:app",
         "--port", "9999", "--log-level", "error"],
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    time.sleep(3)
    return proc


async def run_all_tests(docs: dict) -> dict:
    results = {}

    for fmt_name, formatter in FORMATS.items():
        print(f"\n{'='*70}")
        print(f"Format: {fmt_name.upper()}")
        print(f"{'='*70}")
        fmt_results = []

        for q in QUERIES:
            doc_id = q["acf_doc"]
            doc = docs.get(doc_id)
            if doc is None:
                print(f"  [WARN] doc not found: {doc_id}")
                continue

            formatted = formatter.format_doc(doc)
            a_tokens = count_tokens(formatted)

            t_start = time.time()
            result = await send_to_agent_b(formatted, q["question"])
            wall_ms = round((time.time() - t_start) * 1000)

            answer = result["answer"]
            b_tokens = result["b_tokens"]
            latency_ms = result.get("latency_ms", wall_ms)
            total_tokens = a_tokens + b_tokens
            cost_usd = round(total_tokens / 1_000_000 * COST_PER_1M.get("claude-haiku", 0.80), 6)

            grade = grade_answer(answer, q["expected_facts"])
            accuracy = grade["accuracy"]
            data_loss = round(1.0 - accuracy, 2)

            print(f"  [{q['id']}] a={a_tokens} b={b_tokens} total={total_tokens} "
                  f"acc={accuracy:.2f} loss={data_loss:.2f} {wall_ms}ms")

            fmt_results.append({
                "query_id": q["id"],
                "question": q["question"],
                "a_tokens": a_tokens,
                "b_tokens": b_tokens,
                "total_tokens": total_tokens,
                "accuracy": accuracy,
                "data_loss": data_loss,
                "latency_ms": wall_ms,
                "cost_usd": cost_usd,
                "answer": answer,
                "grade": grade,
            })

        results[fmt_name] = fmt_results

    return results


def aggregate_runs(all_runs: list[dict]) -> dict:
    """Merge results from N runs into per-format averaged stats."""
    merged: dict[str, list] = {}
    for run in all_runs:
        for fmt_name, queries in run.items():
            merged.setdefault(fmt_name, []).extend(queries)
    return merged


def print_summary(results: dict, n_runs: int = 1) -> None:
    label = f"Phase 7 -- A2A Protocol Results (avg over {n_runs} run{'s' if n_runs > 1 else ''})"
    print(f"\n{'='*70}")
    print(label)
    print(f"{'='*70}")

    header = f"{'Format':<10} {'A Tok':>7} {'B Tok':>7} {'Total':>7} {'Accuracy':>9} {'DataLoss':>9} {'Latency':>10} {'Cost':>12}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    for fmt_name, runs in results.items():
        if not runs:
            continue
        avg_a = round(sum(r["a_tokens"] for r in runs) / len(runs))
        avg_b = round(sum(r["b_tokens"] for r in runs) / len(runs))
        avg_total = round(sum(r["total_tokens"] for r in runs) / len(runs))
        avg_acc = round(sum(r["accuracy"] for r in runs) / len(runs), 2)
        avg_loss = round(sum(r["data_loss"] for r in runs) / len(runs), 2)
        avg_lat = round(sum(r["latency_ms"] for r in runs) / len(runs))
        avg_cost = round(sum(r["cost_usd"] for r in runs) / len(runs), 6)
        print(f"{fmt_name.upper():<10} {avg_a:>7} {avg_b:>7} {avg_total:>7} {avg_acc:>9.2f} {avg_loss:>9.2f} {avg_lat:>9}ms ${avg_cost:>11.6f}")

    print(sep)
    print("\nPhase 4 Haiku Baseline (in-process, no HTTP):")
    print(header)
    print(sep)
    for fmt_name, b in P4_BASELINE.items():
        print(f"{fmt_name.upper():<10} {b['a_tokens']:>7} {b['b_tokens']:>7} {b['total']:>7} "
              f"{b['accuracy']:>9.2f} {b['data_loss']:>9.2f} {b['latency_ms']:>9}ms ${b['cost_usd']:>11.6f}")
    print(sep)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=1, help="Number of full test passes to average")
    args = parser.parse_args()

    docs = load_documents(DOCS_DIR)
    print(f"Loaded {len(docs)} documents")

    print("Starting Agent B server on port 9999...")
    proc = start_agent_b()

    async def run_n(n: int) -> list[dict]:
        runs = []
        for i in range(n):
            if n > 1:
                print(f"\n{'#'*70}")
                print(f"RUN {i + 1} / {n}")
                print(f"{'#'*70}")
            runs.append(await run_all_tests(docs))
        return runs

    try:
        all_runs = asyncio.run(run_n(args.runs))
        aggregated = aggregate_runs(all_runs)
        print_summary(aggregated, n_runs=args.runs)

        RESULTS_FILE.parent.mkdir(exist_ok=True)
        with open(RESULTS_FILE, "w") as f:
            json.dump({
                "phase": 7,
                "model": "claude-haiku",
                "transport": "a2a-sdk-1.0.3",
                "n_runs": args.runs,
                "results": aggregated,
                "raw_runs": all_runs,
            }, f, indent=2)
        print(f"\nResults saved to {RESULTS_FILE}")

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
