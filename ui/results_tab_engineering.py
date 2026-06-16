"""Engineering Mode Results tab (Phase 10 / Option B per DL-14).

Real numbers:
  * Instability tax (reproduces DORA $344K)
  * J-Curve chart at default ramp shape

V3-pending annotations (NOT dollar values):
  * Archetype-adjusted portfolio
  * Capability-adjusted portfolio
"""

from __future__ import annotations

import streamlit as st

from roi_calc.engineering_engine import (
    engineering_annual_value,
    engineering_cumulative_cost_vs_savings,
    engineering_portfolio,
)
from roi_calc.models import EngineeringInputs
from ui.charts import break_even_chart


def render() -> None:
    inputs: EngineeringInputs = st.session_state.get(
        "engineering_inputs", EngineeringInputs()
    )

    st.markdown(
        '<div class="eyebrow">02 · Results · Engineering Mode</div>',
        unsafe_allow_html=True,
    )
    st.header("DORA J-Curve · Engineering data")
    st.markdown(
        """
<div class="reader-anchor">
  <p><strong>What this tab is.</strong>
  The same engine and chart as People Mode, running on engineering data
  instead of HR data. The <em>$344K instability tax</em> tile below
  reproduces DORA's published calculator output exactly with default
  inputs.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    result = engineering_portfolio(inputs)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Instability Tax (annual)",
            value=f"${result.instability_tax_annual:,.0f}",
            help=(
                "DORA 2026: (cfr_after − cfr_before) × deploys × incident_cost. "
                "Terminology note: DORA's own publications use 'verification tax' "
                "for this construct; 'instability tax' is third-party / industry "
                "shorthand for the same number — we use the more common label "
                "but credit DORA's terminology."
            ),
        )
        st.caption(
            "Real number — reproduces DORA's $344K with default inputs. "
            "DORA labels this construct **verification tax** in their own materials; "
            "'instability tax' is the third-party term used here for industry "
            "familiarity. Same $344K, same math."
        )

    with col2:
        if result.user_centric_gate_triggered:
            st.error(
                "⚠️ **User-centric focus gate triggered** "
                f"(score = {inputs.user_centric_focus} ≤ 2). "
                "DORA 2025 finding: AI adoption produces NEGATIVE value here. "
                "Address user-centric focus before scaling AI."
            )
        else:
            st.success(
                f"User-centric focus score = {inputs.user_centric_focus} > 2. "
                "User-centric focus above threshold; AI value flows through."
            )

    st.markdown("---")

    st.subheader("Archetype-adjusted portfolio")
    st.info(
        f"📍 **{result.archetype_adjusted_status}** — *deliberate Day-90 "
        f"deliverable, not a half-built feature.*\n\n"
        f"Selected archetype: *{inputs.archetype}*. The 7 DORA archetype "
        "multipliers (Foundational Challenges → Harmonious High-Achievers) "
        "calibrate against your organization's measured baselines at Day 90 "
        "of an engagement. This template ships the structural API; the "
        "calibration math is the deliverable a real engagement produces."
    )

    st.subheader("Capability-adjusted portfolio")
    st.info(
        f"📍 **{result.capability_adjusted_status}** — *deliberate Day-90 "
        f"deliverable, not a half-built feature.*\n\n"
        "The 7 DORA capability weights calibrate at Day 90 against your "
        "organization's measured baselines. Default 1-5 scores display on "
        "the Assessment radar tab; multiplier-derived dollar values do NOT "
        "display until calibration is complete — surfacing un-calibrated "
        "numbers would be dishonest."
    )

    st.markdown("---")
    st.subheader("Engineering Mode J-Curve")
    try:
        annual_net = engineering_annual_value(inputs)
        st.metric(
            label="Engineering annual net value",
            value=f"${annual_net:,.0f}",
            help=(
                "adopting_engineers × hours_saved/yr × hourly_cost "
                "− instability tax (DORA $344K)"
            ),
        )
        break_even = engineering_cumulative_cost_vs_savings(inputs)
        fig = break_even_chart(break_even)
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Real Engineering Mode J-Curve per DORA 2026 ROI Report + METR 2025 "
            "RCT discount. Productivity gain × adopting engineers × FTE hourly "
            "cost, net of DORA verification tax (0.15) and instability tax "
            "($344K reproduction). $344K reproduces DORA's calculator output "
            "under their default assumptions as the Engineering-Mode "
            "credibility check; the real figure comes from your organization's own incident "
            "data — that's the Day-90 deliverable. Archetype + capability "
            "multipliers fixed to 1.0× (decorative in this template — Day-90 calibration "
            "with org-measured baselines replaces."
        )
    except ValueError as e:
        st.error(f"J-Curve cannot render: {e}")

    st.markdown("---")
    st.caption(
        "This is the credibility-check half of the dual-mode pitch — same scaffolding, "
        "different data. Day-90 deliverable: ingest v3 archetype + capability "
        "multipliers, then swap these v3-pending annotations for real dollar tiles."
    )
