"""JSON formatter — serialises the parsed document dict as indented JSON."""

import json


def format_doc(doc: dict) -> str:
    payload = {"header": doc["header"], "body": doc["body"]}
    return json.dumps(payload, indent=2)
