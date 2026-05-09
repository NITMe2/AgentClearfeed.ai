"""Phase 2 test harness: multi-document retrieval comparison (HTML vs ACF)."""

import argparse
import json
import os
import time
from pathlib import Path

import httpx
import tiktoken
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from test_harness.phase2.queries_phase2 import PHASE2_QUERIES, PHASE2_TOPICS

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:14b"
ACF_SERVER = "http://localhost:8000"
RAW_DIR = Path(__file__).parent / "raw_sources"
RESULTS_DIR = Path(__file__).parent.parent / "results"

HTML_SEPARATOR = "\n\n<!-- === DOCUMENT BOUNDARY === -->\n\n"
ACF_SEPARATOR = "\n\n===\n\n"

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
    "You are a research assistant. You have been given a collection of documents. "
    "Answer the question using ONLY the provided context. "
    "Find the relevant document and extract the answer. "
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
               swarm: bool = False,
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

    kwargs = {}
    if swarm:
        kwargs["extra_body"] = {
            "agent": {
                "type": "swarm",
                "max_agents": 10,
                "max_steps": 500,
            }
        }

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
                **kwargs,
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


def query_model(prompt: str, context: str, model: str,
                swarm: bool = False) -> dict:
    if is_claude_model(model):
        return query_claude(prompt, context, model)
    if is_kimi_model(model):
        return query_kimi(prompt, context, model, swarm=swarm)
    return query_ollama(prompt, context, model)


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
             acf_fetch_time: float, model: str,
             html_only: bool = False, swarm: bool = False) -> dict:
    print(f"\n{'='*60}")
    print(f"Query [{query['id']}]: {query['question']}")
    print(f"Target topic: {query['target_topic']}")
    if swarm:
        print(f"Mode: Agent Swarm")
    print(f"{'='*60}")

    html_ctx_tokens = count_tokens(html_context)
    print(f"  HTML context: {html_ctx_tokens:,} tokens (all 10 docs)")
    if not html_only:
        acf_ctx_tokens = count_tokens(acf_context)
        print(f"  ACF context:  {acf_ctx_tokens:,} tokens (all 10 docs)")
        print(f"  Ratio:        {html_ctx_tokens / acf_ctx_tokens:.1f}x")

    print(f"\n  Running HTML query{'  [SWARM]' if swarm else ''} (10-doc haystack)...")
    html_result = query_model(query["question"], html_context, model, swarm=swarm)
    html_grade = grade_answer(html_result["answer"], query["expected_facts"])

    print(f"\n  --- Results ---")
    print(f"  HTML: {html_result['context_tokens']:,} ctx tokens, "
          f"{html_result['latency_seconds']}s, "
          f"accuracy {html_grade['accuracy']}")

    result = {
        "query_id": query["id"],
        "question": query["question"],
        "target_topic": query["target_topic"],
        "swarm": swarm,
        "html": {**html_result, "grade": html_grade},
    }

    if not html_only:
        print(f"  Running ACF query (10-doc haystack, +{acf_fetch_time:.2f}s fetch overhead)...")
        acf_result = query_model(query["question"], acf_context, model)
        acf_grade = grade_answer(acf_result["answer"], query["expected_facts"])

        acf_total_latency = round(acf_result["latency_seconds"] + acf_fetch_time, 2)
        token_saving = html_result["context_tokens"] - acf_result["context_tokens"]
        token_saving_pct = round(token_saving / html_result["context_tokens"] * 100, 1)

        print(f"  ACF:  {acf_result['context_tokens']:,} ctx tokens, "
              f"{acf_total_latency}s (incl {acf_fetch_time:.2f}s fetch), "
              f"accuracy {acf_grade['accuracy']}")
        print(f"  Token saving: {token_saving:,} ({token_saving_pct}%)")

        result["acf"] = {
            **acf_result,
            "fetch_overhead_seconds": round(acf_fetch_time, 2),
            "total_latency_seconds": acf_total_latency,
            "grade": acf_grade,
        }
        result["delta"] = {
            "token_saving": token_saving,
            "token_saving_pct": token_saving_pct,
            "latency_diff": round(
                html_result["latency_seconds"] - acf_total_latency, 2
            ),
            "accuracy_diff": round(
                acf_grade["accuracy"] - html_grade["accuracy"], 2
            ),
        }

    return result


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
    parser = argparse.ArgumentParser(description="Phase 2: multi-document ACF vs HTML")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Ollama model or claude-haiku/claude-sonnet/claude-opus/kimi-k2.5/kimi-k2.6 (default: {DEFAULT_MODEL})")
    parser.add_argument("--swarm", action="store_true",
                        help="Enable Kimi Agent Swarm mode (only works with kimi- models)")
    parser.add_argument("--html-only", action="store_true",
                        help="Only run HTML queries, skip ACF")
    args = parser.parse_args()
    model = args.model

    if args.swarm and not is_kimi_model(model):
        print("ERROR: --swarm only works with kimi- models")
        return

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

    mode_label = ""
    if args.swarm:
        mode_label = " [Agent Swarm]"
    if args.html_only:
        mode_label += " [HTML-only]"

    print(f"AgentClearfeed Phase 2 — Multi-Document Retrieval Test{mode_label}")
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

    acf_context = ""
    acf_per_topic = {}
    acf_fetch_time = 0.0
    acf_total_tokens = 0

    if not args.html_only:
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
    for i, query in enumerate(PHASE2_QUERIES):
        result = run_test(query, html_context, acf_context, acf_fetch_time, model,
                          html_only=args.html_only, swarm=args.swarm)
        results.append(result)

    if not args.html_only:
        print_summary(results)

    safe_model_name = model.replace(":", "_").replace("/", "_")
    suffix = "_swarm" if args.swarm else ""
    suffix += "_html_only" if args.html_only else ""
    output_path = RESULTS_DIR / f"results_phase2_{safe_model_name}{suffix}.json"
    output_data = {
        "phase": 2,
        "model": model,
        "swarm": args.swarm,
        "html_only": args.html_only,
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
