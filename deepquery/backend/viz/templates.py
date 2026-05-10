import json
import math
import re
from typing import Any

import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder


NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


def _figure_dict(fig: go.Figure) -> dict:
    payload = json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))
    payload.get("layout", {}).pop("template", None)
    return payload


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None

    match = NUMBER_RE.search(str(value).replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _ci_bounds(ci: Any, value: float) -> tuple[float, float] | None:
    if not ci:
        return None

    nums = [float(x) for x in NUMBER_RE.findall(str(ci).replace(",", ""))]
    if len(nums) < 2:
        return None

    lower, upper = nums[-2], nums[-1]
    if lower > upper:
        lower, upper = upper, lower
    if lower <= value <= upper:
        return lower, upper
    return None


def _base_layout(title: str) -> dict:
    return {
        "title": {"text": title, "x": 0.02, "font": {"size": 16, "color": "#1A1A1A", "family": "Young Serif, Georgia, serif"}},
        "font": {"color": "#666666", "family": "Inter, ui-sans-serif, system-ui"},
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#F5F5F5",
        "margin": {"l": 72, "r": 28, "t": 58, "b": 56},
        "hoverlabel": {"bgcolor": "#1A1A1A", "font": {"color": "#FFFFFF"}},
    }


def _short(text: Any, limit: int = 68) -> str:
    if not text:
        return "Untitled"
    value = str(text).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def _numeric_findings(findings: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for finding in findings:
        value = _number(finding.get("value"))
        if value is None:
            continue
        row = dict(finding)
        row["_numeric_value"] = value
        rows.append(row)
    return rows


def _sample_size(row: dict) -> int | None:
    value = _number(row.get("sample_size"))
    if value is None or value <= 0:
        return None
    return int(value)


def _p_value(row: dict) -> float | None:
    value = _number(row.get("p_value"))
    if value is None or value < 0:
        return None
    return value


def _significant(row: dict) -> bool | None:
    p_value = _p_value(row)
    if p_value is None:
        return None
    return p_value < 0.05


def _provider(row: dict) -> str:
    source = row.get("source") or ""
    return {
        "pubmed": "PubMed",
        "arxiv": "arXiv",
        "openalex": "OpenAlex",
        "web": "Web",
        "upload": "Uploaded file",
        "cached_demo": "Cached demo",
        "semantic_scholar": "Semantic Scholar",
    }.get(str(source), "Semantic Scholar")


def _evidence_item(row: dict, group_label: str = "", index: int = 0) -> dict:
    return {
        "id": f"{row.get('paper_id') or row.get('paper_title') or 'source'}:{index}:{row.get('metric') or ''}",
        "metric": row.get("metric") or "",
        "value": row.get("value") or "",
        "sampleSize": _sample_size(row),
        "ci": row.get("ci"),
        "pValue": _p_value(row),
        "significant": _significant(row),
        "intervention": row.get("intervention") or "",
        "sourceQuote": row.get("source_quote") or "",
        "paperTitle": row.get("paper_title") or "Untitled source",
        "paperId": row.get("paper_id") or "",
        "year": row.get("year"),
        "url": row.get("url") or "",
        "provider": _provider(row),
        "groupLabel": group_label,
    }


def _datum_meta(label: str, value: float, rows: list[dict]) -> dict:
    p_values = [p for p in (_p_value(row) for row in rows) if p is not None]
    sample_sizes = [n for n in (_sample_size(row) for row in rows) if n is not None]
    significant_count = sum(1 for row in rows if _significant(row) is True)
    significant: bool | None = None
    if p_values:
        significant = significant_count >= max(1, math.ceil(len(p_values) / 2))

    return {
        "label": label,
        "value": value,
        "sampleSize": sum(sample_sizes) if sample_sizes else None,
        "pValue": min(p_values) if p_values else None,
        "significant": significant,
        "significantCount": significant_count,
        "evidenceCount": len(rows),
        "evidence": [_evidence_item(row, label, idx) for idx, row in enumerate(rows[:8])],
    }


def forest_plot(findings: list[dict]) -> tuple[dict, str]:
    rows = _numeric_findings(findings)[:16]
    if not rows:
        raise ValueError("forest_plot requires at least one numeric finding")

    labels = [
        _short(row.get("paper_title") or row.get("metric") or f"Finding {idx + 1}", 58)
        for idx, row in enumerate(rows)
    ]
    values = [row["_numeric_value"] for row in rows]
    metadata = [_datum_meta(label, value, [row]) for label, value, row in zip(labels, values, rows)]
    marker_sizes = [
        max(8, min(22, math.sqrt(meta["sampleSize"]) if meta.get("sampleSize") else 10))
        for meta in metadata
    ]
    hover = [
        (
            f"<b>{_short(row.get('metric'), 90)}</b><br>"
            f"Value: {row.get('value')}<br>"
            f"n: {_sample_size(row) or 'not stated'}<br>"
            f"p: {_p_value(row) if _p_value(row) is not None else 'not stated'}<br>"
            f"Intervention: {_short(row.get('intervention') or 'not specified', 90)}<br>"
            f"Year: {row.get('year') or 'unknown'}<extra></extra>"
        )
        for row in rows
    ]

    error_plus: list[float] = []
    error_minus: list[float] = []
    has_error = False
    for row, value in zip(rows, values):
        bounds = _ci_bounds(row.get("ci"), value)
        if bounds:
            lower, upper = bounds
            error_plus.append(round(upper - value, 4))
            error_minus.append(round(value - lower, 4))
            has_error = True
        else:
            error_plus.append(0)
            error_minus.append(0)

    trace: dict[str, Any] = {
        "x": values,
        "y": labels,
        "mode": "markers",
        "marker": {"size": marker_sizes, "color": "#E25A3D", "line": {"color": "#FFEDD5", "width": 1}},
        "hovertemplate": hover,
        "customdata": metadata,
        "orientation": "h",
    }
    if has_error:
        trace["error_x"] = {
            "type": "data",
            "array": error_plus,
            "arrayminus": error_minus,
            "visible": True,
            "color": "#FCA89A",
            "thickness": 1.5,
        }

    fig = go.Figure(data=[go.Scatter(**trace)])
    fig.update_layout(
        **_base_layout("Effect estimates across extracted findings"),
        xaxis={"title": "Extracted numeric value", "gridcolor": "#E5E7EB", "zerolinecolor": "#9CA3AF"},
        yaxis={"autorange": "reversed", "gridcolor": "#F5F5F5"},
        height=max(360, 92 + len(rows) * 34),
    )

    insight = (
        f"{len(rows)} numeric findings plotted; extracted values range "
        f"from {min(values):.2f} to {max(values):.2f}."
    )
    return _figure_dict(fig), insight


def bar_comparison(compare_result: dict, findings: list[dict] | None = None) -> tuple[dict, str]:
    groups = compare_result.get("groups") or []
    if not groups:
        raise ValueError("bar_comparison requires compare_result['groups']")

    group_by = compare_result.get("group_by") or "group"
    raw_labels = [row.get(group_by) or row.get("metric") or row.get("intervention") for row in groups]
    labels = [_short(label, 40) for label in raw_labels]
    values = [_number(row.get("avg_value")) or 0 for row in groups]
    errors = [_number(row.get("std_dev")) or 0 for row in groups]
    counts = [row.get("n_studies", 0) for row in groups]
    source_rows = findings or []
    metadata: list[dict] = []
    for label, value, count in zip(raw_labels, values, counts):
        matched = [row for row in source_rows if str(row.get(group_by) or "") == str(label or "")]
        meta = _datum_meta(_short(label, 40), value, matched)
        if not matched:
            meta["evidenceCount"] = int(count or 0)
        metadata.append(meta)

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker={"color": "#E25A3D", "line": {"color": "#FFEDD5", "width": 1}},
            error_y={"type": "data", "array": errors, "visible": any(e > 0 for e in errors), "color": "#9CA3AF"},
            customdata=metadata,
            hovertemplate="<b>%{x}</b><br>Average: %{y:.3f}<br>Evidence items: %{customdata.evidenceCount}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout(f"Average extracted value by {group_by}"),
        xaxis={"title": str(group_by).replace("_", " "), "gridcolor": "#F5F5F5"},
        yaxis={"title": "Average numeric value", "gridcolor": "#E5E7EB", "zerolinecolor": "#9CA3AF"},
        height=360,
    )

    top_idx = max(range(len(values)), key=lambda idx: values[idx])
    insight = f"{labels[top_idx]} has the highest average extracted value ({values[top_idx]:.2f})."
    return _figure_dict(fig), insight


def timeline(findings: list[dict]) -> tuple[dict, str]:
    rows = [
        row for row in _numeric_findings(findings)
        if isinstance(row.get("year"), int) or str(row.get("year") or "").isdigit()
    ]
    if len(rows) < 2:
        raise ValueError("timeline requires at least two numeric findings with years")

    rows = sorted(rows, key=lambda row: int(row["year"]))
    years = [int(row["year"]) for row in rows]
    values = [row["_numeric_value"] for row in rows]
    metrics = [_short(row.get("metric"), 52) for row in rows]
    metadata = [_datum_meta(metric, value, [row]) for metric, value, row in zip(metrics, values, rows)]
    sizes = []
    for row in rows:
        n = _number(row.get("sample_size"))
        sizes.append(max(8, min(28, math.sqrt(n) if n else 10)))

    fig = go.Figure(data=[
        go.Scatter(
            x=years,
            y=values,
            mode="markers",
            marker={
                "size": sizes,
                "color": values,
                "colorscale": [[0, "#FFEDD5"], [0.5, "#E25A3D"], [1, "#1A1A1A"]],
                "line": {"color": "#666666", "width": 0.8},
                "showscale": False,
            },
            text=metrics,
            customdata=metadata,
            hovertemplate="<b>%{text}</b><br>%{customdata.evidence[0].paperTitle}<br>Year: %{x}<br>Value: %{y:.3f}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Extracted values over publication time"),
        xaxis={"title": "Publication year", "gridcolor": "#E5E7EB"},
        yaxis={"title": "Extracted numeric value", "gridcolor": "#E5E7EB", "zerolinecolor": "#9CA3AF"},
        height=360,
    )

    insight = (
        f"{len(rows)} dated findings span {years[0]}-{years[-1]}; "
        f"the earliest value is {values[0]:.2f} and the latest is {values[-1]:.2f}."
    )
    return _figure_dict(fig), insight


def chartable_counts(findings: list[dict], analysis: dict) -> dict[str, int]:
    return {
        "forest_plot": len(_numeric_findings(findings)),
        "bar_comparison": len((analysis.get("compare") or {}).get("groups") or []),
        "timeline": len([
            row for row in _numeric_findings(findings)
            if isinstance(row.get("year"), int) or str(row.get("year") or "").isdigit()
        ]),
    }
