"""Evolved formatter — renders a document dict according to a candidate schema."""

from phase5.schema import ABBREV


def _process_body(body: str, nesting: str) -> str:
    if nesting == "nested":
        return body
    # flat: strip lines that are all-uppercase alphabetic words (section headers like DEFINITION, NOTES)
    lines = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped and stripped.isalpha() and stripped.isupper():
            continue
        lines.append(line)
    return "\n".join(lines)


def format_doc(doc: dict, schema: dict) -> str:
    """Render doc according to schema rules. Returns a string ready to send to Agent B."""
    header = doc["header"]
    delimiter = schema["delimiter"]
    key_style = schema["key_style"]
    quote_values = schema["quote_values"]
    newline_sep = schema["newline_sep"]

    lines = []
    for field in schema["field_order"]:
        if field not in header:
            continue
        value = str(header[field])
        if quote_values:
            value = f'"{value}"'

        if key_style == "none":
            lines.append(value)
        elif key_style == "short":
            key = ABBREV.get(field, field[:3])
            lines.append(f"{key}{delimiter}{value}")
        else:  # "full"
            lines.append(f"{field}{delimiter}{value}")

    sep = "\n" if newline_sep else " "
    header_block = sep.join(lines)

    body = _process_body(doc["body"], schema["nesting"])
    return f"{header_block}\n---\n{body}"
