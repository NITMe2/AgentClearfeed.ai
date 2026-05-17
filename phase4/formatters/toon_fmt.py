"""TOON formatter — implements Token-Oriented Object Notation.

toon-format 0.1.0 ships with encode() as a stub (NotImplementedError), so this
module implements the encoder directly from the published TOON spec:
  https://github.com/toon-format/toon

Rules:
  - Objects   → key: value  (one per line, no braces)
  - Nested    → key:\n  child: val  (indented 2 spaces)
  - Tabular   → key[N]{f1,f2}:\n  v1,v2  (uniform list-of-dicts)
  - Arrays    → key[N]: v1,v2,v3  (primitives)
  - Strings   → unquoted unless they contain the delimiter or are empty
  - Multi-line strings → indented block under key:
"""

_DELIMITER = ","


def format_doc(doc: dict) -> str:
    payload = {"header": doc["header"], "body": doc["body"]}
    return _encode_dict(payload, depth=0)


def _encode_dict(d: dict, depth: int) -> str:
    pad = "  " * depth
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"{pad}{k}:")
            lines.append(_encode_dict(v, depth + 1))
        elif isinstance(v, list):
            lines.append(_encode_list(k, v, depth))
        elif isinstance(v, str) and "\n" in v:
            lines.append(f"{pad}{k}:")
            for sub in v.split("\n"):
                lines.append(f"{pad}  {sub}" if sub else "")
        else:
            lines.append(f"{pad}{k}: {_prim(v)}")
    return "\n".join(lines)


def _encode_list(key: str, lst: list, depth: int) -> str:
    pad = "  " * depth
    n = len(lst)
    if not lst:
        return f"{pad}{key}[0]:"
    if all(isinstance(item, dict) for item in lst):
        key_sets = [frozenset(item.keys()) for item in lst]
        if len(set(key_sets)) == 1:
            fields = list(lst[0].keys())
            header = f"{pad}{key}[{n}]{{{_DELIMITER.join(fields)}}}:"
            rows = [f"{pad}  {_DELIMITER.join(_prim(item[f]) for f in fields)}" for item in lst]
            return header + "\n" + "\n".join(rows)
    items_str = _DELIMITER.join(_prim(item) for item in lst)
    return f"{pad}{key}[{n}]: {items_str}"


def _prim(val) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    if _DELIMITER in s or not s.strip():
        return f'"{s}"'
    return s
