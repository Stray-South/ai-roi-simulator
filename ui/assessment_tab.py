"""Assessment radar tab (Phase 10 / Option B).

Renders 7-capability radar with the user-centric focus axis painted red when
DL-13 gate triggers. Multiplier-derived dollar values are v3-pending; this
tab only displays the 1-5 scores themselves.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from roi_calc.engineering_engine import user_centric_gate_active
from roi_calc.models import EngineeringInputs


_CAPABILITY_FIELDS = (
    "clear_ai_stance",
    "healthy_data_ecosystem",
    "ai_accessible_data",
    "version_control",
    "small_batches",
    "user_centric_focus",
    "quality_platform",
)


def render() -> None:
    inputs: EngineeringInputs = st.session_state.get(
        "engineering_inputs", EngineeringInputs()
    )

    st.header("Engineering Mode — Assessment Radar")
    st.markdown(
        "7 DORA AI capabilities, scored 1–5. **user_centric_focus** is the "
        "DORA 2025 finding: scores ≤ 2 zero out AI value per DORA 2025's headline "
        "finding."
    )

    scores = [getattr(inputs, f) for f in _CAPABILITY_FIELDS]
    labels = [
        "Clear AI stance", "Healthy data ecosystem", "AI-accessible data",
        "Version control", "Small batches", "User-centric focus",
        "Quality platform",
    ]
    gate_active = user_centric_gate_active(inputs.user_centric_focus)

    # Paint user_centric_focus marker red when gate triggers, purple otherwise
    UCF_INDEX = 5  # _CAPABILITY_FIELDS.index("user_centric_focus")
    marker_colors = ["#907AFF"] * len(scores)
    if gate_active:
        marker_colors[UCF_INDEX] = "#EF4444"
    # Close the polygon — repeat first marker color at the end
    marker_colors_closed = marker_colors + [marker_colors[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=scores + [scores[0]],
            theta=labels + [labels[0]],
            fill="toself",
            line=dict(color="#907AFF", width=2),
            fillcolor="rgba(144, 122, 255, 0.20)",
            marker=dict(color=marker_colors_closed, size=10),
            name="Current",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False,
        height=480,
    )

    st.plotly_chart(fig, width="stretch")

    if gate_active:
        st.error(
            f"⚠️ user_centric_focus = {inputs.user_centric_focus} ≤ 2 — "
            "DORA 2025 gate ACTIVE. Per DORA 2025, AI adoption in this team "
            "produces NEGATIVE value until user-centric focus rises above 2. "
            "User-centric-focus marker is painted **red** on the radar above."
        )

    st.markdown("---")
    st.subheader(f"Archetype: *{inputs.archetype}*")
    st.info(
        "**v3-calibration pending** — the 7 DORA archetype multipliers "
        "(Foundational Challenges 0.4× through Harmonious High-Achievers 1.25×) "
        "are not yet on disk in v1. Default capability scores display on this "
        "radar; multiplier-derived dollar values do NOT display until v3 ships."
    )
