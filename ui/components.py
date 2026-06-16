"""Shared UI components for the AI ROI Simulator (Phase 6).

DL-12: amber T5 widget background is rendered via custom CSS using
``st.markdown(unsafe_allow_html=True)``, NOT via theme tokens.
``.streamlit/config.toml`` controls the dark theme + Plotly palette;
``#FFF7ED`` for T5 widget backgrounds comes from here.

DL-16 + Cascade 8 sibling: the Confidence Audit tab (Phase 9) and the
inputs Review tab (Phase 11) both depend on these helpers + ``FRIENDLY_LABELS``.
"""

from __future__ import annotations

from typing import Any, Callable, Literal

import streamlit as st

from roi_calc.constants import Citation


__all__ = [
    "AMBER_BG",
    "FRIENDLY_LABELS",
    "amber_flag_widget",
    "citation_tooltip",
    "render_amber_block",
    "render_tile",
    "render_portfolio_compact",  # v3 — canvas-faithful 6th-cell variant
    "render_portfolio_tile",     # full-width hero (kept for compatibility)
    "render_footer_html",
]


AMBER_BG = "#FFF7ED"

# Per spec §8.4 (label suffix convention) — Phase 9 + Phase 11 render T5 inputs
# with the citation's amber `.flag` text suffixed to the human-readable label.
# Keep these in sync with the PeopleInputs / EngineeringInputs field names.
FRIENDLY_LABELS: dict[str, str] = {
    # Organization (People)
    "employees": "Employees (headcount)",
    "annual_hires": "Annual hires",
    "fully_loaded_cost_per_fte": "Fully-loaded cost per FTE ($)",
    "hr_specialist_loaded_hourly": "HR Specialist loaded hourly ($)",
    "it_specialist_loaded_hourly": "IT Specialist loaded hourly ($)",
    "manager_loaded_hourly": "HR Manager loaded hourly ($)",
    # T·T·D primitives
    "onboarding_touches_per_event_baseline": "Onboarding touches per event",
    "onboarding_avg_minutes_per_touch_baseline": "Avg minutes per touch",
    "decision_points_per_event_baseline": "Decision points per event",
    "decision_point_error_cost_avg": "Decision-point error cost ($)",
    # AI automation
    "touches_automated_pct": "Touches automated (%)",
    "time_per_touch_reduction_pct": "Time-per-touch reduction (%)",
    "decision_point_error_rate_baseline": "Decision-point error rate (baseline)",
    "decision_point_error_rate_with_ai": "Decision-point error rate (with AI)",
    # J-Curve timing
    "learning_curve_months": "Learning curve (months)",
    "time_to_steady_state_months": "Time to steady-state (months)",
    "horizon_months": "Analysis horizon (months)",
    # Capability multipliers (decorative Option D)
    "training_spend_ppt": "Training spend (ppt)",
    "manager_support_score": "Manager support score (1–5)",
    # Scenario
    "pipeline_scenario": "Pipeline scenario",
    # Engineering Mode
    "engineers": "Engineering headcount",
    "cfr_before": "CFR before AI",
    "cfr_after": "CFR after AI",
    "deploys_per_year": "Deploys per year",
    "incident_cost": "Per-incident cost ($)",
    "self_report_discount": "METR self-report discount",
    "archetype": "DORA archetype",
    "clear_ai_stance": "Clear AI stance (1–5)",
    "healthy_data_ecosystem": "Healthy data ecosystem (1–5)",
    "ai_accessible_data": "AI-accessible data (1–5)",
    "version_control": "Version control (1–5)",
    "small_batches": "Small batches (1–5)",
    "user_centric_focus": "User-centric focus (1–5)",
    "quality_platform": "Quality platform (1–5)",
    # Engineering Mode v3 §5.1 productivity formula (Phase 14 Stream B2 / DL-29)
    "ai_adoption_pct": "AI adoption (%)",
    "ai_hours_per_workday": "AI hours per workday",
    "productivity_gain_greenfield": "Productivity gain — greenfield (%)",
    "productivity_gain_legacy": "Productivity gain — legacy (%)",
    "pct_work_greenfield": "Greenfield work mix (%)",
    "engineering_verification_tax": "Engineering verification tax (%)",
    "workdays_per_year": "Workdays per year",
}


def friendly_label(field_name: str) -> str:
    """Return the human-readable label for a field, or the raw name if unmapped."""
    return FRIENDLY_LABELS.get(field_name, field_name)


def citation_tooltip(citation: Citation) -> str:
    """Compose the help-text shown on hover for a Citation-backed input.

    Format: ``"[T1] source string"`` (or with flag prefix if T5).
    """
    flag = f"{citation.flag}  " if citation.flag else ""
    return f"{flag}[{citation.tier}] {citation.source}"


def render_amber_block(label: str, flag: str) -> None:
    """Render an amber-tinted info block via ``st.markdown(unsafe_allow_html=True)``.

    Used by ``amber_flag_widget`` and by Phase 9 Confidence Audit rows to
    surface the T5 calibration disclosure.
    """
    st.markdown(
        f'<div style="background-color: {AMBER_BG}; padding: 8px 12px; '
        f'border-left: 4px solid #F59E0B; border-radius: 4px; '
        f'margin: 4px 0; font-size: 0.85em;">'
        f"<strong>{label}</strong> &nbsp; <em>{flag}</em></div>",
        unsafe_allow_html=True,
    )


def amber_flag_widget(
    label: str,
    citation: Citation,
    widget_fn: Callable[..., Any],
    **kwargs: Any,
) -> Any:
    """Wrap a Streamlit input widget with the T5 amber-flag treatment.

    v4 single-render contract: the field name appears EXACTLY ONCE. The
    rendered block is `label + ⚠ T5 pill` (amber-tinted row) above the
    input, the widget itself with its native label hidden, and the
    bracketed source-status flag as a muted caption BELOW the input.

    Pre-v4 this helper rendered the label twice (once in the amber block,
    once as the widget's own label suffixed with ⚠️), which made every T5
    field look like it had a duplicate row.

    For non-T5 citations: passes through to ``widget_fn`` with just the
    label and the citation tooltip in ``help=``.

    Returns whatever ``widget_fn`` returns (Streamlit widgets return their value).
    """
    tooltip = citation_tooltip(citation)
    if citation.tier == "T5" and citation.flag:
        # Amber-tinted row: label on the left, ⚠ T5 pill on the right.
        # Source-status caption renders BELOW the input, not in this row.
        st.markdown(
            f'<div style="background-color: {AMBER_BG}; padding: 8px 12px; '
            f'border-left: 4px solid #F59E0B; border-radius: 4px; '
            f'margin: 6px 0 0; display: flex; justify-content: space-between; '
            f'align-items: center; gap: 12px; font-size: 0.92em;">'
            f'<span style="font-weight: 500; color: var(--ink);">{label}</span>'
            f'<span class="amber-pill">⚠ T5</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
        kwargs.setdefault("help", tooltip)
        # Hide the widget's own label visually so the field name renders ONCE
        # (in the amber row above). Streamlit still emits it for screen readers.
        kwargs.setdefault("label_visibility", "collapsed")
        result = widget_fn(label, **kwargs)
        # Source-status caption — muted, plain text, below the input.
        st.caption(citation.flag)
        return result

    # Non-T5 passthrough: single Streamlit widget with help= tooltip.
    kwargs.setdefault("help", tooltip)
    return widget_fn(label, **kwargs)


# ---------- Phase 15 design refresh — class-based tile/portfolio/footer ----------
# The hard-coded inline styles previously inside `_render_tile` /
# `_render_portfolio_tile` in `ui/results_tab_people.py` move OUT to these
# class-based helpers. Visual styles live in `ui/assets/theme.css`.


def render_tile(
    label: str,
    value: float,
    citation: str,
    *,
    tier: str = "T2",
    kind: Literal["savings", "risk"] = "savings",
    detail: str | None = None,
    calibrated: bool = False,
    tail_risk_note: str | None = None,
    badge: str | None = None,
) -> None:
    """Render one of the five hard-dollar tiles.

    `kind` only controls color tokens (--green for savings, --red for risk).
    `value` is the raw float — formatted here, sign rendered as "−" for risk.
    `tail_risk_note` renders the Mobley/Kistler footnote (Gate 11) when set.
    """
    sign = "−" if kind == "risk" else ""
    formatted = f"${abs(value):,.0f}"
    badge_html = f'<span class="tier tier--{tier}">{tier}</span>'
    extra = ""
    if calibrated:
        extra += ' <span class="amber-pill">⚠ T5</span>'
    if badge:
        extra += f' <span class="tier tier--T2">{badge}</span>'

    tail = ""
    if tail_risk_note:
        tail = (
            '<div class="calibrated-row" style="margin-top: 6px;">'
            f"<strong>Tail risk:</strong> {tail_risk_note}"
            "</div>"
        )

    detail_html = f'<div class="tile__detail">{detail}</div>' if detail else ""

    # Flush-left HTML — see streamlit_app.py header for why indentation matters.
    st.markdown(
        f"""
<div class="tile tile--{kind}">
  <div style="display:flex; justify-content:space-between; gap:8px;">
    <div class="tile__label">{label}</div>
    <div style="display:flex; gap:6px; align-items:center;">{badge_html}</div>
  </div>
  <div class="tile__value">{sign}{formatted}</div>
  {detail_html}
  <div class="tile__footer">
    <span class="tile__citation">{citation}</span>
    <span>{extra}</span>
  </div>
  {tail}
</div>
""",
        unsafe_allow_html=True,
    )


def render_portfolio_compact(net_value: float, gross: float, risk: float) -> None:
    """Render the portfolio tile in the 6th grid cell — canvas-faithful (v3).

    Gate 10: NO compensation comparison. Fits the same column width as the
    other five tiles; the gross/risk breakdown sits inside the same tile
    rather than spanning full-width.
    """
    st.markdown(
        f"""
        <div class="portfolio-tile">
          <div style="display:flex; justify-content:space-between; gap:8px;">
            <div class="portfolio-tile__label">Net Annual Value · Portfolio</div>
            <span class="tier tier--T1">T1</span>
          </div>
          <div class="portfolio-tile__value">${net_value:,.0f}</div>
          <div class="tile__detail">Σ savings (post-tax) − Σ risks</div>
          <div class="portfolio-tile__breakdown">
            <b>Gross</b> ${gross:,.0f} (post-37% tax)<br>
            <b>Risk</b> &nbsp;−${risk:,.0f} exposure
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_portfolio_tile(net_value: float, gross: float, risk: float) -> None:
    """Render the Net Annual Value hero card (full-width).

    Kept for any caller that prefers the hero layout. The canvas-faithful
    People-Mode Results tab uses render_portfolio_compact() instead.
    """
    st.markdown(
        f"""
        <div class="portfolio-hero">
          <div>
            <div class="eyebrow">Net annual value · People Mode portfolio</div>
            <div class="big">${net_value:,.0f}</div>
          </div>
          <div class="breakdown">
            <div>
              <div class="eyebrow">Gross savings (post 37% tax)</div>
              <div class="num" style="font-size:20px; color: var(--green);
                                      margin-top:4px; font-weight: 500;">
                ${gross:,.0f}
              </div>
            </div>
            <div>
              <div class="eyebrow">Risk exposure</div>
              <div class="num" style="font-size:20px; color: var(--red);
                                      margin-top:4px; font-weight: 500;">
                −${risk:,.0f}
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer_html(text: str) -> None:
    """Render the persistent footer with the verbatim text from ui/footer.py.

    The bolded Day-90 sentence (markdown `**...**`) is preserved as inline
    `<strong>` HTML. Footer text is LOCKED by Phase 11 regression tests; this
    helper only restyles, never edits the text.
    """
    parts = text.split("**")
    rendered = "".join(
        f"<strong>{p}</strong>" if i % 2 else p
        for i, p in enumerate(parts)
    )
    st.markdown(
        f'<div class="app-footer"><em>{rendered}</em></div>',
        unsafe_allow_html=True,
    )
