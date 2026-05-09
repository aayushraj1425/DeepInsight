import math
import re
from typing import Any


NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


def number_from_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None

    match = NUMBER_RE.search(str(value).replace(",", ""))
    if not match:
        return None

    try:
        numeric = float(match.group(0))
    except ValueError:
        return None
    return numeric if math.isfinite(numeric) else None


def extract_numeric_snippets(text: str, limit: int = 12) -> list[str]:
    snippets: list[str] = []
    seen: set[str] = set()

    for chunk in re.split(r"(?<=[.!?])\s+|\n+", text):
        candidate = " ".join(chunk.split())
        if not candidate or not NUMBER_RE.search(candidate):
            continue
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(candidate[:240])
        if len(snippets) >= limit:
            break

    return snippets
