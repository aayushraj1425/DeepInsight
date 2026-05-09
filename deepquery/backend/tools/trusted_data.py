import io
import math
import re
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd


CURRENT_YEAR = datetime.now(timezone.utc).year

TRUSTED_SOURCE_CATALOG = [
    {
        "provider": "BLS",
        "title": "BLS Current Employment Statistics: Computer systems design employment",
        "url": "https://www.bls.gov/ces/",
        "source_class": "government_labor",
        "credibility": 0.96,
        "reason": "Primary U.S. labor-market source for payroll employment by industry.",
    },
    {
        "provider": "BLS",
        "title": "BLS Occupational Outlook Handbook: Software developers",
        "url": "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm",
        "source_class": "government_labor",
        "credibility": 0.95,
        "reason": "Primary occupational outlook source for employment, wages, and projections.",
    },
    {
        "provider": "FRED",
        "title": "Federal funds effective rate",
        "url": "https://fred.stlouisfed.org/series/FEDFUNDS",
        "source_class": "macro_indicator",
        "credibility": 0.95,
        "reason": "Primary macroeconomic indicator useful for separating AI effects from monetary tightening.",
    },
    {
        "provider": "FRED",
        "title": "U.S. unemployment rate",
        "url": "https://fred.stlouisfed.org/series/UNRATE",
        "source_class": "macro_indicator",
        "credibility": 0.95,
        "reason": "Primary labor-market context for broad employment-cycle interpretation.",
    },
    {
        "provider": "World Bank",
        "title": "World Bank Open Data",
        "url": "https://data.worldbank.org/",
        "source_class": "global_macro_indicator",
        "credibility": 0.92,
        "reason": "Primary global development and labor-market indicators.",
    },
    {
        "provider": "OECD",
        "title": "OECD Data Explorer",
        "url": "https://data-explorer.oecd.org/",
        "source_class": "international_labor_indicator",
        "credibility": 0.92,
        "reason": "High-quality international labor, productivity, and policy datasets.",
    },
    {
        "provider": "SEC EDGAR",
        "title": "SEC EDGAR company filings",
        "url": "https://www.sec.gov/edgar/search/",
        "source_class": "company_primary_source",
        "credibility": 0.9,
        "reason": "Primary company filings for risk factors, headcount, spending, and management commentary.",
    },
    {
        "provider": "NBER",
        "title": "NBER working papers",
        "url": "https://www.nber.org/papers",
        "source_class": "economics_research",
        "credibility": 0.86,
        "reason": "Strong source for labor economics, automation, productivity, and causal inference research.",
    },
    {
        "provider": "Stanford HAI",
        "title": "Stanford AI Index Report",
        "url": "https://aiindex.stanford.edu/report/",
        "source_class": "ai_adoption_report",
        "credibility": 0.88,
        "reason": "Widely cited annual AI adoption and investment report.",
    },
    {
        "provider": "McKinsey",
        "title": "McKinsey Global Institute AI and labor reports",
        "url": "https://www.mckinsey.com/mgi/overview",
        "source_class": "consulting_report",
        "credibility": 0.76,
        "reason": "Useful strategy context, but assumptions and commercial incentives require caveats.",
    },
    {
        "provider": "WEF",
        "title": "World Economic Forum Future of Jobs reports",
        "url": "https://www.weforum.org/publications/",
        "source_class": "survey_report",
        "credibility": 0.74,
        "reason": "Useful for employer expectations and task-shift narratives, but survey methodology must be checked.",
    },
    {
        "provider": "LinkedIn",
        "title": "LinkedIn Economic Graph",
        "url": "https://economicgraph.linkedin.com/",
        "source_class": "platform_labor_signal",
        "credibility": 0.73,
        "reason": "Useful hiring and skill-demand signal, but platform coverage is not a full labor census.",
    },
    {
        "provider": "Stack Overflow",
        "title": "Stack Overflow Developer Survey",
        "url": "https://survey.stackoverflow.co/",
        "source_class": "developer_survey",
        "credibility": 0.78,
        "reason": "Large developer survey; useful but self-selected and not a labor-market census.",
    },
    {
        "provider": "GitHub",
        "title": "GitHub Octoverse",
        "url": "https://octoverse.github.com/",
        "source_class": "developer_activity",
        "credibility": 0.78,
        "reason": "Useful signal for developer activity and AI-tool adoption, but platform-specific.",
    },
    {
        "provider": "Layoffs.fyi",
        "title": "Layoffs.fyi tech layoff tracker",
        "url": "https://layoffs.fyi/",
        "source_class": "layoff_tracker",
        "credibility": 0.72,
        "reason": "Timely layoff tracker; useful for directional analysis but not official labor statistics.",
    },
]

TECH_JOB_TERMS = {
    "ai", "artificial", "developer", "developers", "engineer", "engineering", "jobs",
    "programmer", "software", "swe", "tech", "technology",
}

WORLD_BANK_INDICATORS = [
    ("SL.TLF.TOTL.IN", "World Bank labor force, total"),
    ("NY.GDP.MKTP.KD.ZG", "World Bank GDP growth"),
]

BLS_SERIES = [
    ("CES6054150001", "BLS employment: Computer systems design and related services", "thousands of payroll jobs"),
    ("CES6051100001", "BLS employment: Software publishers", "thousands of payroll jobs"),
]

FRED_SERIES = [
    ("FEDFUNDS", "FRED federal funds effective rate", "percent"),
    ("UNRATE", "FRED U.S. unemployment rate", "percent"),
]


def _clean(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z0-9-]{2,}", text.lower()))


def _query_is_tech_labor(query: str, plan: dict | None = None) -> bool:
    haystack = query
    if plan:
        haystack += " " + " ".join(plan.get("dataset_targets", []) or [])
        haystack += " " + " ".join(plan.get("source_priorities", []) or [])
    tokens = _tokens(haystack)
    return bool(tokens & TECH_JOB_TERMS) and bool(tokens & {"job", "jobs", "labor", "employment", "hiring", "layoff", "layoffs", "workforce", "developer", "developers", "engineer", "engineering", "software", "swe"})


def trusted_source_candidates(query: str, plan: dict | None = None) -> list[dict]:
    if _query_is_tech_labor(query, plan):
        return [dict(source) for source in TRUSTED_SOURCE_CATALOG]

    generic = [
        source for source in TRUSTED_SOURCE_CATALOG
        if source["provider"] in {"FRED", "BLS", "World Bank", "Stanford HAI"}
    ]
    return [dict(source) for source in generic[:4]]


def _series_stats(points: list[dict]) -> dict:
    if len(points) < 2:
        return {}
    first = points[0]
    latest = points[-1]
    start_value = float(first["value"])
    latest_value = float(latest["value"])
    absolute_change = latest_value - start_value
    pct_change = None
    if start_value:
        pct_change = 100 * absolute_change / abs(start_value)
    years = max(1, int(latest["year"]) - int(first["year"]))
    annualized = None
    if start_value > 0 and latest_value > 0 and years:
        annualized = 100 * ((latest_value / start_value) ** (1 / years) - 1)
    return {
        "start_year": int(first["year"]),
        "latest_year": int(latest["year"]),
        "start_value": round(start_value, 4),
        "latest_value": round(latest_value, 4),
        "absolute_change": round(absolute_change, 4),
        "pct_change": round(pct_change, 2) if pct_change is not None and math.isfinite(pct_change) else None,
        "annualized_change_pct": round(annualized, 2) if annualized is not None and math.isfinite(annualized) else None,
        "points": len(points),
    }


def _series_findings(source_id: str, title: str, provider: str, unit: str, points: list[dict]) -> list[dict]:
    rows: list[dict] = []
    stats = _series_stats(points)
    for point in points[-12:]:
        rows.append({
            "metric": title,
            "value": str(point["value"]),
            "sample_size": None,
            "ci": None,
            "p_value": None,
            "intervention": "trusted public time series",
            "source_quote": (
                f"{provider} reported {point['value']} {unit} for {point['date']}. "
                f"Series trend: {stats.get('start_year', 'n/a')} to {stats.get('latest_year', 'n/a')}."
            ),
            "unit_hint": unit,
            "paper_title": title,
            "year": int(point["year"]),
            "source_type": "dataset",
            "source_title": title,
            "source_id": source_id,
            "series_id": source_id,
            "provider": provider,
        })
    return rows


async def fetch_bls_series(series_id: str, title: str, unit: str, start_year: int | None = None) -> tuple[dict | None, list[dict]]:
    start = start_year or max(2014, CURRENT_YEAR - 12)
    end = CURRENT_YEAR
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    payload = {"seriesid": [series_id], "startyear": str(start), "endyear": str(end)}
    async with httpx.AsyncClient(timeout=25.0) as http:
        response = await http.post(url, json=payload)
        response.raise_for_status()
    data = response.json()
    series = (data.get("Results") or {}).get("series") or []
    if not series:
        return None, []

    points = []
    for item in series[0].get("data", []):
        period = item.get("period", "")
        if not period.startswith("M") or period == "M13":
            continue
        try:
            value = float(str(item.get("value", "")).replace(",", ""))
            year = int(item.get("year"))
            month = int(period[1:])
        except ValueError:
            continue
        points.append({"date": f"{year}-{month:02d}-01", "year": year, "value": value})

    points.sort(key=lambda row: row["date"])
    if not points:
        return None, []

    source_id = f"trusted:bls:{series_id}"
    profile = {
        "dataset_id": source_id,
        "provider": "BLS",
        "title": title,
        "url": "https://www.bls.gov/ces/",
        "source_class": "government_labor",
        "credibility": 0.96,
        "unit": unit,
        "series_id": series_id,
        "rows": len(points),
        "year_column": "year",
        "numeric_columns": ["value"],
        "summary": {"value": _series_stats(points)},
        "points": points[-36:],
    }
    return profile, _series_findings(source_id, title, "BLS", unit, points)


async def fetch_fred_series(series_id: str, title: str, unit: str, start_year: int | None = None) -> tuple[dict | None, list[dict]]:
    start = start_year or max(2014, CURRENT_YEAR - 12)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as http:
        response = await http.get(url)
        response.raise_for_status()

    df = pd.read_csv(io.BytesIO(response.content))
    if "observation_date" not in df.columns or series_id not in df.columns:
        return None, []
    df["year"] = pd.to_datetime(df["observation_date"], errors="coerce").dt.year
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df[(df["year"] >= start) & df[series_id].notna()].copy()
    if df.empty:
        return None, []

    annual = (
        df.groupby("year", as_index=False)[series_id]
        .mean()
        .sort_values("year")
    )
    points = [
        {"date": f"{int(row.year)}-12-31", "year": int(row.year), "value": round(float(getattr(row, series_id)), 4)}
        for row in annual.itertuples(index=False)
    ]
    source_id = f"trusted:fred:{series_id}"
    profile = {
        "dataset_id": source_id,
        "provider": "FRED",
        "title": title,
        "url": f"https://fred.stlouisfed.org/series/{series_id}",
        "source_class": "macro_indicator",
        "credibility": 0.95,
        "unit": unit,
        "series_id": series_id,
        "rows": len(points),
        "year_column": "year",
        "numeric_columns": ["value"],
        "summary": {"value": _series_stats(points)},
        "points": points[-36:],
    }
    return profile, _series_findings(source_id, title, "FRED", unit, points)


async def fetch_world_bank_indicator(indicator: str, title: str) -> tuple[dict | None, list[dict]]:
    url = f"https://api.worldbank.org/v2/country/USA/indicator/{indicator}"
    params = {"format": "json", "per_page": 80}
    async with httpx.AsyncClient(timeout=25.0) as http:
        response = await http.get(url, params=params)
        response.raise_for_status()
    payload = response.json()
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    points = []
    for item in rows:
        if item.get("value") is None:
            continue
        try:
            year = int(item.get("date"))
            value = float(item.get("value"))
        except (TypeError, ValueError):
            continue
        if year >= max(2014, CURRENT_YEAR - 12):
            points.append({"date": f"{year}-12-31", "year": year, "value": round(value, 4)})
    points.sort(key=lambda row: row["year"])
    if not points:
        return None, []

    source_id = f"trusted:worldbank:{indicator}"
    profile = {
        "dataset_id": source_id,
        "provider": "World Bank",
        "title": title,
        "url": f"https://data.worldbank.org/indicator/{indicator}",
        "source_class": "macro_indicator",
        "credibility": 0.92,
        "unit": "indicator value",
        "series_id": indicator,
        "rows": len(points),
        "year_column": "year",
        "numeric_columns": ["value"],
        "summary": {"value": _series_stats(points)},
        "points": points[-36:],
    }
    return profile, _series_findings(source_id, title, "World Bank", "indicator value", points)


async def load_trusted_time_series(query: str, plan: dict | None = None) -> tuple[list[dict], list[dict], list[dict]]:
    candidates = trusted_source_candidates(query, plan)
    profiles: list[dict] = []
    findings: list[dict] = []

    if _query_is_tech_labor(query, plan):
        for series_id, title, unit in BLS_SERIES:
            try:
                profile, rows = await fetch_bls_series(series_id, title, unit)
                if profile:
                    profiles.append(profile)
                    findings.extend(rows)
            except Exception:
                continue

    for series_id, title, unit in FRED_SERIES:
        try:
            profile, rows = await fetch_fred_series(series_id, title, unit)
            if profile:
                profiles.append(profile)
                findings.extend(rows)
        except Exception:
            continue

    if not profiles:
        for indicator, title in WORLD_BANK_INDICATORS:
            try:
                profile, rows = await fetch_world_bank_indicator(indicator, title)
                if profile:
                    profiles.append(profile)
                    findings.extend(rows)
            except Exception:
                continue

    return candidates, profiles, findings
