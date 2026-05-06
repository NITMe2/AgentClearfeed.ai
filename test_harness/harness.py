"""Test harness: compare agent performance on raw HTML vs ACF content."""

import json
import time
from pathlib import Path

import httpx
import tiktoken

from test_harness.queries import QUERIES

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:14b"
ACF_SERVER = "http://localhost:8000"
RAW_DIR = Path(__file__).parent / "raw_sources"
RESULTS_DIR = Path(__file__).parent / "results"


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def query_ollama(prompt: str, context: str) -> dict:
    full_prompt = (
        f"You are a research assistant. Answer the question using ONLY the provided context.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {prompt}\n\n"
        f"Answer concisely and factually."
    )

    context_tokens = count_tokens(context)
    prompt_tokens = count_tokens(full_prompt)

    start = time.time()
    resp = httpx.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False},
        timeout=600.0,
    )
    elapsed = time.time() - start

    data = resp.json()
    answer = data.get("response", "")
    answer_tokens = count_tokens(answer)

    return {
        "answer": answer,
        "context_tokens": context_tokens,
        "prompt_tokens": prompt_tokens,
        "answer_tokens": answer_tokens,
        "total_tokens": prompt_tokens + answer_tokens,
        "latency_seconds": round(elapsed, 2),
    }


def grade_answer(answer: str, expected_facts: list[str]) -> dict:
    answer_lower = answer.lower()
    hits = []
    misses = []
    for fact in expected_facts:
        words = fact.lower().split()
        key_words = [w for w in words if len(w) > 3]
        matched = sum(1 for w in key_words if w in answer_lower)
        if matched >= len(key_words) * 0.5:
            hits.append(fact)
        else:
            misses.append(fact)
    return {
        "facts_found": len(hits),
        "facts_total": len(expected_facts),
        "accuracy": round(len(hits) / len(expected_facts), 2) if expected_facts else 0,
        "hits": hits,
        "misses": misses,
    }


def fetch_acf_content(doc_id: str) -> str:
    resp = httpx.get(f"{ACF_SERVER}/acf/document/{doc_id}", timeout=10.0)
    resp.raise_for_status()
    return resp.text


def load_html_content(filename: str) -> str:
    return (RAW_DIR / filename).read_text(encoding="utf-8")


def run_test(query: dict) -> dict:
    print(f"\n{'='*60}")
    print(f"Query: {query['question']}")
    print(f"{'='*60}")

    html_content = load_html_content(query["html_file"])
    acf_content = fetch_acf_content(query["acf_doc"])

    print(f"\n  HTML context: {count_tokens(html_content)} tokens")
    print(f"  ACF context:  {count_tokens(acf_content)} tokens")
    print(f"  Ratio:        {count_tokens(html_content) / count_tokens(acf_content):.1f}x")

    print("\n  Running HTML query...")
    html_result = query_ollama(query["question"], html_content)
    html_grade = grade_answer(html_result["answer"], query["expected_facts"])

    print("  Running ACF query...")
    acf_result = query_ollama(query["question"], acf_content)
    acf_grade = grade_answer(acf_result["answer"], query["expected_facts"])

    token_saving = html_result["context_tokens"] - acf_result["context_tokens"]
    token_saving_pct = round(token_saving / html_result["context_tokens"] * 100, 1)

    print(f"\n  --- Results ---")
    print(f"  HTML: {html_result['context_tokens']} ctx tokens, "
          f"{html_result['latency_seconds']}s, "
          f"accuracy {html_grade['accuracy']}")
    print(f"  ACF:  {acf_result['context_tokens']} ctx tokens, "
          f"{acf_result['latency_seconds']}s, "
          f"accuracy {acf_grade['accuracy']}")
    print(f"  Token saving: {token_saving} ({token_saving_pct}%)")

    return {
        "query_id": query["id"],
        "question": query["question"],
        "html": {**html_result, "grade": html_grade},
        "acf": {**acf_result, "grade": acf_grade},
        "delta": {
            "token_saving": token_saving,
            "token_saving_pct": token_saving_pct,
            "latency_diff": round(
                html_result["latency_seconds"] - acf_result["latency_seconds"], 2
            ),
            "accuracy_diff": round(
                acf_grade["accuracy"] - html_grade["accuracy"], 2
            ),
        },
    }


def print_summary(results: list[dict]):
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Query':<8} {'HTML Tokens':>12} {'ACF Tokens':>12} {'Saving':>8} "
          f"{'HTML Acc':>9} {'ACF Acc':>9} {'HTML Lat':>9} {'ACF Lat':>9}")
    print("-" * 90)

    totals = {"html_tokens": 0, "acf_tokens": 0, "html_acc": 0, "acf_acc": 0}
    for r in results:
        print(f"{r['query_id']:<8} "
              f"{r['html']['context_tokens']:>12} "
              f"{r['acf']['context_tokens']:>12} "
              f"{r['delta']['token_saving_pct']:>7}% "
              f"{r['html']['grade']['accuracy']:>9} "
              f"{r['acf']['grade']['accuracy']:>9} "
              f"{r['html']['latency_seconds']:>8}s "
              f"{r['acf']['latency_seconds']:>8}s")
        totals["html_tokens"] += r["html"]["context_tokens"]
        totals["acf_tokens"] += r["acf"]["context_tokens"]
        totals["html_acc"] += r["html"]["grade"]["accuracy"]
        totals["acf_acc"] += r["acf"]["grade"]["accuracy"]

    n = len(results)
    avg_saving = round((1 - totals["acf_tokens"] / totals["html_tokens"]) * 100, 1)
    print("-" * 90)
    print(f"{'AVG':<8} "
          f"{totals['html_tokens']//n:>12} "
          f"{totals['acf_tokens']//n:>12} "
          f"{avg_saving:>7}% "
          f"{totals['html_acc']/n:>9.2f} "
          f"{totals['acf_acc']/n:>9.2f}")
    print(f"\nOverall token reduction: {avg_saving}%")


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    print("AgentClearfeed Test Harness")
    print("Comparing raw HTML vs ACF format for agent consumption")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"ACF Server: {ACF_SERVER}")

    results = []
    for query in QUERIES:
        result = run_test(query)
        results.append(result)

    print_summary(results)

    output_path = RESULTS_DIR / "results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to {output_path}")


if __name__ == "__main__":
    main()
