import json
import math
import re
from typing import Any

import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from tools.numbers import NUMBER_RE, number_from_value


def _figure_dict(fig: go.Figure) -> dict:
    payload = json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))
    payload.get("layout", {}).pop("template", None)
    return payload


def _number(value: Any) -> float | None:
    return number_from_value(value)


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


def _join_sources(titles: list[Any], limit: int = 3) -> str:
    names: list[str] = []
    seen: set[str] = set()
    for title in titles:
        name = _short(title, 60)
        if not name or name == "Untitled" or name in seen:
            continue
        seen.add(name)
        names.append(name)
        if len(names) >= limit:
            break
    return ", ".join(names) if names else "source metadata"


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


def source_mix(findings: list[dict]) -> tuple[dict, str]:
    counts: dict[str, int] = {}
    for finding in findings:
        source_type = str(finding.get("source_type") or "unknown").replace("_", " ").title()
        counts[source_type] = counts.get(source_type, 0) + 1

    if not counts:
        raise ValueError("source_mix requires at least one finding")

    labels = list(counts.keys())
    values = list(counts.values())
    colors = ["#38bdf8", "#22c55e", "#f59e0b", "#a78bfa", "#f43f5e"][: len(labels)]

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker={"color": colors, "line": {"color": "#e5e7eb", "width": 0.5}},
            hovertemplate="<b>%{x}</b><br>Findings: %{y}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Evidence mix by source type"),
        xaxis={"title": "Source type", "gridcolor": "#111111"},
        yaxis={"title": "Extracted or computed findings", "gridcolor": "#1f2937"},
        height=330,
    )

    top_idx = max(range(len(values)), key=lambda idx: values[idx])
    insight = f"{labels[top_idx]} contributes the most evidence items in this run ({values[top_idx]} findings)."
    return _figure_dict(fig), insight


def dataset_metric_summary(findings: list[dict]) -> tuple[dict, str]:
    rows = [
        row for row in _numeric_findings(findings)
        if row.get("source_type") == "dataset"
    ][:12]
    if not rows:
        raise ValueError("dataset_metric_summary requires dataset findings")

    labels = [_short(row.get("metric"), 42) for row in rows]
    values = [row["_numeric_value"] for row in rows]
    sources = [_short(row.get("source_title"), 80) for row in rows]

    fig = go.Figure(data=[
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker={"color": "#14b8a6", "line": {"color": "#99f6e4", "width": 0.8}},
            customdata=sources,
            hovertemplate="<b>%{y}</b><br>Computed value: %{x:.3f}<br>%{customdata}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Computed statistics from public datasets"),
        xaxis={"title": "Computed numeric value", "gridcolor": "#1f2937", "zerolinecolor": "#4b5563"},
        yaxis={"autorange": "reversed", "gridcolor": "#111111"},
        height=max(340, 120 + len(rows) * 32),
    )

    insight = f"{len(rows)} computed dataset statistics are shown; hover each bar to see the source dataset."
    return _figure_dict(fig), insight


def trend_series(findings: list[dict]) -> tuple[dict, str]:
    rows = [
        row for row in _numeric_findings(findings)
        if row.get("series_id") and (isinstance(row.get("year"), int) or str(row.get("year") or "").isdigit())
    ]
    if len(rows) < 4:
        raise ValueError("trend_series requires at least four dated series findings")

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("series_id")), []).append(row)

    traces = []
    source_titles: list[str] = []
    plotted = 0
    for series_id, series_rows in grouped.items():
        series_rows = sorted(series_rows, key=lambda row: int(row["year"]))
        if len(series_rows) < 2:
            continue
        first_value = series_rows[0]["_numeric_value"]
        if not first_value:
            continue
        years = [int(row["year"]) for row in series_rows]
        normalized = [round(100 * row["_numeric_value"] / first_value, 2) for row in series_rows]
        raw_values = [row.get("value") for row in series_rows]
        label = _short(series_rows[-1].get("source_title") or series_rows[-1].get("metric"), 54)
        source_titles.append(label)
        traces.append(go.Scatter(
            x=years,
            y=normalized,
            mode="lines+markers",
            name=label,
            customdata=raw_values,
            hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Indexed: %{y:.1f}<br>Raw: %{customdata}<extra></extra>",
        ))
        plotted += 1
        if plotted >= 5:
            break

    if not traces:
        raise ValueError("trend_series found no plottable series")

    fig = go.Figure(data=traces)
    fig.update_layout(
        **_base_layout("Indexed trusted time-series trends"),
        xaxis={"title": "Year", "gridcolor": "#1f2937"},
        yaxis={"title": "Index (first observed year = 100)", "gridcolor": "#1f2937", "zerolinecolor": "#4b5563"},
        legend={"orientation": "h", "y": -0.28},
        height=430,
        annotations=[
            {
                "text": "Each line starts at 100 in its first observed year; compare direction, not units.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.08,
                "showarrow": False,
                "font": {"size": 11, "color": "#94a3b8"},
                "align": "left",
            }
        ],
    )
    insight = (
        f"{plotted} trusted time series are indexed to their first observed year, "
        f"so directional movement can be compared without mixing units (sources: {_join_sources(source_titles)})."
    )
    return _figure_dict(fig), insight


def evidence_quality(validation_report: dict) -> tuple[dict, str]:
    rows = validation_report.get("source_scores") or []
    rows = [row for row in rows if row.get("credibility_score") is not None][:18]
    if not rows:
        raise ValueError("evidence_quality requires validation source scores")

    labels = [_short(row.get("title") or row.get("provider"), 46) for row in rows]
    values = [float(row.get("credibility_score") or 0) for row in rows]
    providers = [row.get("provider") or "Unknown" for row in rows]
    colors = ["#22c55e" if value >= 0.85 else "#f59e0b" if value >= 0.7 else "#f43f5e" for value in values]

    fig = go.Figure(data=[
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker={"color": colors, "line": {"color": "#e5e7eb", "width": 0.4}},
            customdata=providers,
            hovertemplate="<b>%{y}</b><br>Provider: %{customdata}<br>Credibility score: %{x:.2f}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Evidence quality and source credibility"),
        xaxis={"title": "Credibility score", "range": [0, 1], "gridcolor": "#1f2937"},
        yaxis={"autorange": "reversed", "gridcolor": "#111111"},
        height=max(360, 110 + len(rows) * 28),
        annotations=[
            {
                "text": "Green = stronger source base; amber/red = use as directional or caveated evidence.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.08,
                "showarrow": False,
                "font": {"size": 11, "color": "#94a3b8"},
                "align": "left",
            }
        ],
    )
    avg = validation_report.get("average_credibility", 0)
    insight = (
        f"Average source credibility is {avg}; lower-scored sources should be treated as directional, "
        f"not definitive (examples: {_join_sources([row.get('title') for row in rows])})."
    )
    return _figure_dict(fig), insight


def scenario_matrix(economic_model: dict) -> tuple[dict, str]:
    scenarios = economic_model.get("scenarios") or []
    if not scenarios:
        raise ValueError("scenario_matrix requires economic scenarios")

    confidence_score = {"low": 0.35, "medium": 0.65, "high": 0.9}
    labels = [_short(row.get("name"), 36) for row in scenarios[:6]]
    values = [confidence_score.get(str(row.get("confidence", "")).lower(), 0.5) for row in scenarios[:6]]
    outcomes = [_short(row.get("directional_outcome"), 110) for row in scenarios[:6]]
    evidence = [_join_sources(row.get("evidence_basis") or [], limit=2) for row in scenarios[:6]]
    colors = ["#38bdf8", "#22c55e", "#f59e0b", "#f43f5e", "#a78bfa", "#14b8a6"][: len(labels)]

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker={"color": colors, "line": {"color": "#e5e7eb", "width": 0.5}},
            customdata=list(zip(outcomes, evidence, strict=False)),
            hovertemplate="<b>%{x}</b><br>Confidence: %{y:.2f}<br>%{customdata[0]}<br>Evidence: %{customdata[1]}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Scenario confidence map"),
        xaxis={"title": "Scenario", "gridcolor": "#111111"},
        yaxis={"title": "Qualitative confidence score", "range": [0, 1], "gridcolor": "#1f2937"},
        height=340,
        annotations=[
            {
                "text": "Qualitative scenarios only; no invented percentages or point forecasts.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.08,
                "showarrow": False,
                "font": {"size": 11, "color": "#94a3b8"},
                "align": "left",
            }
        ],
    )
    insight = (
        "Scenarios are qualitative and assumption-driven; confidence reflects evidence strength, not certainty "
        f"(evidence examples: {_join_sources([item for row in scenarios for item in (row.get('evidence_basis') or [])])})."
    )
    return _figure_dict(fig), insight


def trend_change_summary(analysis: dict) -> tuple[dict, str]:
    trends = ((analysis.get("trends") or {}).get("trends") or [])[:12]
    rows = [
        trend for trend in trends
        if trend.get("pct_change") is not None or trend.get("absolute_change") is not None
    ]
    if not rows:
        raise ValueError("trend_change_summary requires trend analysis output")

    use_pct = any(row.get("pct_change") is not None for row in rows)
    values = [
        float(row.get("pct_change") if use_pct and row.get("pct_change") is not None else row.get("absolute_change") or 0)
        for row in rows
    ]
    labels = [_short(row.get("metric") or row.get("source_title") or row.get("series_id"), 52) for row in rows]
    sources = [_short(row.get("source_title") or row.get("provider") or "", 70) for row in rows]
    periods = [
        f"{row.get('start_year', 'n/a')}-{row.get('latest_year', 'n/a')}"
        for row in rows
    ]
    colors = ["#22c55e" if value >= 0 else "#f97316" for value in values]

    fig = go.Figure(data=[
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker={"color": colors, "line": {"color": "#e5e7eb", "width": 0.5}},
            customdata=list(zip(sources, periods, strict=False)),
            hovertemplate=(
                "<b>%{y}</b><br>"
                + ("Change: %{x:.2f}%" if use_pct else "Change: %{x:.3f}")
                + "<br>Period: %{customdata[1]}<br>Source: %{customdata[0]}<extra></extra>"
            ),
        )
    ])
    fig.update_layout(
        **_base_layout("Historical change in key indicators"),
        xaxis={
            "title": "Percent change" if use_pct else "Absolute change",
            "gridcolor": "#1f2937",
            "zerolinecolor": "#94a3b8",
        },
        yaxis={"autorange": "reversed", "gridcolor": "#111111"},
        height=max(340, 120 + len(rows) * 34),
        annotations=[
            {
                "text": "Uses computed trend analysis from loaded public time series; period differs by source availability.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.08,
                "showarrow": False,
                "font": {"size": 11, "color": "#94a3b8"},
                "align": "left",
            }
        ],
    )
    strongest_idx = max(range(len(values)), key=lambda idx: abs(values[idx]))
    unit = "%" if use_pct else ""
    insight = (
        f"The largest displayed historical movement is {labels[strongest_idx]} "
        f"({values[strongest_idx]:.2f}{unit}, source: {sources[strongest_idx]})."
    )
    return _figure_dict(fig), insight


def claim_support_status(fact_check_report: dict) -> tuple[dict, str]:
    claims = fact_check_report.get("checked_claims") or []
    if not claims:
        raise ValueError("claim_support_status requires checked claims")

    labels_order = ["supported", "partially_supported", "contradicted", "insufficient_evidence"]
    counts = {label: 0 for label in labels_order}
    for claim in claims:
        status = str(claim.get("status") or "insufficient_evidence")
        counts[status if status in counts else "insufficient_evidence"] += 1

    labels = [label.replace("_", " ").title() for label in labels_order]
    values = [counts[label] for label in labels_order]
    colors = ["#22c55e", "#f59e0b", "#ef4444", "#64748b"]

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker={"color": colors, "line": {"color": "#e5e7eb", "width": 0.5}},
            hovertemplate="<b>%{x}</b><br>Claims: %{y}<extra></extra>",
        )
    ])
    fig.update_layout(
        **_base_layout("Fact-check status of major claims"),
        xaxis={"title": "Claim status", "gridcolor": "#111111"},
        yaxis={"title": "Checked claims", "dtick": 1, "gridcolor": "#1f2937"},
        height=330,
        annotations=[
            {
                "text": "Only claims backed by provided sources should appear as findings in the report.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.08,
                "showarrow": False,
                "font": {"size": 11, "color": "#94a3b8"},
                "align": "left",
            }
        ],
    )
    unsupported = counts["contradicted"] + counts["insufficient_evidence"]
    insight = (
        f"{values[0]} claim(s) are fully supported and {unsupported} claim(s) need caveats or exclusion."
    )
    return _figure_dict(fig), insight


def chartable_counts(findings: list[dict], analysis: dict, validation_report: dict | None = None, economic_model: dict | None = None) -> dict[str, int]:
    return {
        "trend_series": len([
            row for row in _numeric_findings(findings)
            if row.get("series_id") and (isinstance(row.get("year"), int) or str(row.get("year") or "").isdigit())
        ]),
        "trend_change_summary": len((analysis.get("trends") or {}).get("trends") or []),
        "evidence_quality": len((validation_report or {}).get("source_scores") or []),
        "scenario_matrix": len((economic_model or {}).get("scenarios") or []),
        "forest_plot": len(_numeric_findings(findings)),
        "bar_comparison": len((analysis.get("compare") or {}).get("groups") or []),
        "timeline": len([
            row for row in _numeric_findings(findings)
            if isinstance(row.get("year"), int) or str(row.get("year") or "").isdigit()
        ]),
        "source_mix": len(findings),
        "dataset_metric_summary": len([
            row for row in _numeric_findings(findings)
            if row.get("source_type") == "dataset"
        ]),
    }
