"""Full replacement for ui/results_tab_people.py — v3 (canvas-faithful).

CHANGES from v2:
  * Reverts to the ORIGINAL canvas layout:
    - Header copy: "Five hard-dollar calculations, each net of the Workday
      37% verification tax."
    - Portfolio sits as the 6TH CELL in a 2×3 grid (NOT a full-width hero).
    - The full-width portfolio_hero variant is no longer used here.
  * Uses render_portfolio_compact() — a new helper that fits the tile slot.

All gates still honored:
  - Gate 10: no compensation_multiple display
  - Gate 11: Mobley/Kistler tail-risk footnote on Tile 5
  - Gate 6: chart is visualization, not parameter-driven prediction
"""

from __future__ import annotations

import streamlit as st

from roi_calc.models import PeopleInputs
from roi_calc.people_engine import (
    benefits_billing_recovery_value,
    candidate_pipeline_risk,
    cumulative_cost_vs_savings,
    decision_point_risk_delta,
    help_desk_deflection_value,
    onboarding_productivity_delta_value,
    people_mode_portfolio,
)
from ui.charts import break_even_chart
from ui.components import render_portfolio_compact, render_tile


def render() -> None:
    """Render the People Mode Results tab."""
    inputs: PeopleInputs = st.session_state.get("people_inputs", PeopleInputs())

    st.header("People Mode — Infrastructure Onboarding Results")
    st.markdown(
        "##### Five hard-dollar calculations, each net of the Workday 37% "
        "verification tax (Workday/Hanover n=3,200)"
    )

    # ----- Compute -----
    help_desk = help_desk_deflection_value(inputs)
    onboarding = onboarding_productivity_delta_value(inputs)
    benefits = benefits_billing_recovery_value(inputs)
    pipeline_risk = candidate_pipeline_risk(inputs)
    dp_risk = decision_point_risk_delta(inputs)
    portfolio = people_mode_portfolio(inputs)

    # ----- 2 × 3 grid — five calc tiles + portfolio in 6th cell -----
    row1 = st.columns(3)
    with row1[0]:
        render_tile(
            label="Help Desk Deflection",
            value=help_desk, kind="savings",
            citation="Unthread 2025", tier="T2",
            detail="1,151 emp × 26 tickets × 42.5% × $13 cost Δ",
        )
    with row1[1]:
        render_tile(
            label="Onboarding Productivity Δ",
            value=onboarding, kind="savings",
            citation="Mewayz 2026 · 8.5 → 5.9 wks", tier="T2",
            detail="230 hires × 2.6 wks × weekly loaded",
        )
    with row1[2]:
        render_tile(
            label="Benefits Billing Recovery",
            value=benefits, kind="savings",
            citation="Beneration Nov 2025", tier="T2",
            detail="2.30 cohorts × $1M discrepancy × 20% recovery",
            calibrated=True,
        )

    row2 = st.columns(3)
    with row2[0]:
        render_tile(
            label=f"Candidate Pipeline Risk ({inputs.pipeline_scenario})",
            value=-pipeline_risk, kind="risk",
            citation="Greenhouse 2025 · SHRM 2025", tier="T1",
            detail="230 × 5 × dropout × $5,475 cost-per-hire",
            badge=inputs.pipeline_scenario.upper(),
        )
    with row2[1]:
        render_tile(
            label="Decision-Point Compliance Risk",
            value=-dp_risk, kind="risk",
            citation="T·T·D primitive", tier="T5",
            detail="230 × 4 dp · 1.5pp delta · $5K/error",
            calibrated=True,
            # Gate 11
            tail_risk_note=(
                "<em>Mobley v. Workday</em> (class certified May 2025; "
                "bench trial Jan 2026) · <em>Kistler v. Eightfold AI</em> — "
                "a substantiated bias-tail event could exceed this annual "
                "figure by 1–2 orders of magnitude."
            ),
        )
    with row2[2]:
        # 6th cell — portfolio tile (canvas-faithful, NOT full-width hero)
        render_portfolio_compact(
            net_value=portfolio.net_annual_value,
            gross=portfolio.gross_savings_after_verification_tax,
            risk=portfolio.risk_costs,
        )

    # A3 framing for tile 5 — placed below the grid to avoid making it taller
    # than the others (Streamlit columns equalize height by content).
    st.caption(
        "*Tile 5 framing.* AI raises the decision-point error rate from 3.0% "
        "to 4.5% — mirrors DORA's CFR-rises-with-AI finding from the "
        "engineering side. The ~$69K/yr is expected: it's the cost of "
        "running AI before the oversight layer is fully wired. **Day 90's "
        "deliverable wires that oversight layer.**"
    )

    st.markdown(
        '<hr style="margin: 24px 0; border: 0; border-top: 1px solid var(--rule);" />',
        unsafe_allow_html=True,
    )

    # ----- Break-even chart -----
    st.subheader("Break-Even Trajectory")
    try:
        break_even = cumulative_cost_vs_savings(inputs)
        fig = break_even_chart(break_even)
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Learning curve and steady-state durations are calibrated from "
            "engineering analogs (amber-flagged in Setup). Actual HR "
            "trajectory requires baseline measurement at the deployment "
            "org. Per Gate 6: this is a visualization of cumulative cost "
            "vs savings, NOT a parameter-driven prediction — no invented "
            "trough depth."
        )
    except ValueError as e:
        st.error(f"Break-even chart cannot render: {e}")
