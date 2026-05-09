import json
import re
from typing import Any


DROP_KEYS = {
    "abstract_inverted_index",
    "data",
    "figure",
    "full_text_truncated",
}

TEXT_LIMITS = {
    "abstract": 1800,
    "description": 700,
    "document_brief": 3500,
    "excerpt": 700,
    "reasoning": 900,
    "source_quote": 280,
    "title": 260,
    "url": 360,
}


def clip_text(value: Any, max_chars: int = 1200) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + f"... [truncated {len(text) - max_chars} chars]"


def _limit_for_key(key: str | None) -> int:
    return TEXT_LIMITS.get(key or "", 1200)


def compact_value(value: Any, *, key: str | None = None, max_items: int = 20, depth: int = 0) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, bytes):
        return f"<{len(value)} bytes omitted>"
    if isinstance(value, str):
        return clip_text(value, _limit_for_key(key))
    if depth >= 5:
        return clip_text(value, 600)

    if isinstance(value, dict):
        compacted: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            child_key = str(raw_key)
            if child_key in DROP_KEYS:
                continue
            if child_key == "resources":
                compacted["resource_count"] = len(raw_value) if isinstance(raw_value, list) else 0
                continue
            compacted[child_key] = compact_value(
                raw_value,
                key=child_key,
                max_items=max_items,
                depth=depth + 1,
            )
        return compacted

    if isinstance(value, (list, tuple, set)):
        items = list(value)
        compacted_items = [
            compact_value(item, key=key, max_items=max_items, depth=depth + 1)
            for item in items[:max_items]
        ]
        if len(items) > max_items:
            compacted_items.append({"omitted_items": len(items) - max_items})
        return compacted_items

    return clip_text(value, _limit_for_key(key))


def compact_json(value: Any, *, max_chars: int = 12000, max_items: int = 20) -> str:
    text = json.dumps(
        compact_value(value, max_items=max_items),
        ensure_ascii=True,
        default=str,
        separators=(",", ": "),
    )
    return clip_text(text, max_chars)


def slim_findings(findings: list[dict], *, limit: int = 10) -> list[dict]:
    keys = [
        "metric",
        "value",
        "sample_size",
        "ci",
        "p_value",
        "intervention",
        "source_quote",
        "unit_hint",
        "paper_title",
        "year",
        "source_type",
        "source_title",
        "source_id",
        "provider",
        "series_id",
    ]
    rows: list[dict] = []
    for finding in findings[:limit]:
        row = {key: finding.get(key) for key in keys if finding.get(key) not in (None, "")}
        rows.append(compact_value(row, max_items=8))
    return rows


def slim_paper_sources(papers: list[dict], *, limit: int = 12, include_abstract: bool = False) -> list[dict]:
    rows: list[dict] = []
    for paper in papers[:limit]:
        row = {
            "source_id": paper.get("source_id"),
            "provider": paper.get("provider"),
            "title": paper.get("title"),
            "year": paper.get("year"),
            "citation_count": paper.get("citation_count"),
            "authors": (paper.get("authors") or [])[:5],
            "url": paper.get("url"),
        }
        if include_abstract:
            row["abstract"] = clip_text(paper.get("abstract", ""), 900)
        rows.append(compact_value(row, max_items=8))
    return rows


def slim_datasets(datasets: list[dict], *, limit: int = 10) -> list[dict]:
    rows: list[dict] = []
    for dataset in datasets[:limit]:
        rows.append(compact_value({
            "source_id": dataset.get("source_id"),
            "provider": dataset.get("provider"),
            "title": dataset.get("title"),
            "description": dataset.get("description"),
            "url": dataset.get("url"),
            "resource_count": len(dataset.get("resources", [])),
            "score": dataset.get("score"),
        }, max_items=8))
    return rows
