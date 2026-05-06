"""Parse .acf files into structured dicts."""

from pathlib import Path


def parse_header(text: str) -> dict:
    lines = text.strip().split("\n")
    header = {}
    for line in lines:
        if line.startswith("ACF/"):
            header["version"] = line.strip()
            continue
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            header[key.strip()] = value.strip()
    return header


def parse_acf(text: str) -> dict:
    parts = text.split("---", 1)
    header_text = parts[0]
    body_text = parts[1] if len(parts) > 1 else ""

    header = parse_header(header_text)
    return {
        "header": header,
        "body": body_text.strip(),
        "raw": text,
    }


def load_documents(directory: Path) -> dict[str, dict]:
    docs = {}
    for path in directory.glob("*.acf"):
        text = path.read_text(encoding="utf-8")
        doc = parse_acf(text)
        doc_id = doc["header"].get("id", path.stem)
        docs[doc_id] = doc
    return docs
