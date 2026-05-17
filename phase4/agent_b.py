"""Agent B — receives a formatted message, queries a model, returns graded metrics."""

import os
import time

import httpx
import tiktoken
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:14b"

CLAUDE_MODELS = {
    "claude-haiku":  "claude-haiku-4-5-20251001",
    "claude-sonnet": "claude-sonnet-4-6",
    "claude-opus":   "claude-opus-4-7",
}
KIMI_MODELS = {
    "kimi-k2.5": "kimi-k2.5",
    "kimi-k2.6": "kimi-k2.6",
}
KIMI_BASE_URL = "https://api.moonshot.ai/v1"

# Cost per 1M tokens (input) — used for estimation
COST_PER_1M = {
    "claude-haiku":  0.80,
    "claude-sonnet": 3.00,
    "claude-opus":  15.00,
    "kimi-k2.5":     0.30,
    "kimi-k2.6":     0.30,
}
_DEFAULT_COST = 0.30

_ENC = tiktoken.get_encoding("cl100k_base")

_SYSTEM = (
    "You are a research assistant. "
    "Answer the question using ONLY the provided context. "
    "Answer concisely and factually."
)


def count_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def resolve_model(model: str) -> str:
    if model in CLAUDE_MODELS:
        return CLAUDE_MODELS[model]
    if model in KIMI_MODELS:
        return KIMI_MODELS[model]
    return model


def is_claude(model: str) -> bool:
    return model.startswith("claude-")


def is_kimi(model: str) -> bool:
    return model.startswith("kimi-")


def grade_answer(answer: str, expected_facts: list[str]) -> dict:
    answer_lower = answer.lower()
    hits, misses = [], []
    for fact in expected_facts:
        words = fact.lower().split()
        key_words = [w for w in words if len(w) > 3]
        matched = sum(1 for w in key_words if w in answer_lower)
        if matched >= len(key_words) * 0.5:
            hits.append(fact)
        else:
            misses.append(fact)
    accuracy = round(len(hits) / len(expected_facts), 2) if expected_facts else 0.0
    return {
        "facts_found": len(hits),
        "facts_total": len(expected_facts),
        "accuracy": accuracy,
        "hits": hits,
        "misses": misses,
    }


def _call_ollama(full_prompt: str, model: str) -> tuple[str, int]:
    start = time.time()
    resp = httpx.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"seed": 42, "temperature": 0},
        },
        timeout=600.0,
    )
    latency_ms = round((time.time() - start) * 1000)
    return resp.json().get("response", ""), latency_ms


def _call_claude(question: str, context: str, model: str) -> tuple[str, int]:
    from anthropic import Anthropic
    client = Anthropic()
    start = time.time()
    msg = client.messages.create(
        model=resolve_model(model),
        max_tokens=512,
        system=_SYSTEM,
        messages=[{"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}],
    )
    latency_ms = round((time.time() - start) * 1000)
    return msg.content[0].text, latency_ms


def _call_kimi(question: str, context: str, model: str) -> tuple[str, int]:
    from openai import OpenAI
    api_key = os.environ.get("KIMI_API_KEY")
    if not api_key:
        raise RuntimeError("KIMI_API_KEY not set")
    client = OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
    start = time.time()
    resp = client.chat.completions.create(
        model=resolve_model(model),
        max_tokens=512,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"},
        ],
    )
    latency_ms = round((time.time() - start) * 1000)
    return resp.choices[0].message.content or "", latency_ms


def process(message: dict, question: str, expected_facts: list[str],
            model: str = DEFAULT_MODEL) -> dict:
    """Send message + question to the chosen model and return graded metrics."""
    context = message["content"]

    if is_claude(model):
        answer, latency_ms = _call_claude(question, context, model)
        user_msg = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
        b_tokens = count_tokens(_SYSTEM + user_msg)
    elif is_kimi(model):
        answer, latency_ms = _call_kimi(question, context, model)
        user_msg = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
        b_tokens = count_tokens(_SYSTEM + user_msg)
    else:
        full_prompt = f"{_SYSTEM}\n\nCONTEXT:\n{context}\n\nQUESTION: {question}\n"
        answer, latency_ms = _call_ollama(full_prompt, model)
        b_tokens = count_tokens(full_prompt)

    grade = grade_answer(answer, expected_facts)
    total_tokens = message["a_tokens"] + b_tokens
    cost_per_1m = COST_PER_1M.get(model, _DEFAULT_COST)
    cost_usd = round(total_tokens / 1_000_000 * cost_per_1m, 6)

    return {
        "answer": answer,
        "b_tokens": b_tokens,
        "total_tokens": total_tokens,
        "accuracy": grade["accuracy"],
        "data_loss": round(1.0 - grade["accuracy"], 2),
        "grade": grade,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
    }
