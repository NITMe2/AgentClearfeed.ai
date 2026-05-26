"""Phase 5 Step 1 — establish llama3.1:8b baseline on Phase 4 tests.

Reuses the Phase 4 orchestrator directly; only the model and output path differ.
Run before ga.py — the ACF row from these results is the target to beat.
"""

import json
from pathlib import Path

from phase4.orchestrator import TESTS, run_test
from test_harness.queries import QUERIES

MODEL = "llama3.1:8b"
RESULTS_DIR = Path(__file__).parent / "results"


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    print("AgentClearfeed Phase 5 — Baseline (llama3.1:8b)")
    print(f"Model:   {MODEL}")
    print(f"Dataset: Phase 1 (AI Fairness, {len(QUERIES)} queries)")
    print("Formats: ACF vs JSON vs TOON")
    print("=" * 80)

    all_results = []
    for test in TESTS:
        result = run_test(test, MODEL, QUERIES)
        all_results.append(result)

    output = {
        "phase": 5,
        "step": "baseline",
        "model": MODEL,
        "dataset": "phase1",
        "queries": len(QUERIES),
        "tests": all_results,
    }

    out_path = RESULTS_DIR / "baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nBaseline results saved to {out_path}")

    # Surface the ACF numbers — that's what the GA will try to beat
    test4 = next(t for t in all_results if t["test_id"] == 4)
    acf = test4["aggregated"].get("acf", {})
    print(f"\nACF baseline — tokens: {acf.get('total_tokens', '?')}, accuracy: {acf.get('accuracy', '?')}")
    print("This is the benchmark the GA must beat.")


if __name__ == "__main__":
    main()
