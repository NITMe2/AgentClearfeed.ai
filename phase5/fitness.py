"""Fitness function for Phase 5 GA — evaluates a schema against Phase 1 queries."""

from pathlib import Path

from phase4.agent_b import _SYSTEM, _call_ollama, count_tokens, grade_answer
from phase5.formatters.evolved import format_doc
from server.parser import load_documents
from test_harness.queries import QUERIES

_SERVER_DIR = Path(__file__).resolve().parents[1] / "server"

_docs: dict | None = None
_last_eval_metrics: dict = {}


def _get_docs() -> dict:
    global _docs
    if _docs is None:
        _docs = load_documents(_SERVER_DIR / "documents")
    return _docs


def evaluate(schema: dict) -> tuple[float]:
    """Score a schema: 60% accuracy + 40% token efficiency. Returns a DEAP-compatible tuple."""
    global _last_eval_metrics
    docs = _get_docs()

    scores = []
    total_tokens = 0
    total_accuracy = 0.0

    for query in QUERIES:
        doc = docs[query["acf_doc"]]
        formatted = format_doc(doc, schema)
        full_prompt = f"{_SYSTEM}\n\nCONTEXT:\n{formatted}\n\nQUESTION: {query['question']}\n"

        a_tokens = count_tokens(formatted)
        b_tokens = count_tokens(full_prompt)

        answer, _ = _call_ollama(full_prompt, "llama3.1:8b")
        grade = grade_answer(answer, query["expected_facts"])
        accuracy = grade["accuracy"]

        token_efficiency = 1.0 / (a_tokens + b_tokens)
        score = (accuracy * 0.6) + (token_efficiency * 1000 * 0.4)
        scores.append(score)

        total_tokens += a_tokens + b_tokens
        total_accuracy += accuracy

    n = len(QUERIES)
    _last_eval_metrics = {
        "avg_tokens": round(total_tokens / n),
        "avg_accuracy": round(total_accuracy / n, 2),
    }

    return (sum(scores) / n,)


def get_last_metrics() -> dict:
    """Return token and accuracy stats from the most recent evaluate() call."""
    return dict(_last_eval_metrics)
