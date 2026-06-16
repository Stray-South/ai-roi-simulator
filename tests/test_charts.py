"""Phase 7 + 8 chart tests — Plotly figure shape, not visual rendering."""

from __future__ import annotations

import plotly.graph_objects as go
import pytest

from roi_calc.models import BreakEvenResult, PeopleInputs
from roi_calc.people_engine import cumulative_cost_vs_savings
from ui.charts import break_even_chart, tornado_chart


# ---------------------------------------------------------------------------
# break_even_chart (Phase 7)
# ---------------------------------------------------------------------------

def test_break_even_chart_returns_plotly_figure() -> None:
    result = cumulative_cost_vs_savings(PeopleInputs())
    fig = break_even_chart(result)
    assert isinstance(fig, go.Figure)


def test_break_even_chart_has_cost_and_savings_lines() -> None:
    """At sample defaults: investment-phase polygon (amber fill) + cost line + savings line = 3 traces."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    fig = break_even_chart(result)
    # Two line+marker traces (cost + savings) plus optional investment-phase polygon
    line_traces = [t for t in fig.data if getattr(t, "mode", "") == "lines+markers"]
    assert len(line_traces) == 2


def test_break_even_chart_skips_polygon_when_single_investment_month() -> None:
    """Edge: 1-month investment region collapses to a 2-point polygon = zero-width
    vertical line that Plotly cannot fill. Guard against the silent-no-fill case
    by requiring ≥2 investment months for the amber polygon to render."""
    result = BreakEvenResult(
        months=(1, 2, 3),
        cumulative_cost=(100.0, 90.0, 80.0),
        cumulative_savings=(50.0, 95.0, 200.0),  # month 1: cost > savings; months 2+: savings > cost
        breakeven_month=2,
    )
    fig = break_even_chart(result)
    polygon_traces = [
        t for t in fig.data
        if getattr(t, "fill", "") == "toself"
        and getattr(t, "fillcolor", "") == "rgba(245, 158, 11, 0.18)"
    ]
    assert len(polygon_traces) == 0  # 1-point investment region → no polygon


def test_break_even_chart_amber_fill_only_in_investment_region() -> None:
    """Gate 6: amber polygon is filled only where cost > savings (investment phase),
    NOT in the post-breakeven region."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    fig = break_even_chart(result)
    polygon_traces = [
        t for t in fig.data
        if getattr(t, "fill", "") == "toself"
        and getattr(t, "fillcolor", "") == "rgba(245, 158, 11, 0.18)"
    ]
    assert len(polygon_traces) == 1
    # The polygon's x-coordinates are months where cost > savings (forward + reverse).
    # At sample defaults breakeven is month 8, so investment region is months 1-7.
    poly_x = list(polygon_traces[0].x)
    # Polygon traces forward through investment months then reverses — all values ≤ 7
    assert max(poly_x) <= 7


def test_break_even_chart_annotates_breakeven_month() -> None:
    """At sample defaults breakeven is M8 — annotation must reference it."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    fig = break_even_chart(result)
    # Plotly stores vline annotations in fig.layout.annotations
    annotations = [a.text for a in fig.layout.annotations if a.text]
    assert any("Month 8" in a or "Break-even" in a for a in annotations)


def test_break_even_chart_handles_no_breakeven() -> None:
    """If breakeven_month is None, no vline annotation; chart still renders.
    The full horizon is investment phase so polygon is the entire region."""
    empty_result = BreakEvenResult(
        months=tuple(range(1, 13)),
        cumulative_cost=tuple([100.0] * 12),
        cumulative_savings=tuple([0.0] * 12),
        breakeven_month=None,
    )
    fig = break_even_chart(empty_result)
    assert isinstance(fig, go.Figure)
    # 1 polygon (full horizon is investment) + 2 line traces = 3
    line_traces = [t for t in fig.data if getattr(t, "mode", "") == "lines+markers"]
    assert len(line_traces) == 2


def test_break_even_chart_uses_spec_colors() -> None:
    """Phase 15 light-theme palette: red cost #B33B2E, green savings #2D7A5C
    per .streamlit/config.toml + Design Handoff §03 (was #EF4444 / #10B981
    in the dark-theme palette).
    """
    result = cumulative_cost_vs_savings(PeopleInputs())
    fig = break_even_chart(result)
    colors = [t.line.color for t in fig.data if getattr(t, "line", None) and t.line.color]
    assert "#B33B2E" in colors  # red cost (light theme)
    assert "#2D7A5C" in colors  # green savings (light theme)


# ---------------------------------------------------------------------------
# tornado_chart (Phase 8 consumes this)
# ---------------------------------------------------------------------------

def test_tornado_chart_returns_plotly_figure() -> None:
    from roi_calc.sensitivity import tornado_for_people
    bars = tornado_for_people(PeopleInputs())
    fig = tornado_chart(bars)
    assert isinstance(fig, go.Figure)


def test_tornado_chart_empty_input_returns_empty_figure() -> None:
    fig = tornado_chart([])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_tornado_chart_orphans_render_gray() -> None:
    """DL-19: orphan bars must render in the light-theme neutral gray.
    Phase 15 refresh: #6B7280 (dark-theme) → #9CA3AF (light-theme).
    """
    from roi_calc.sensitivity import tornado_for_people
    bars = tornado_for_people(PeopleInputs())
    fig = tornado_chart(bars)
    # Gather all marker colors from non-empty traces
    all_colors = []
    for trace in fig.data:
        if hasattr(trace.marker, "color") and trace.marker.color is not None:
            color = trace.marker.color
            if isinstance(color, (list, tuple)):
                all_colors.extend(color)
            else:
                all_colors.append(color)
    # At least one orphan present → light-theme gray must appear
    assert "#9CA3AF" in all_colors


def test_tornado_chart_hovertemplate_uses_customdata_not_arithmetic() -> None:
    """Phase 15 fix: Plotly hovertemplate doesn't support arithmetic between
    trace attributes (`%{base+x:$,.0f}` renders the literal text "base+x").
    The post-fix tornado pre-computes absolute hover values via `customdata`
    and references `%{customdata:$,.0f}`. This regression guards against the
    bug reappearing.
    """
    from roi_calc.sensitivity import tornado_for_people
    bars = tornado_for_people(PeopleInputs())
    fig = tornado_chart(bars)
    for trace in fig.data:
        template = str(getattr(trace, "hovertemplate", "") or "")
        assert "base+x" not in template, (
            f"hovertemplate contains invalid arithmetic syntax: {template!r}"
        )
        if template:
            assert "customdata" in template, (
                f"hovertemplate should reference customdata: {template!r}"
            )
        # And customdata must be populated when hovertemplate references it.
        if "customdata" in template:
            assert trace.customdata is not None, (
                "trace references %{customdata} but customdata is None"
            )
