"""ACF formatter — returns the raw .acf text unchanged."""


def format_doc(doc: dict) -> str:
    return doc["raw"]
