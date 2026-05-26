"""Champion formatter — renders docs using the Phase 5-GA combined winner schema."""

import json
from pathlib import Path

from phase5.formatters.evolved import format_doc as _render

_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "phase5" / "results" / "ga_combined_results.json")
    .read_text()
)["best_schema"]


def format_doc(doc: dict) -> str:
    return _render(doc, _SCHEMA)
