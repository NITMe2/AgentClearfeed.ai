"""Agent A — fetches a document and formats it for transmission to Agent B."""

from pathlib import Path

import tiktoken

from phase4.formatters import acf, json_fmt, toon_fmt, champion
from server.parser import load_documents

_SERVER_DIR = Path(__file__).resolve().parents[1] / "server"
_ENC = tiktoken.get_encoding("cl100k_base")

FORMATTERS = {
    "acf": acf,
    "json": json_fmt,
    "toon": toon_fmt,
    "champion": champion,
}

_documents: dict | None = None


def _get_documents() -> dict:
    global _documents
    if _documents is None:
        _documents = load_documents(_SERVER_DIR / "documents")
        _documents.update(load_documents(_SERVER_DIR / "documents_phase2"))
    return _documents


def count_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def prepare_message(query: dict, fmt_name: str) -> dict:
    """Return the formatted document + outbound token count for Agent B."""
    docs = _get_documents()
    doc_id = query["acf_doc"]
    if doc_id not in docs:
        raise KeyError(f"Document '{doc_id}' not found in {_DOCS_DIR}")
    doc = docs[doc_id]
    formatter = FORMATTERS[fmt_name]
    content = formatter.format_doc(doc)
    return {
        "content": content,
        "a_tokens": count_tokens(content),
        "format": fmt_name,
    }
