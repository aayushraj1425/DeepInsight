import numpy as np
import pandas as pd

from tools.numbers import number_from_value


def _numeric_series(values: pd.Series) -> pd.Series:
    return values.apply(number_from_value).dropna()


def aggregate(findings: list[dict]) -> dict:
    if not findings:
        return {"error": "no findings"}

    df = pd.DataFrame(findings)
    df["_num"] = _numeric_series(df.get("value", pd.Series(dtype=str)))
    numeric = df["_num"].dropna()

    result: dict = {
        "total_findings": len(findings),
        "metrics": list(df["metric"].unique()) if "metric" in df.columns else [],
        "source_types": list(df["source_type"].dropna().unique()) if "source_type" in df.columns else [],
    }
    if not numeric.empty:
        result["value_stats"] = {
            "mean": round(float(numeric.mean()), 4),
            "median": round(float(numeric.median()), 4),
            "std": round(float(numeric.std()), 4),
            "min": round(float(numeric.min()), 4),
            "max": round(float(numeric.max()), 4),
            "n": int(len(numeric)),
        }
    return result


def compare(findings: list[dict], group_by: str = "metric") -> dict:
    if not findings:
        return {"error": "no findings"}

    df = pd.DataFrame(findings)
    if group_by not in df.columns:
        return {"error": f"field '{group_by}' not present in findings"}

    df["_num"] = _numeric_series(df.get("value", pd.Series(dtype=str)))
    grouped = (
        df.groupby(group_by)["_num"]
        .agg(avg_value="mean", n_studies="count", std_dev="std")
        .reset_index()
        .dropna(subset=["avg_value"])
    )
    grouped["avg_value"] = grouped["avg_value"].round(4)
    grouped["std_dev"] = grouped["std_dev"].round(4)
    return {"group_by": group_by, "groups": grouped.to_dict(orient="records")}


def correlate(findings: list[dict], metric_a: str, metric_b: str) -> dict:
    df = pd.DataFrame(findings)
    if "metric" not in df.columns:
        return {"error": "no 'metric' field in findings"}

    a = _numeric_series(df[df["metric"] == metric_a]["value"])
    b = _numeric_series(df[df["metric"] == metric_b]["value"])
    n = min(len(a), len(b))
    if n < 3:
        return {"error": f"need >=3 paired data points, got {n}"}

    r = float(np.corrcoef(a.values[:n], b.values[:n])[0, 1])
    return {"metric_a": metric_a, "metric_b": metric_b, "pearson_r": round(r, 4), "n": n}


def trend_analysis(findings: list[dict]) -> dict:
    if not findings:
        return {"error": "no findings"}

    df = pd.DataFrame(findings)
    if "year" not in df.columns:
        return {"error": "no year field in findings"}

    df["_year"] = pd.to_numeric(df["year"], errors="coerce")
    df["_num"] = _numeric_series(df.get("value", pd.Series(dtype=str)))
    df = df.dropna(subset=["_year", "_num"])
    if df.empty:
        return {"error": "no numeric dated findings"}

    group_key = "series_id" if "series_id" in df.columns else "metric"
    trends = []
    for key, group in df.groupby(group_key):
        group = group.sort_values("_year")
        if len(group) < 2:
            continue
        first = group.iloc[0]
        latest = group.iloc[-1]
        start_value = float(first["_num"])
        latest_value = float(latest["_num"])
        absolute_change = latest_value - start_value
        pct_change = None
        if start_value:
            pct_change = 100 * absolute_change / abs(start_value)
        trends.append({
            "series_id": str(key),
            "metric": str(latest.get("metric") or key),
            "source_title": str(latest.get("source_title") or latest.get("paper_title") or ""),
            "provider": str(latest.get("provider") or ""),
            "start_year": int(first["_year"]),
            "latest_year": int(latest["_year"]),
            "start_value": round(start_value, 4),
            "latest_value": round(latest_value, 4),
            "absolute_change": round(absolute_change, 4),
            "pct_change": round(pct_change, 2) if pct_change is not None and np.isfinite(pct_change) else None,
            "points": int(len(group)),
            "unit_hint": latest.get("unit_hint"),
        })

    trends.sort(key=lambda row: (row["points"], row["latest_year"]), reverse=True)
    return {"group_by": group_key, "trends": trends[:20], "series_count": len(trends)}


def triangulate_sources(findings: list[dict]) -> dict:
    if not findings:
        return {"error": "no findings"}

    df = pd.DataFrame(findings)
    source_type_counts = (
        df.get("source_type", pd.Series(dtype=str)).fillna("unknown").value_counts().to_dict()
        if "source_type" in df.columns
        else {}
    )
    source_title_counts = (
        df.get("source_title", pd.Series(dtype=str)).fillna("unknown").value_counts().head(12).to_dict()
        if "source_title" in df.columns
        else {}
    )
    metrics_by_source = {}
    if "source_type" in df.columns and "metric" in df.columns:
        for source_type, group in df.groupby("source_type"):
            metrics_by_source[str(source_type)] = sorted({str(metric) for metric in group["metric"].dropna()})[:12]

    return {
        "source_type_counts": source_type_counts,
        "top_source_titles": source_title_counts,
        "metrics_by_source_type": metrics_by_source,
        "triangulation_note": (
            "A claim is stronger when supported across primary datasets, scholarly papers, and independent reports; "
            "single-source claims should remain caveated."
        ),
    }
