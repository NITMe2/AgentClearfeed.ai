"""Phase 2 test harness: multi-document retrieval comparison (HTML vs ACF)."""

import argparse
import json
import time
from pathlib import Path

import httpx
import tiktoken

from test_harness.phase2.queries_phase2 import PHASE2_QUERIES, PHASE2_TOPICS

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:14b"
ACF_SERVER = "http://localhost:8000"
RAW_DIR = Path(__file__).parent / "raw_sources"
RESULTS_DIR = Path(__file__).parent.parent / "results"

HTML_SEPARATOR = "\n\n<!-- === DOCUMENT BOUNDARY === -->\n\n"
ACF_SEPARATOR = "\n\n===\n\n"


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def query_ollama(prompt: str, context: str, model: str) -> dict:
    full_prompt = (
        "You are a research assistant. You have been given a collection of documents.\n"
        "Answer the question using ONLY the provided context.\n"
        "Find the relevant document and extract the answer.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {prompt}\n\n"
        "Answer concisely and factually."
    )
    context_tokens = count_tokens(context)
    prompt_tokens = count_tokens(full_prompt)

    start = time.time()
    resp = httpx.post(
        OLLAMA_URL,
        json={"model": model, "prompt": full_prompt, "stream": False},
        timeout=900.0,
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


def load_all_html() -> tuple[str, dict]:
    parts = []
    per_topic = {}
    for topic in PHASE2_TOPICS:
        path = RAW_DIR / topic["html_file"]
        html = path.read_text(encoding="utf-8")
        tokens = count_tokens(html)
        per_topic[topic["id"]] = tokens
        parts.append(html)
    combined = HTML_SEPARATOR.join(parts)
    return combined, per_topic


def fetch_all_acf() -> tuple[str, dict, float]:
    parts = []
    per_topic = {}
    total_fetch_time = 0.0
    for topic in PHASE2_TOPICS:
        start = time.time()
        resp = httpx.get(
            f"{ACF_SERVER}/acf/document/{topic['acf_doc']}", timeout=10.0
        )
        resp.raise_for_status()
        fetch_elapsed = time.time() - start
        total_fetch_time += fetch_elapsed

        acf_text = resp.text
        tokens = count_tokens(acf_text)
        per_topic[topic["id"]] = tokens
        parts.append(acf_text)
    combined = ACF_SEPARATOR.join(parts)
    return combined, per_topic, total_fetch_time


def run_test(query: dict, html_context: str, acf_context: str,
             acf_fetch_time: float, model: str) -> dict:
    print(f"\n{'='*60}")
    print(f"Query [{query['id']}]: {query['question']}")
    print(f"Target topic: {query['target_topic']}")
    print(f"{'='*60}")

    html_ctx_tokens = count_tokens(html_context)
    acf_ctx_tokens = count_tokens(acf_context)
    print(f"  HTML context: {html_ctx_tokens:,} tokens (all 10 docs)")
    print(f"  ACF context:  {acf_ctx_tokens:,} tokens (all 10 docs)")
    print(f"  Ratio:        {html_ctx_tokens / acf_ctx_tokens:.1f}x")

    print("\n  Running HTML query (10-doc haystack)...")
    html_result = query_ollama(query["question"], html_context, model)
    html_grade = grade_answer(html_result["answer"], query["expected_facts"])

    print(f"  Running ACF query (10-doc haystack, +{acf_fetch_time:.2f}s fetch overhead)...")
    acf_result = query_ollama(query["question"], acf_context, model)
    acf_grade = grade_answer(acf_result["answer"], query["expected_facts"])

    acf_total_latency = round(acf_result["latency_seconds"] + acf_fetch_time, 2)

    token_saving = html_result["context_tokens"] - acf_result["context_tokens"]
    token_saving_pct = round(token_saving / html_result["context_tokens"] * 100, 1)

    print(f"\n  --- Results ---")
    print(f"  HTML: {html_result['context_tokens']:,} ctx tokens, "
          f"{html_result['latency_seconds']}s, "
          f"accuracy {html_grade['accuracy']}")
    print(f"  ACF:  {acf_result['context_tokens']:,} ctx tokens, "
          f"{acf_total_latency}s (incl {acf_fetch_time:.2f}s fetch), "
          f"accuracy {acf_grade['accuracy']}")
    print(f"  Token saving: {token_saving:,} ({token_saving_pct}%)")

    return {
        "query_id": query["id"],
        "question": query["question"],
        "target_topic": query["target_topic"],
        "html": {**html_result, "grade": html_grade},
        "acf": {
            **acf_result,
            "fetch_overhead_seconds": round(acf_fetch_time, 2),
            "total_latency_seconds": acf_total_latency,
            "grade": acf_grade,
        },
        "delta": {
            "token_saving": token_saving,
            "token_saving_pct": token_saving_pct,
            "latency_diff": round(
                html_result["latency_seconds"] - acf_total_latency, 2
            ),
            "accuracy_diff": round(
                acf_grade["accuracy"] - html_grade["accuracy"], 2
            ),
        },
    }


def print_summary(results: list[dict]):
    print(f"\n{'='*70}")
    print("PHASE 2 SUMMARY — Multi-Document Retrieval (10 docs)")
    print(f"{'='*70}")
    print(f"{'Query':<8} {'Target':<16} {'HTML Tok':>10} {'ACF Tok':>10} "
          f"{'Saving':>8} {'HTML Acc':>9} {'ACF Acc':>9} "
          f"{'HTML Lat':>9} {'ACF Lat':>9}")
    print("-" * 100)

    totals = {
        "html_tokens": 0, "acf_tokens": 0,
        "html_acc": 0, "acf_acc": 0,
        "html_lat": 0, "acf_lat": 0,
    }
    for r in results:
        acf_lat = r["acf"]["total_latency_seconds"]
        print(f"{r['query_id']:<8} "
              f"{r['target_topic']:<16} "
              f"{r['html']['context_tokens']:>10,} "
              f"{r['acf']['context_tokens']:>10,} "
              f"{r['delta']['token_saving_pct']:>7}% "
              f"{r['html']['grade']['accuracy']:>9} "
              f"{r['acf']['grade']['accuracy']:>9} "
              f"{r['html']['latency_seconds']:>8}s "
              f"{acf_lat:>8}s")
        totals["html_tokens"] += r["html"]["context_tokens"]
        totals["acf_tokens"] += r["acf"]["context_tokens"]
        totals["html_acc"] += r["html"]["grade"]["accuracy"]
        totals["acf_acc"] += r["acf"]["grade"]["accuracy"]
        totals["html_lat"] += r["html"]["latency_seconds"]
        totals["acf_lat"] += acf_lat

    n = len(results)
    avg_saving = round((1 - totals["acf_tokens"] / totals["html_tokens"]) * 100, 1)
    print("-" * 100)
    print(f"{'AVG':<8} {'':16} "
          f"{totals['html_tokens']//n:>10,} "
          f"{totals['acf_tokens']//n:>10,} "
          f"{avg_saving:>7}% "
          f"{totals['html_acc']/n:>9.2f} "
          f"{totals['acf_acc']/n:>9.2f} "
          f"{totals['html_lat']/n:>8.1f}s "
          f"{totals['acf_lat']/n:>8.1f}s")
    print(f"\nOverall token reduction: {avg_saving}%")
    if totals["acf_lat"] > 0:
        print(f"Speedup: {totals['html_lat']/totals['acf_lat']:.1f}x (including ACF fetch overhead)")


def main():
    parser = argparse.ArgumentParser(description="Phase 2: multi-document ACF vs HTML")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Ollama model (default: {DEFAULT_MODEL})")
    args = parser.parse_args()
    model = args.model

    RESULTS_DIR.mkdir(exist_ok=True)

    print("AgentClearfeed Phase 2 — Multi-Document Retrieval Test")
    print(f"Model: {model}")
    print(f"Documents: {len(PHASE2_TOPICS)} topics")
    print(f"Queries: {len(PHASE2_QUERIES)} questions")

    print("\nLoading HTML contexts...")
    html_context, html_per_topic = load_all_html()
    html_total_tokens = count_tokens(html_context)
    print(f"  Total HTML context: {html_total_tokens:,} tokens")

    if html_total_tokens > 120_000:
        print(f"  WARNING: HTML context ({html_total_tokens:,} tokens) may exceed "
              f"model context window. Consider reducing page sizes.")

    print("\nFetching ACF contexts from server...")
    acf_context, acf_per_topic, acf_fetch_time = fetch_all_acf()
    acf_total_tokens = count_tokens(acf_context)
    print(f"  Total ACF context: {acf_total_tokens:,} tokens")
    print(f"  ACF fetch time: {acf_fetch_time:.2f}s (realistic conversion layer overhead)")

    print("\nPer-topic token breakdown:")
    for topic in PHASE2_TOPICS:
        tid = topic["id"]
        html_t = html_per_topic[tid]
        acf_t = acf_per_topic[tid]
        print(f"  {tid:<25} HTML: {html_t:>8,}  ACF: {acf_t:>6,}  Ratio: {html_t/acf_t:.0f}x")

    results = []
    for query in PHASE2_QUERIES:
        result = run_test(query, html_context, acf_context, acf_fetch_time, model)
        results.append(result)

    print_summary(results)

    safe_model_name = model.replace(":", "_").replace("/", "_")
    output_path = RESULTS_DIR / f"results_phase2_{safe_model_name}.json"
    output_data = {
        "phase": 2,
        "model": model,
        "num_documents": len(PHASE2_TOPICS),
        "num_queries": len(PHASE2_QUERIES),
        "html_total_tokens": html_total_tokens,
        "acf_total_tokens": acf_total_tokens,
        "acf_fetch_overhead_seconds": round(acf_fetch_time, 2),
        "per_topic_tokens": {
            "html": html_per_topic,
            "acf": acf_per_topic,
        },
        "results": results,
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nDetailed results saved to {output_path}")


if __name__ == "__main__":
    main()
