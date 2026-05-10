"""Phase 3 test harness: dynamic content comparison (HTML vs ACF) with live data."""

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import tiktoken
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from test_harness.phase3.queries_phase3 import PHASE3_QUERIES

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "claude-haiku"
ACF_SERVER = "http://localhost:8000"
RESULTS_DIR = Path(__file__).parent.parent / "results"

CLAUDE_MODELS = {
    "claude-haiku": "claude-haiku-4-5-20251001",
    "claude-sonnet": "claude-sonnet-4-6",
    "claude-opus": "claude-opus-4-7",
}

KIMI_MODELS = {
    "kimi-k2.5": "kimi-k2.5",
    "kimi-k2.6": "kimi-k2.6",
}
KIMI_BASE_URL = "https://api.moonshot.ai/v1"

SYSTEM_PROMPT = (
    "You are a research assistant. You have been given a document. "
    "Answer the question using ONLY the provided context. "
    "Extract the answer precisely as it appears in the document. "
    "Answer concisely and factually."
)


def is_claude_model(model: str) -> bool:
    return model.startswith("claude-")


def is_kimi_model(model: str) -> bool:
    return model.startswith("kimi-")


def resolve_model(model: str) -> str:
    if model in CLAUDE_MODELS:
        return CLAUDE_MODELS[model]
    if model in KIMI_MODELS:
        return KIMI_MODELS[model]
    return model


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def query_claude(prompt: str, context: str, model: str,
                  max_retries: int = 5, base_delay: float = 5.0) -> dict:
    from anthropic import Anthropic, RateLimitError

    client = Anthropic()
    resolved = resolve_model(model)
    user_message = f"CONTEXT:\n{context}\n\nQUESTION: {prompt}"

    context_tokens = count_tokens(context)
    prompt_tokens = count_tokens(user_message + SYSTEM_PROMPT)

    for attempt in range(max_retries + 1):
        try:
            start = time.time()
            message = client.messages.create(
                model=resolved,
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            elapsed = time.time() - start
            break
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"    Rate limited, retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)

    answer = message.content[0].text
    answer_tokens = count_tokens(answer)

    return {
        "answer": answer,
        "context_tokens": context_tokens,
        "prompt_tokens": prompt_tokens,
        "answer_tokens": answer_tokens,
        "total_tokens": prompt_tokens + answer_tokens,
        "latency_seconds": round(elapsed, 2),
        "api_input_tokens": message.usage.input_tokens,
        "api_output_tokens": message.usage.output_tokens,
    }


def query_ollama(prompt: str, context: str, model: str) -> dict:
    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {prompt}"
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


def query_kimi(prompt: str, context: str, model: str,
               max_retries: int = 5, base_delay: float = 5.0) -> dict:
    from openai import OpenAI, RateLimitError

    api_key = os.environ.get("KIMI_API_KEY")
    if not api_key:
        raise RuntimeError("KIMI_API_KEY not set in environment")

    client = OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
    resolved = resolve_model(model)
    user_message = f"CONTEXT:\n{context}\n\nQUESTION: {prompt}"

    context_tokens = count_tokens(context)
    prompt_tokens = count_tokens(user_message + SYSTEM_PROMPT)

    for attempt in range(max_retries + 1):
        try:
            start = time.time()
            response = client.chat.completions.create(
                model=resolved,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            elapsed = time.time() - start
            break
        except RateLimitError:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"    Rate limited, retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)

    answer = response.choices[0].message.content or ""
    answer_tokens = count_tokens(answer)

    return {
        "answer": answer,
        "context_tokens": context_tokens,
        "prompt_tokens": prompt_tokens,
        "answer_tokens": answer_tokens,
        "total_tokens": prompt_tokens + answer_tokens,
        "latency_seconds": round(elapsed, 2),
        "api_input_tokens": response.usage.prompt_tokens,
        "api_output_tokens": response.usage.completion_tokens,
    }


def query_model(prompt: str, context: str, model: str) -> dict:
    if is_claude_model(model):
        return query_claude(prompt, context, model)
    if is_kimi_model(model):
        return query_kimi(prompt, context, model)
    return query_ollama(prompt, context, model)


def extract_numbers(text: str) -> list[float]:
    text = text.replace(",", "")
    return [float(m) for m in re.findall(r"[\-+]?\d+\.?\d*", text)]


def grade_phase3_answer(answer: str, actual_data: dict) -> dict:
    answer_lower = answer.lower()
    actual_price = actual_data["price_usd"]
    actual_change = actual_data["change_24h"]
    hits = []
    misses = []

    if "bitcoin" in answer_lower or "btc" in answer_lower:
        hits.append("BTC or Bitcoin mentioned")
    else:
        misses.append("BTC or Bitcoin mentioned")

    nums = extract_numbers(answer)
    price_found = any(abs(n - actual_price) / actual_price < 0.01 for n in nums)
    if price_found:
        hits.append("bitcoin price in USD")
    else:
        misses.append("bitcoin price in USD")

    change_found = any(abs(n - abs(actual_change)) < 0.5 for n in nums)
    if change_found:
        hits.append("24-hour percentage change")
    else:
        misses.append("24-hour percentage change")

    total = len(hits) + len(misses)
    return {
        "facts_found": len(hits),
        "facts_total": total,
        "accuracy": round(len(hits) / total, 2) if total else 0,
        "hits": hits,
        "misses": misses,
    }


def calc_staleness(fetched_at_iso: str, answer_received_at: float) -> float:
    fetched_ts = datetime.fromisoformat(fetched_at_iso).timestamp()
    return round(answer_received_at - fetched_ts, 2)


def fetch_phase3_content(endpoint: str) -> tuple[str, dict, float]:
    start = time.time()
    resp = httpx.get(f"{ACF_SERVER}{endpoint}", timeout=15.0)
    resp.raise_for_status()
    fetch_time = time.time() - start
    payload = resp.json()
    return payload["content"], payload["data"], fetch_time


def run_test(query: dict, model: str) -> dict:
    print(f"\n{'='*60}")
    print(f"Query [{query['id']}]: {query['question']}")
    print(f"{'='*60}")

    # --- HTML ---
    print("\n  Fetching bloated HTML (live CoinGecko)...")
    html_content, html_data, html_fetch_time = fetch_phase3_content("/phase3/html/bitcoin-price")
    html_ctx_tokens = count_tokens(html_content)
    print(f"  HTML context: {html_ctx_tokens:,} tokens (fetched in {html_fetch_time:.2f}s)")
    print(f"  Live price:   ${html_data['price_usd']:,.2f} ({html_data['change_24h']:+.2f}%)")

    print(f"  Running HTML query...")
    html_result = query_model(query["question"], html_content, model)
    html_answer_received = time.time()
    html_grade = grade_phase3_answer(html_result["answer"], html_data)
    html_staleness = calc_staleness(html_data["fetched_at"], html_answer_received)

    print(f"  HTML: {html_result['context_tokens']:,} ctx tokens, "
          f"{html_result['latency_seconds']}s, "
          f"accuracy {html_grade['accuracy']}, "
          f"staleness {html_staleness}s")

    # --- ACF ---
    print(f"\n  Fetching ACF action (live CoinGecko)...")
    acf_content, acf_data, acf_fetch_time = fetch_phase3_content("/phase3/acf/bitcoin-price")
    acf_ctx_tokens = count_tokens(acf_content)
    print(f"  ACF context:  {acf_ctx_tokens:,} tokens (fetched in {acf_fetch_time:.2f}s)")
    print(f"  Live price:   ${acf_data['price_usd']:,.2f} ({acf_data['change_24h']:+.2f}%)")

    print(f"  Running ACF query...")
    acf_result = query_model(query["question"], acf_content, model)
    acf_answer_received = time.time()
    acf_grade = grade_phase3_answer(acf_result["answer"], acf_data)
    acf_staleness = calc_staleness(acf_data["fetched_at"], acf_answer_received)

    acf_total_latency = round(acf_result["latency_seconds"] + acf_fetch_time, 2)
    token_saving = html_result["context_tokens"] - acf_result["context_tokens"]
    token_saving_pct = round(token_saving / html_result["context_tokens"] * 100, 1)

    print(f"  ACF: {acf_result['context_tokens']:,} ctx tokens, "
          f"{acf_total_latency}s (incl {acf_fetch_time:.2f}s fetch), "
          f"accuracy {acf_grade['accuracy']}, "
          f"staleness {acf_staleness}s")
    print(f"  Token saving: {token_saving:,} ({token_saving_pct}%)")

    print(f"\n  --- Staleness ---")
    print(f"  HTML: {html_staleness}s (data age when agent answered)")
    print(f"  ACF:  {acf_staleness}s (data age when agent answered)")

    result = {
        "query_id": query["id"],
        "question": query["question"],
        "html": {
            **html_result,
            "grade": html_grade,
            "data_served": html_data,
            "fetch_seconds": round(html_fetch_time, 2),
            "staleness_seconds": html_staleness,
        },
        "acf": {
            **acf_result,
            "grade": acf_grade,
            "data_served": acf_data,
            "fetch_overhead_seconds": round(acf_fetch_time, 2),
            "total_latency_seconds": acf_total_latency,
            "staleness_seconds": acf_staleness,
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
            "staleness_diff": round(html_staleness - acf_staleness, 2),
        },
    }
    return result


def print_summary(results: list[dict]):
    print(f"\n{'='*70}")
    print("PHASE 3 SUMMARY — Dynamic Content (Live Bitcoin Price)")
    print(f"{'='*70}")
    print(f"{'Query':<8} {'HTML Tok':>10} {'ACF Tok':>10} "
          f"{'Saving':>8} {'HTML Acc':>9} {'ACF Acc':>9} "
          f"{'HTML Lat':>9} {'ACF Lat':>9} "
          f"{'HTML Stale':>11} {'ACF Stale':>10}")
    print("-" * 110)

    totals = {
        "html_tokens": 0, "acf_tokens": 0,
        "html_acc": 0, "acf_acc": 0,
        "html_lat": 0, "acf_lat": 0,
        "html_stale": 0, "acf_stale": 0,
    }
    for r in results:
        acf_lat = r["acf"]["total_latency_seconds"]
        print(f"{r['query_id']:<8} "
              f"{r['html']['context_tokens']:>10,} "
              f"{r['acf']['context_tokens']:>10,} "
              f"{r['delta']['token_saving_pct']:>7}% "
              f"{r['html']['grade']['accuracy']:>9} "
              f"{r['acf']['grade']['accuracy']:>9} "
              f"{r['html']['latency_seconds']:>8}s "
              f"{acf_lat:>8}s "
              f"{r['html']['staleness_seconds']:>10}s "
              f"{r['acf']['staleness_seconds']:>9}s")
        totals["html_tokens"] += r["html"]["context_tokens"]
        totals["acf_tokens"] += r["acf"]["context_tokens"]
        totals["html_acc"] += r["html"]["grade"]["accuracy"]
        totals["acf_acc"] += r["acf"]["grade"]["accuracy"]
        totals["html_lat"] += r["html"]["latency_seconds"]
        totals["acf_lat"] += acf_lat
        totals["html_stale"] += r["html"]["staleness_seconds"]
        totals["acf_stale"] += r["acf"]["staleness_seconds"]

    n = len(results)
    avg_saving = round((1 - totals["acf_tokens"] / totals["html_tokens"]) * 100, 1)
    print("-" * 110)
    print(f"{'AVG':<8} "
          f"{totals['html_tokens']//n:>10,} "
          f"{totals['acf_tokens']//n:>10,} "
          f"{avg_saving:>7}% "
          f"{totals['html_acc']/n:>9.2f} "
          f"{totals['acf_acc']/n:>9.2f} "
          f"{totals['html_lat']/n:>8.1f}s "
          f"{totals['acf_lat']/n:>8.1f}s "
          f"{totals['html_stale']/n:>10.1f}s "
          f"{totals['acf_stale']/n:>9.1f}s")
    print(f"\nOverall token reduction: {avg_saving}%")
    if totals["acf_lat"] > 0:
        print(f"Speedup: {totals['html_lat']/totals['acf_lat']:.1f}x (including ACF fetch overhead)")

    total_api_in = sum(
        r["html"].get("api_input_tokens", 0) + r["acf"].get("api_input_tokens", 0)
        for r in results
    )
    total_api_out = sum(
        r["html"].get("api_output_tokens", 0) + r["acf"].get("api_output_tokens", 0)
        for r in results
    )
    if total_api_in > 0:
        print(f"\nAPI usage: {total_api_in:,} input tokens, {total_api_out:,} output tokens")


def main():
    parser = argparse.ArgumentParser(description="Phase 3: dynamic content ACF vs HTML")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()
    model = args.model

    if is_claude_model(model):
        resolved = resolve_model(model)
        print(f"Using Claude API: {model} -> {resolved}")
        import anthropic
        try:
            anthropic.Anthropic()
        except anthropic.AuthenticationError:
            print("ERROR: Set ANTHROPIC_API_KEY environment variable")
            return
    elif is_kimi_model(model):
        resolved = resolve_model(model)
        print(f"Using Kimi API: {model} -> {resolved}")
        if not os.environ.get("KIMI_API_KEY"):
            print("ERROR: Set KIMI_API_KEY environment variable")
            return

    RESULTS_DIR.mkdir(exist_ok=True)

    print(f"AgentClearfeed Phase 3 — Dynamic Content Test (Live Bitcoin Price)")
    print(f"Model: {model}")
    print(f"Queries: {len(PHASE3_QUERIES)}")
    print(f"Source: CoinGecko API (live)")

    results = []
    for query in PHASE3_QUERIES:
        result = run_test(query, model)
        results.append(result)

    print_summary(results)

    safe_model_name = model.replace(":", "_").replace("/", "_")
    output_path = RESULTS_DIR / f"results_phase3_{safe_model_name}.json"
    output_data = {
        "phase": 3,
        "test_type": "dynamic_content",
        "model": model,
        "num_queries": len(PHASE3_QUERIES),
        "data_source": "CoinGecko API (live)",
        "results": results,
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nDetailed results saved to {output_path}")


if __name__ == "__main__":
    main()
