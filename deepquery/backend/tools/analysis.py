import pandas as pd
import numpy as np


def aggregate(findings: list[dict]) -> dict:
    if not findings:
        return {"error": "no findings"}
    df = pd.DataFrame(findings)
    df["_num"] = pd.to_numeric(df.get("value", pd.Series(dtype=str)), errors="coerce")
    numeric = df["_num"].dropna()
    result: dict = {
        "total_findings": len(findings),
        "metrics": list(df["metric"].unique()) if "metric" in df.columns else [],
    }
    if not numeric.empty:
        result["value_stats"] = {
            "mean":   round(float(numeric.mean()), 4),
            "median": round(float(numeric.median()), 4),
            "std":    round(float(numeric.std()), 4),
            "min":    round(float(numeric.min()), 4),
            "max":    round(float(numeric.max()), 4),
            "n":      int(len(numeric)),
        }
    return result


def compare(findings: list[dict], group_by: str = "metric") -> dict:
    if not findings:
        return {"error": "no findings"}
    df = pd.DataFrame(findings)
    if group_by not in df.columns:
        return {"error": f"field '{group_by}' not present in findings"}
    df["_num"] = pd.to_numeric(df.get("value", pd.Series(dtype=str)), errors="coerce")
    grouped = (
        df.groupby(group_by)["_num"]
        .agg(avg_value="mean", n_studies="count", std_dev="std")
        .reset_index()
        .dropna(subset=["avg_value"])
    )
    grouped["avg_value"] = grouped["avg_value"].round(4)
    grouped["std_dev"]   = grouped["std_dev"].round(4)
    return {"group_by": group_by, "groups": grouped.to_dict(orient="records")}


def correlate(findings: list[dict], metric_a: str, metric_b: str) -> dict:
    df = pd.DataFrame(findings)
    if "metric" not in df.columns:
        return {"error": "no 'metric' field in findings"}
    a = pd.to_numeric(df[df["metric"] == metric_a]["value"], errors="coerce").dropna()
    b = pd.to_numeric(df[df["metric"] == metric_b]["value"], errors="coerce").dropna()
    n = min(len(a), len(b))
    if n < 3:
        return {"error": f"need ≥3 paired data points, got {n}"}
    r = float(np.corrcoef(a.values[:n], b.values[:n])[0, 1])
    return {"metric_a": metric_a, "metric_b": metric_b, "pearson_r": round(r, 4), "n": n}
