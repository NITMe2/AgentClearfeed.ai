"""Formatter — renders a doc dict as evolved-ACF, ACF, or JSON."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from phase5.formatters.evolved import format_doc
from phase5.schema import ACF_SEED

_GA_RESULTS = os.path.join(os.path.dirname(__file__), "..", "phase5", "results", "ga_results.json")

try:
    with open(_GA_RESULTS) as f:
        _EVOLVED_SCHEMA = json.load(f)["best_schema"]
except (FileNotFoundError, KeyError):
    _EVOLVED_SCHEMA = ACF_SEED


def format_evolved(doc: dict) -> str:
    return format_doc(doc, _EVOLVED_SCHEMA)


def format_acf(doc: dict) -> str:
    return format_doc(doc, ACF_SEED)


def format_json(doc: dict) -> str:
    return json.dumps(
        {
            "title": doc["header"]["title"],
            "source": doc["header"]["source"],
            "content": doc["body"],
        },
        indent=2,
    )


FORMATTERS = {
    "evolved": format_evolved,
    "acf": format_acf,
    "json": format_json,
}
