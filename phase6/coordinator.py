"""Coordinator — single-call and explicit 3-agent topologies."""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openai import OpenAI
from anthropic import Anthropic
from phase4.agent_b import (
    count_tokens,
    grade_answer,
    _SYSTEM,
    KIMI_MODELS,
    CLAUDE_MODELS,
    COST_PER_1M,
    _DEFAULT_COST,
    resolve_model,
)

KIMI_BASE_URL = "https://api.moonshot.ai/v1"
MAX_ANSWER_TOKENS = 1024
SUB_AGENT_MAX_TOKENS = 512


# ── Kimi single-call (kept for standard run) ─────────────────────────────────

def _call_kimi_coordinator(question: str, combined: str, model: str,
                            swarm: bool = False) -> tuple[str, int]:
    api_key = os.environ.get("KIMI_API_KEY")
    if not api_key:
        raise RuntimeError("KIMI_API_KEY not set")
    client = OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
    kwargs = dict(
        model=resolve_model(model),
        max_tokens=MAX_ANSWER_TOKENS,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"CONTEXT:\n{combined}\n\nQUESTION: {question}"},
        ],
    )
    if swarm:
        kwargs["extra_body"] = {"agent": {"type": "swarm", "max_agents": 5, "max_steps": 200}}

    start = time.time()
    for attempt in range(5):
        try:
            resp = client.chat.completions.create(**kwargs)
            latency_ms = round((time.time() - start) * 1000)
            return resp.choices[0].message.content or "", latency_ms
        except Exception as e:
            if "429" in str(e) or "overloaded" in str(e).lower() or "rate" in str(e).lower():
                wait = 10 * (2 ** attempt)
                print(f"    Rate limited — retrying in {wait}s (attempt {attempt+1}/5)...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Kimi rate limit: max retries exceeded")


# ── Claude Haiku helpers (explicit topology) ──────────────────────────────────

def _call_claude(messages: list[dict], model: str, max_tokens: int) -> tuple[str, int]:
    client = Anthropic()
    start = time.time()
    for attempt in range(5):
        try:
            msg = client.messages.create(
                model=resolve_model(model),
                max_tokens=max_tokens,
                system=_SYSTEM,
                messages=messages,
            )
            latency_ms = round((time.time() - start) * 1000)
            return msg.content[0].text, latency_ms
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower() or "overloaded" in str(e).lower():
                wait = 5 * (2 ** attempt)
                print(f"    Rate limited — retrying in {wait}s (attempt {attempt+1}/5)...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Claude rate limit: max retries exceeded")


def _call_claude_sub_agent(content: str, question: str, model: str) -> tuple[str, int]:
    return _call_claude(
        [{"role": "user", "content": f"CONTEXT:\n{content}\n\nQUESTION: {question}"}],
        model, SUB_AGENT_MAX_TOKENS,
    )


def _call_claude_coordinator(question: str, combined: str, model: str) -> tuple[str, int]:
    return _call_claude(
        [{"role": "user", "content": f"CONTEXT:\n{combined}\n\nQUESTION: {question}"}],
        model, MAX_ANSWER_TOKENS,
    )


# ── Public: standard single-call synthesize ───────────────────────────────────

def synthesize(
    summaries: list[dict],
    question: str,
    expected_facts: list[str],
    model: str = "kimi-k2.5",
    swarm: bool = False,
) -> dict:
    """Single coordinator call with all 3 formatted docs concatenated."""
    combined = "\n\n---SOURCE---\n\n".join(s["content"] for s in summaries)
    full_prompt = f"{_SYSTEM}\n\nCONTEXT:\n{combined}\n\nQUESTION: {question}\n"
    b_tokens = count_tokens(full_prompt)

    total_context_tokens = sum(s["a_tokens"] for s in summaries)
    per_fetcher_tokens = round(total_context_tokens / len(summaries))

    answer, latency_ms = _call_kimi_coordinator(question, combined, model, swarm=swarm)

    grade = grade_answer(answer, expected_facts)
    total_tokens = total_context_tokens + b_tokens
    cost_per_1m = COST_PER_1M.get(model, _DEFAULT_COST)
    cost_usd = round(total_tokens / 1_000_000 * cost_per_1m, 6)

    return {
        "answer": answer,
        "per_fetcher_tokens": per_fetcher_tokens,
        "total_context_tokens": total_context_tokens,
        "b_tokens": b_tokens,
        "total_tokens": total_tokens,
        "accuracy": grade["accuracy"],
        "data_loss": round(1.0 - grade["accuracy"], 2),
        "grade": grade,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "swarm": swarm,
    }


# ── Public: explicit 3-agent synthesize ───────────────────────────────────────

def synthesize_explicit(
    summaries: list[dict],
    question: str,
    expected_facts: list[str],
    model: str = "claude-haiku",
) -> dict:
    """3 parallel Haiku sub-agents (one per doc) → 1 Haiku coordinator."""
    total_context_tokens = sum(s["a_tokens"] for s in summaries)
    per_fetcher_tokens = round(total_context_tokens / len(summaries))

    # Parallel sub-agent calls
    sub_answers = [None] * len(summaries)
    sub_latencies = [0] * len(summaries)

    wall_start = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_call_claude_sub_agent, s["content"], question, model): i
            for i, s in enumerate(summaries)
        }
        for fut in as_completed(futures):
            i = futures[fut]
            sub_answers[i], sub_latencies[i] = fut.result()
    sub_agent_latency_ms = round((time.time() - wall_start) * 1000)

    # Coordinator call
    combined = "\n\n---AGENT---\n\n".join(sub_answers)
    coordinator_prompt = f"{_SYSTEM}\n\nCONTEXT:\n{combined}\n\nQUESTION: {question}\n"
    b_tokens = count_tokens(coordinator_prompt)

    final_answer, synthesis_latency_ms = _call_claude_coordinator(question, combined, model)

    grade = grade_answer(final_answer, expected_facts)
    total_tokens = total_context_tokens + b_tokens
    cost_per_1m = COST_PER_1M.get(model, _DEFAULT_COST)
    cost_usd = round(total_tokens / 1_000_000 * cost_per_1m, 6)

    return {
        "answer": final_answer,
        "sub_answers": sub_answers,
        "per_fetcher_tokens": per_fetcher_tokens,
        "total_context_tokens": total_context_tokens,
        "sub_agent_latency_ms": sub_agent_latency_ms,
        "b_tokens": b_tokens,
        "synthesis_latency_ms": synthesis_latency_ms,
        "total_tokens": total_tokens,
        "latency_ms": sub_agent_latency_ms + synthesis_latency_ms,
        "accuracy": grade["accuracy"],
        "data_loss": round(1.0 - grade["accuracy"], 2),
        "grade": grade,
        "cost_usd": cost_usd,
        "mode": "explicit",
    }
