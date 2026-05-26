"""Fetcher — pulls a live Wikipedia article and returns a doc dict."""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_harness.phase2.fetch_wikipedia import fetch_wikipedia_html
from phase4.agent_b import count_tokens

MAX_BODY_TOKENS = 2000

_cache: dict[str, dict] = {}


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate(text: str, max_tokens: int) -> str:
    if count_tokens(text) <= max_tokens:
        return text
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)[:max_tokens]
    return enc.decode(tokens)


def fetch_as_doc(article_title: str) -> dict:
    if article_title in _cache:
        return _cache[article_title]

    html, title = fetch_wikipedia_html(article_title)
    plain = _strip_html(html)
    body = _truncate(plain, MAX_BODY_TOKENS)

    doc = {
        "header": {
            "id": f"live-{article_title.lower().replace('_', '-')}",
            "type": "article",
            "title": title,
            "source": f"https://en.wikipedia.org/wiki/{article_title}",
            "confidence": "claimed",
            "domain": article_title.replace("_", " "),
            "tags": article_title.replace("_", " ").lower(),
        },
        "body": body,
    }
    _cache[article_title] = doc
    return doc
