"""Phase 4 orchestrator — runs all four agent-communication format tests."""

import argparse
import json
from pathlib import Path

from phase4 import agent_a, agent_b
from test_harness.queries import QUERIES
from test_harness.phase2.queries_phase2 import PHASE2_QUERIES, PHASE2_TOPICS


def _build_phase2_queries() -> list[dict]:
    """Join PHASE2_QUERIES with PHASE2_TOPICS to add acf_doc to each query."""
    topic_map = {t["id"]: t["acf_doc"] for t in PHASE2_TOPICS}
    queries = []
    for q in PHASE2_QUERIES:
        queries.append({**q, "acf_doc": topic_map[q["target_topic"]]})
    return queries

RESULTS_DIR = Path(__file__).parent / "results"

TESTS = [
    {"id": 1, "name": "ACF vs JSON",          "formats": ["acf", "json"]},
    {"id": 2, "name": "ACF vs TOON",          "formats": ["acf", "toon"]},
    {"id": 3, "name": "JSON vs TOON",         "formats": ["json", "toon"]},
    {"id": 4, "name": "ACF vs JSON vs TOON",  "formats": ["acf", "json", "toon"]},
]

COL_W = {
    "format":   6,
    "a_tok":   10,
    "b_tok":   10,
    "total":   10,
    "acc":      9,
    "loss":     9,
    "lat":     10,
    "cost":    10,
}


def _header_row() -> str:
    return (
        f"{'Format':<{COL_W['format']}} "
        f"{'A Tokens':>{COL_W['a_tok']}} "
        f"{'B Tokens':>{COL_W['b_tok']}} "
        f"{'Total':>{COL_W['total']}} "
        f"{'Accuracy':>{COL_W['acc']}} "
        f"{'DataLoss':>{COL_W['loss']}} "
        f"{'Latency':>{COL_W['lat']}} "
        f"{'Cost':>{COL_W['cost']}}"
    )


def _data_row(fmt: str, agg: dict) -> str:
    return (
        f"{fmt.upper():<{COL_W['format']}} "
        f"{agg['a_tokens']:>{COL_W['a_tok']},} "
        f"{agg['b_tokens']:>{COL_W['b_tok']},} "
        f"{agg['total_tokens']:>{COL_W['total']},} "
        f"{agg['accuracy']:>{COL_W['acc']}.2f} "
        f"{agg['data_loss']:>{COL_W['loss']}.2f} "
        f"{agg['latency_ms']:>{COL_W['lat']},}ms "
        f"${agg['cost_usd']:>{COL_W['cost'] - 1}.6f}"
    )


def _delta_row(fmt_a: str, fmt_b: str, agg_a: dict, agg_b: dict) -> str:
    def pct(a, b):
        if a == 0:
            return "N/A"
        return f"{(b - a) / a * 100:+.1f}%"

    return (
        f"{'Delta':<{COL_W['format']}} "
        f"{pct(agg_a['a_tokens'], agg_b['a_tokens']):>{COL_W['a_tok']}} "
        f"{pct(agg_a['b_tokens'], agg_b['b_tokens']):>{COL_W['b_tok']}} "
        f"{pct(agg_a['total_tokens'], agg_b['total_tokens']):>{COL_W['total']}} "
        f"{agg_b['accuracy'] - agg_a['accuracy']:>+{COL_W['acc']}.2f} "
        f"{agg_b['data_loss'] - agg_a['data_loss']:>+{COL_W['loss']}.2f} "
        f"{pct(agg_a['latency_ms'], agg_b['latency_ms']):>{COL_W['lat']}} "
        f"{pct(agg_a['cost_usd'], agg_b['cost_usd']):>{COL_W['cost']}}"
    )


def run_test(test: dict, model: str, queries: list) -> dict:
    print(f"\nTEST {test['id']}: {test['name']}")
    print("=" * 80)

    per_format_runs: dict[str, list] = {fmt: [] for fmt in test["formats"]}

    for query in queries:
        print(f"\n  Query [{query['id']}]: {query['question']}")
        for fmt in test["formats"]:
            message = agent_a.prepare_message(query, fmt)
            print(f"    [{fmt.upper()}] {message['a_tokens']} outbound tokens - calling Agent B...", end=" ", flush=True)
            result = agent_b.process(message, query["question"], query["expected_facts"], model=model)
            print(f"acc={result['accuracy']:.2f}  loss={result['data_loss']:.2f}  {result['latency_ms']}ms")
            per_format_runs[fmt].append({
                "query_id": query["id"],
                "a_tokens": message["a_tokens"],
                **result,
            })

    aggregated: dict[str, dict] = {}
    for fmt, runs in per_format_runs.items():
        n = len(runs)
        aggregated[fmt] = {
            "a_tokens": round(sum(r["a_tokens"] for r in runs) / n),
            "b_tokens": round(sum(r["b_tokens"] for r in runs) / n),
            "total_tokens": round(sum(r["total_tokens"] for r in runs) / n),
            "accuracy": round(sum(r["accuracy"] for r in runs) / n, 2),
            "data_loss": round(sum(r["data_loss"] for r in runs) / n, 2),
            "latency_ms": round(sum(r["latency_ms"] for r in runs) / n),
            "cost_usd": round(sum(r["cost_usd"] for r in runs) / n, 6),
        }

    print(f"\n  {'-' * 78}")
    print(f"  {_header_row()}")
    print(f"  {'-' * 78}")
    fmts = test["formats"]
    for fmt in fmts:
        print(f"  {_data_row(fmt, aggregated[fmt])}")
    if len(fmts) == 2:
        print(f"  {_delta_row(fmts[0], fmts[1], aggregated[fmts[0]], aggregated[fmts[1]])}")
    print(f"  {'-' * 78}")

    return {
        "test_id": test["id"],
        "test_name": test["name"],
        "formats": test["formats"],
        "per_query": {fmt: per_format_runs[fmt] for fmt in fmts},
        "aggregated": aggregated,
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 4: agent communication format test")
    parser.add_argument(
        "--model",
        default=agent_b.DEFAULT_MODEL,
        help="Model to use: qwen2.5:14b (default), claude-haiku, claude-sonnet, kimi-k2.5, kimi-k2.6",
    )
    parser.add_argument(
        "--dataset",
        choices=["phase1", "phase2"],
        default="phase1",
        help="Document set to test against: phase1 (AI fairness, 3 queries) or phase2 (Wikipedia, 5 queries)",
    )
    args = parser.parse_args()
    model = args.model

    if args.dataset == "phase2":
        queries = _build_phase2_queries()
        dataset_label = "Phase 2 (Wikipedia)"
    else:
        queries = QUERIES
        dataset_label = "Phase 1 (AI Fairness)"

    RESULTS_DIR.mkdir(exist_ok=True)

    print("AgentClearfeed Phase 4 - Agent Communication Protocol Test")
    print(f"Dataset: {dataset_label}")
    print("Format: ACF vs JSON vs TOON")
    print(f"Model: {model}")
    print(f"Queries: {len(queries)}")

    all_results = []
    for test in TESTS:
        result = run_test(test, model, queries)
        all_results.append(result)

    output = {
        "phase": 4,
        "dataset": args.dataset,
        "model": model,
        "queries": len(queries),
        "tests": all_results,
    }
    safe_model = model.replace(":", "_").replace("/", "_")
    out_path = RESULTS_DIR / f"phase4_results_{args.dataset}_{safe_model}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
