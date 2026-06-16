"""Plotly chart factories shared across tabs.

Phase 7: ``break_even_chart``
Phase 8: ``tornado_chart``
Phase 10: ``j_curve_chart``, ``capability_radar``

Phase 15 design refresh: light canvas + mono ticks + IBM Plex typography via
``_apply_light_theme``. Series-line colors and the amber investment-phase
polygon are unchanged in CONCEPT but updated to the light-theme palette:
  * red (cost)     #B33B2E   (was #EF4444)
  * green (savings) #2D7A5C  (was #10B981)
  * amber (T5)     #F59E0B   (LOCKED, unchanged)
  * navy marker    #1F2A44   (break-even vline, was #907AFF)
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from roi_calc.models import BreakEvenResult


__all__ = ["break_even_chart", "tornado_chart"]


# ---------- Phase 15 light-theme tokens (mirror ui/assets/theme.css) ----------
_INK = "#2A2520"
_MUTED = "#8A8278"
_RULE = "#E8E2D7"
_BG = "#FBFAF7"
_SURFACE = "#FFFFFF"
_FONT_SANS = "IBM Plex Sans, system-ui, sans-serif"
_FONT_MONO = "IBM Plex Mono, ui-monospace, monospace"


def _apply_light_theme(fig: go.Figure, *, title: str | None = None) -> go.Figure:
    """Shared canvas styling for People + Engineering charts.

    Lifted out so ``break_even_chart()`` and ``tornado_chart()`` stay in sync.
    Series-line colors + the amber investment-phase polygon are set in the
    per-chart factory; this helper only touches the canvas + ticks + legend +
    hover label.
    """
    fig.update_layout(
        title=title,  # titles render in the surrounding st.subheader by default
        paper_bgcolor=_SURFACE,
        plot_bgcolor=_SURFACE,
        font=dict(family=_FONT_SANS, size=12, color=_INK),
        margin=dict(l=56, r=24, t=28, b=42),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family=_FONT_MONO, size=11, color=_INK),
        ),
        hoverlabel=dict(
            bgcolor=_SURFACE, bordercolor=_RULE,
            font=dict(family=_FONT_MONO, color=_INK, size=12),
        ),
    )
    fig.update_xaxes(
        gridcolor=_RULE, zerolinecolor=_RULE,
        tickfont=dict(family=_FONT_MONO, size=11, color=_MUTED),
        title_font=dict(family=_FONT_SANS, size=12, color=_MUTED),
    )
    fig.update_yaxes(
        gridcolor=_RULE, zerolinecolor=_RULE,
        tickfont=dict(family=_FONT_MONO, size=11, color=_MUTED),
        title_font=dict(family=_FONT_SANS, size=12, color=_MUTED),
        tickformat="$,.0f",
    )
    return fig


def break_even_chart(result: BreakEvenResult) -> go.Figure:
    """Two-line cumulative cost vs savings over the analysis horizon.

    Spec §6.2 contract:
      * Red line — cumulative implementation cost
      * Green line — cumulative net savings
      * Vertical annotation at ``breakeven_month`` (if not None)
      * Amber-shaded region where cost > savings ("Investment phase")
      * Caption noting calibrated parameters

    Gate 6: this is a VISUALIZATION of computed series, not a parameter-driven
    "predicted curve." The trough is just the region where one line is above
    the other — no invented depth %.
    """
    fig = go.Figure()

    months = list(result.months)
    cost = list(result.cumulative_cost)
    savings = list(result.cumulative_savings)

    # Amber "Investment phase" polygon — fills ONLY where cost > savings,
    # not the post-breakeven region. Spec §6.2 + Gate 6 explicitly require this.
    inv_months = [m for m, c, s in zip(months, cost, savings) if c > s]
    inv_cost = [c for c, s in zip(cost, savings) if c > s]
    inv_savings = [s for c, s in zip(cost, savings) if c > s]
    # Require ≥2 investment months — a 1-point polygon collapses to a vertical
    # line and Plotly renders no fill. Better to omit the polygon entirely
    # than show an invisible amber region.
    if len(inv_months) >= 2:
        fig.add_trace(
            go.Scatter(
                x=inv_months + inv_months[::-1],
                y=inv_cost + inv_savings[::-1],
                fill="toself",
                fillcolor="rgba(245, 158, 11, 0.18)",
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=True,
                name="Investment phase",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=months, y=cost,
            mode="lines+markers",
            name="Cumulative implementation cost",
            line=dict(color="#B33B2E", width=3),  # red — light-theme palette
        )
    )
    fig.add_trace(
        go.Scatter(
            x=months, y=savings,
            mode="lines+markers",
            name="Cumulative net savings",
            line=dict(color="#2D7A5C", width=3),  # green — light-theme palette
        )
    )

    if result.breakeven_month is not None:
        fig.add_vline(
            x=result.breakeven_month,
            # Navy marker (was #907AFF dark-theme accent). Width 1.5 for a finer
            # editorial weight than the prior 2px on a light canvas.
            line=dict(color="#1F2A44", width=1.5, dash="dash"),
            annotation_text=f"Break-even: Month {result.breakeven_month}",
            annotation_position="top",
            annotation_font=dict(family=_FONT_MONO, size=11, color=_INK),
        )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="USD",
        height=420,
        showlegend=True,
    )
    _apply_light_theme(fig)
    return fig


def tornado_chart(bars: list[Any], title: str = "Sensitivity tornado") -> go.Figure:
    """Horizontal tornado bar chart from a list of TornadoBar dataclasses.

    Orphan bars (DL-19) render in gray with annotation 'wires in Phase 9 / Day 90'.
    Used by Phase 8 People Sensitivity + Engineering Sensitivity tabs.
    """
    if not bars:
        return go.Figure()  # empty chart — Phase 8 caller may want to short-circuit

    # Phase 5 already sorts non-orphan by |swing| desc; orphans appended last.
    # Reverse for top-down display in Plotly horizontal bar.
    bars_for_display = list(reversed(bars))

    y_labels = [b.field_name for b in bars_for_display]
    low_vals = [b.low_value_output for b in bars_for_display]
    high_vals = [b.high_value_output for b in bars_for_display]
    # Phase 15 light-theme palette: navy for wired bars, neutral gray for orphans.
    colors = ["#9CA3AF" if b.is_orphan else "#1F2A44" for b in bars_for_display]

    # Tornado is two bars per row: low extends left, high extends right from a baseline.
    # Implement as two go.Bar traces.
    fig = go.Figure()

    baseline = [(l + h) / 2 for l, h in zip(low_vals, high_vals)]
    low_offset = [l - b for l, b in zip(low_vals, baseline)]
    high_offset = [h - b for h, b in zip(high_vals, baseline)]

    # Phase 15 fix: Plotly hovertemplate doesn't support arithmetic between
    # trace attributes (e.g. `%{base+x:$,.0f}` renders the literal text
    # "base+x"). Pre-compute the absolute hover values and pass them via
    # `customdata`, then reference `%{customdata:$,.0f}` instead.
    fig.add_trace(
        go.Bar(
            y=y_labels, x=high_offset,
            base=baseline,
            orientation="h",
            marker_color=colors,
            name="High",
            customdata=high_vals,
            hovertemplate="%{y}<br>high: %{customdata:$,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=y_labels, x=low_offset,
            base=baseline,
            orientation="h",
            marker_color=colors,
            name="Low",
            customdata=low_vals,
            hovertemplate="%{y}<br>low: %{customdata:$,.0f}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis_title="Output ($)",
        yaxis_title="",
        barmode="overlay",
        height=max(300, 30 * len(bars_for_display)),
        margin=dict(l=200, r=20, t=28, b=42),
        showlegend=False,
    )
    _apply_light_theme(fig, title=title)
    return fig
