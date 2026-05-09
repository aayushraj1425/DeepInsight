import io
import re
from typing import Any
from urllib.parse import quote_plus

import httpx
import pandas as pd

MAX_RESOURCE_BYTES = 2_500_000
DATASET_LIMIT = 10
TABLE_LIMIT = 3
MAX_DESCRIPTION_CHARS = 900
MAX_RESOURCES_PER_DATASET = 20


def _clean(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _clip(text: Any, limit: int = MAX_DESCRIPTION_CHARS) -> str:
    value = _clean(text)
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def _source_id(provider: str, raw_id: str, title: str) -> str:
    key = raw_id or quote_plus(title.lower())
    return f"dataset:{provider.lower()}:{key}"


def _dataset_score(dataset: dict, query: str) -> int:
    tokens = {token for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", query.lower())}
    haystack = f"{dataset.get('title', '')} {dataset.get('description', '')}".lower()
    return sum(1 for token in tokens if token in haystack)


async def search_datagov(query: str, limit: int = 5) -> list[dict]:
    params = {"q": query, "rows": limit}
    async with httpx.AsyncClient(timeout=25.0) as http:
        response = await http.get("https://catalog.data.gov/api/3/action/package_search", params=params)
        response.raise_for_status()

    datasets = []
    for item in response.json().get("result", {}).get("results", []):
        resources = []
        for resource in item.get("resources", [])[:MAX_RESOURCES_PER_DATASET]:
            url = resource.get("url") or ""
            fmt = (resource.get("format") or "").lower()
            if not url:
                continue
            resources.append({
                "name": resource.get("name") or "Resource",
                "url": url,
                "format": fmt or url.rsplit(".", 1)[-1].lower(),
            })

        title = _clean(item.get("title") or item.get("name"))
        datasets.append({
            "source_id": _source_id("Data.gov", item.get("id", ""), title),
            "provider": "Data.gov",
            "title": title,
            "description": _clip(item.get("notes")),
            "url": item.get("url") or f"https://catalog.data.gov/dataset/{item.get('name', '')}",
            "resources": resources,
            "score": 0,
        })
    return datasets


async def search_datacite(query: str, limit: int = 5) -> list[dict]:
    params = {"query": query, "resource-type-id": "dataset", "page[size]": limit}
    async with httpx.AsyncClient(timeout=25.0) as http:
        response = await http.get("https://api.datacite.org/dois", params=params)
        response.raise_for_status()

    datasets = []
    for item in response.json().get("data", []):
        attrs = item.get("attributes") or {}
        title = _clean((attrs.get("titles") or [{}])[0].get("title"))
        descriptions = attrs.get("descriptions") or []
        description = _clip(descriptions[0].get("description") if descriptions else "")
        datasets.append({
            "source_id": _source_id("DataCite", item.get("id", ""), title),
            "provider": "DataCite",
            "title": title,
            "description": description,
            "url": attrs.get("url") or f"https://doi.org/{item.get('id', '')}",
            "resources": [],
            "score": 0,
        })
    return datasets


async def discover_datasets(query: str, subqueries: list[str]) -> list[dict]:
    search_terms = [query, *subqueries[:2]]
    seen: set[str] = set()
    datasets: list[dict] = []

    for term in search_terms:
        results: list[dict] = []
        for search in (search_datagov, search_datacite):
            try:
                results.extend(await search(term, limit=4))
            except Exception:
                continue

        for dataset in results:
            key = dataset["source_id"]
            if key in seen:
                continue
            seen.add(key)
            dataset["score"] = _dataset_score(dataset, query)
            datasets.append(dataset)

    datasets.sort(key=lambda item: (item.get("score", 0), len(item.get("resources", []))), reverse=True)
    return datasets[:DATASET_LIMIT]


def _resource_kind(resource: dict) -> str:
    fmt = (resource.get("format") or "").lower()
    url = (resource.get("url") or "").lower()
    if "csv" in fmt or url.endswith(".csv"):
        return "csv"
    if "json" in fmt or url.endswith(".json"):
        return "json"
    return ""


async def _fetch_resource(resource: dict) -> bytes | None:
    url = resource.get("url") or ""
    if not url.startswith(("http://", "https://")):
        return None

    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as http:
        response = await http.get(url)
        response.raise_for_status()
        content = response.content[: MAX_RESOURCE_BYTES + 1]
        if len(content) > MAX_RESOURCE_BYTES:
            return None
        return content


def _read_table(resource: dict, content: bytes) -> pd.DataFrame | None:
    kind = _resource_kind(resource)
    if kind == "csv":
        return pd.read_csv(io.BytesIO(content), nrows=5000)
    if kind == "json":
        payload = pd.read_json(io.BytesIO(content))
        return payload.head(5000)
    return None


def _safe_numeric_columns(df: pd.DataFrame) -> list[str]:
    numeric_columns = []
    for column in df.columns:
        series = pd.to_numeric(df[column], errors="coerce")
        if series.notna().sum() >= max(3, min(20, len(df) // 5)):
            numeric_columns.append(str(column))
    return numeric_columns[:8]


def _year_column(df: pd.DataFrame) -> str | None:
    for column in df.columns:
        name = str(column).lower()
        if "year" in name or name in {"date", "time", "period"}:
            return str(column)
    return None


def profile_table(dataset: dict, resource: dict, df: pd.DataFrame) -> dict:
    numeric_columns = _safe_numeric_columns(df)
    year_column = _year_column(df)
    rows = int(len(df))
    profile = {
        "dataset_id": dataset["source_id"],
        "resource_name": resource.get("name") or dataset["title"],
        "provider": dataset["provider"],
        "title": dataset["title"],
        "url": resource.get("url") or dataset.get("url"),
        "rows": rows,
        "columns": [str(column) for column in df.columns[:30]],
        "numeric_columns": numeric_columns,
        "year_column": year_column,
        "summary": {},
    }

    for column in numeric_columns[:6]:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        profile["summary"][column] = {
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "n": int(series.count()),
        }

    return profile


async def load_dataset_tables(datasets: list[dict]) -> tuple[list[dict], list[dict]]:
    table_profiles: list[dict] = []
    findings: list[dict] = []

    for dataset in datasets:
        if len(table_profiles) >= TABLE_LIMIT:
            break
        resources = [resource for resource in dataset.get("resources", []) if _resource_kind(resource)]
        for resource in resources[:3]:
            if len(table_profiles) >= TABLE_LIMIT:
                break
            try:
                content = await _fetch_resource(resource)
                if not content:
                    continue
                df = _read_table(resource, content)
                if df is None or df.empty:
                    continue
            except Exception:
                continue

            profile = profile_table(dataset, resource, df)
            if not profile["numeric_columns"]:
                continue
            table_profiles.append(profile)

            for column, stats in list(profile["summary"].items())[:4]:
                findings.append({
                    "metric": str(column),
                    "value": str(stats["mean"]),
                    "sample_size": stats["n"],
                    "ci": None,
                    "p_value": None,
                    "intervention": "public dataset summary",
                    "source_quote": f"Computed mean from {stats['n']} rows in {profile['resource_name']}.",
                    "unit_hint": "dataset mean",
                    "paper_title": dataset["title"],
                    "year": None,
                    "source_type": "dataset",
                    "source_title": dataset["title"],
                    "source_id": dataset["source_id"],
                })

    return table_profiles, findings
