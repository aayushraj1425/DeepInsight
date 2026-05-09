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
        "title": {"text": title, "x": 0.02, "font": {"size": 16}},
        "font": {"color": "#e5e7eb", "family": "Inter, ui-sans-serif, system-ui"},
        "paper_bgcolor": "#111111",
        "plot_bgcolor": "#111111",
        "margin": {"l": 72, "r": 28, "t": 58, "b": 56},
        "hoverlabel": {"bgcolor": "#111827", "font": {"color": "#f9fafb"}},
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


def forest_plot(findings: list[dict]) -> tuple[dict, str]:
    rows = _numeric_findings(findings)[:16]
    if not rows:
        raise ValueError("forest_plot requires at least one numeric finding")

    labels = [
        _short(row.get("paper_title") or row.get("metric") or f"Finding {idx + 1}", 58)
        for idx, row in enumerate(rows)
    ]
    values = [row["_numeric_value"] for row in rows]
    hover = [
        (
            f"<b>{_short(row.get('metric'), 90)}</b><br>"
            f"Value: {row.get('value')}<br>"
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
        "marker": {"size": 10, "color": "#38bdf8", "line": {"color": "#bae6fd", "width": 1}},
        "hovertemplate": hover,
        "orientation": "h",
    }
    if has_error:
        trace["error_x"] = {
            "type": "data",
            "array": error_plus,
            "arrayminus": error_minus,
            "visible": True,
            "color": "#93c5fd",
            "thickness": 1.5,
        }

    fig = go.Figure(data=[go.Scatter(**trace)])
    fig.update_layout(
        **_base_layout("Effect estimates across extracted findings"),
        xaxis={"title": "Extracted numeric value", "gridcolor": "#1f2937", "zerolinecolor": "#4b5563"},
        yaxis={"autorange": "reversed", "gridcolor": "#111111"},
        height=max(360, 92 + len(rows) * 34),
    )

    insight = (
        f"{len(rows)} numeric findings plotted; extracted values range "
        f"from {min(values):.2f} to {max(values):.2f}."
    )
    return _figure_dict(fig), insight


def bar_comparison(compare_result: dict) -> tuple[dict, str]:
    groups = compare_result.get("groups") or []
    if not groups:
        raise ValueError("bar_comparison requires compare_result['groups']")

    group_by = compare_result.get("group_by") or "group"
    labels = [_short(row.get(group_by) or row.get("metric") or row.get("intervention"), 40) for row in groups]
    values = [_number(row.get("avg_value")) or 0 for row in groups]
    errors = [_number(row.get("std_dev")) or 0 for row in groups]
    counts = [row.get("n_studies", 0) for row in groups]

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker={"color": "#22c55e", "line": {"color": "#bbf7d0", "width": 1}},
            error_y={"type": "data", "array": errors, "visible": any(e > 0 for e in errors), "color": "#86efac"},
            customdata=counts,
            hovertemplate="<b>%{x}</b><br>Average: %{y:.3f}<br>Studies: %{customdata}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout(f"Average extracted value by {group_by}"),
        xaxis={"title": str(group_by).replace("_", " "), "gridcolor": "#111111"},
        yaxis={"title": "Average numeric value", "gridcolor": "#1f2937", "zerolinecolor": "#4b5563"},
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
                "colorscale": [[0, "#f97316"], [0.5, "#eab308"], [1, "#14b8a6"]],
                "line": {"color": "#f9fafb", "width": 0.8},
                "showscale": False,
            },
            text=metrics,
            customdata=[_short(row.get("paper_title"), 90) for row in rows],
            hovertemplate="<b>%{text}</b><br>%{customdata}<br>Year: %{x}<br>Value: %{y:.3f}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Extracted values over publication time"),
        xaxis={"title": "Publication year", "gridcolor": "#1f2937"},
        yaxis={"title": "Extracted numeric value", "gridcolor": "#1f2937", "zerolinecolor": "#4b5563"},
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
