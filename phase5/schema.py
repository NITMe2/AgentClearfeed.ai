"""Schema representation, mutation, and crossover operators for Phase 5 GA."""

import copy
import random

DELIMITERS = [":", "=", "|", "\t"]
KEY_STYLES = ["full", "short", "none"]
NESTINGS = ["nested", "flat"]

ALL_FIELDS = [
    "id", "type", "title", "source", "author",
    "published", "confidence", "domain", "tags", "conflicts", "license",
]

ESSENTIAL_FIELDS = {"title", "source"}  # never dropped by mutation op 7

# Fixed abbreviation map — avoids first-3-char collisions between field names
ABBREV = {
    "id": "id", "type": "ty", "title": "ti", "source": "src",
    "author": "au", "published": "pub", "confidence": "cf",
    "domain": "dm", "tags": "tg", "conflicts": "cx", "license": "lic",
}

# ACF seed — encodes what the current hand-designed ACF format does
ACF_SEED = {
    "delimiter": ":",
    "key_style": "full",
    "nesting": "nested",
    "field_order": [
        "id", "type", "title", "source", "author",
        "published", "confidence", "domain", "tags",
    ],
    "quote_values": False,
    "newline_sep": True,
}


def _clone(schema: dict) -> dict:
    s = dict(schema)
    s["field_order"] = list(schema["field_order"])
    return s


def mutate(schema: dict) -> dict:
    """Return a new schema with exactly one mutation applied at random."""
    s = _clone(schema)

    droppable = [f for f in s["field_order"] if f not in ESSENTIAL_FIELDS]
    addable = [f for f in ALL_FIELDS if f not in s["field_order"]]

    # Build applicable op list — some ops require a non-empty candidate set
    ops = [1, 2, 3, 4, 5, 6]
    if droppable:
        ops.append(7)
    if addable:
        ops.append(8)

    op = random.choice(ops)

    if op == 1:
        s["delimiter"] = random.choice([d for d in DELIMITERS if d != s["delimiter"]])
    elif op == 2:
        idx = KEY_STYLES.index(s["key_style"])
        s["key_style"] = KEY_STYLES[(idx + 1) % len(KEY_STYLES)]
    elif op == 3:
        s["nesting"] = "flat" if s["nesting"] == "nested" else "nested"
    elif op == 4:
        random.shuffle(s["field_order"])
    elif op == 5:
        s["quote_values"] = not s["quote_values"]
    elif op == 6:
        s["newline_sep"] = not s["newline_sep"]
    elif op == 7:
        s["field_order"].remove(random.choice(droppable))
    elif op == 8:
        s["field_order"].append(random.choice(addable))

    return s


def crossover(schema_a: dict, schema_b: dict) -> tuple[dict, dict]:
    """Return two children by randomly selecting each gene from one parent."""
    def _mix(a: dict, b: dict) -> dict:
        child = {}
        for key in ACF_SEED:
            child[key] = copy.deepcopy(random.choice([a[key], b[key]]))
        return child

    return _mix(schema_a, schema_b), _mix(schema_b, schema_a)
