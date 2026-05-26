"""Phase 5-GA Validation — champion schema in A2A.

Tests whether the GA champion (3-field positional header, 636 tokens) maintains
accuracy in agent-to-agent communication vs ACF and JSON.

Phase 4 Haiku baseline for reference:
  ACF:  acc=1.00, 828 total tokens
  JSON: acc=0.89, 932 total tokens
"""

import json
from pathlib import Path

from phase4.orchestrator import run_test
from test_harness.queries import QUERIES

RESULTS_DIR = Path(__file__).parent / "results"

PHASE4_HAIKU_BASELINE = {
    "acf":  {"acc": 1.00, "total_tokens": 828},
    "json": {"acc": 0.89, "total_tokens": 932},
}

VALIDATION_TEST = {
    "id": 1,
    "name": "Champion vs ACF vs JSON",
    "formats": ["champion", "acf", "json"],
}


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    print("Phase 5-GA Validation — Champion in A2A")
    print("Model:   claude-haiku")
    print("Dataset: Phase 1 (AI Fairness, 3 queries)")
    print("Formats: champion vs acf vs json")
    print("=" * 80)

    result = run_test(VALIDATION_TEST, "claude-haiku", QUERIES)

    # --- Comparison vs Phase 4 Haiku baseline ---
    print("\n" + "=" * 80)
    print("Comparison vs Phase 4 Haiku finale:")
    print(f"  {'Format':<10} {'Acc (now)':>10} {'Acc (P4)':>10} {'Tokens (now)':>14} {'Tokens (P4)':>12}")
    print(f"  {'-' * 60}")
    for fmt in ["champion", "acf", "json"]:
        agg = result["aggregated"][fmt]
        baseline = PHASE4_HAIKU_BASELINE.get(fmt, {})
        acc_p4 = f"{baseline['acc']:.2f}" if baseline else "N/A"
        tok_p4 = f"{baseline['total_tokens']:,}" if baseline else "N/A"
        print(f"  {fmt.upper():<10} {agg['accuracy']:>10.2f} {acc_p4:>10} {agg['total_tokens']:>14,} {tok_p4:>12}")

    # --- Save ---
    output = {
        "phase": "5-GA",
        "label": "champion_validation",
        "model": "claude-haiku",
        "dataset": "phase1",
        "queries": len(QUERIES),
        "test": result,
        "phase4_haiku_baseline": PHASE4_HAIKU_BASELINE,
    }
    out_path = RESULTS_DIR / "validation_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
