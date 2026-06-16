"""Sensitivity tab (Phase 8) — Plotly tornado consuming Phase 5 data.

Renders for both modes via the mode-router dispatcher.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st

from roi_calc.models import EngineeringInputs, PeopleInputs
from roi_calc.sensitivity import tornado_for_engineering, tornado_for_people
from ui.charts import tornado_chart
from ui.components import friendly_label


def render(mode: Literal["People", "Engineering"]) -> None:
    st.header(f"{mode} Mode — Sensitivity Tornado")
    st.markdown(
        "Each bar shows the swing in the portfolio's headline output when one "
        "input is varied ±20% (floats) or ±1 (1–5 scale ints). "
        "**Gray bars are orphan inputs** (decorative; calibrated at Day 90) — they're "
        "wired into the UI but have no engine effect in v1. Day-90 calibration "
        "with org-measured baselines is the deliverable that activates them."
    )

    if mode == "People":
        inputs: PeopleInputs = st.session_state.get("people_inputs", PeopleInputs())
        bars = tornado_for_people(inputs)
        title = "People Mode — Portfolio Net Annual Value (USD)"
    else:
        inputs_e: EngineeringInputs = st.session_state.get(
            "engineering_inputs", EngineeringInputs()
        )
        bars = tornado_for_engineering(inputs_e)
        title = "Engineering Mode — Instability Tax (USD)"

    # Apply friendly labels to the bars so the chart axis is readable
    relabeled = [
        type(b)(
            field_name=friendly_label(b.field_name),
            low_value_output=b.low_value_output,
            high_value_output=b.high_value_output,
            swing=b.swing,
            is_orphan=b.is_orphan,
        )
        for b in bars
    ]
    fig = tornado_chart(relabeled, title=title)
    st.plotly_chart(fig, width="stretch")

    st.caption(
        "Gray bars = orphan inputs (no engine effect in v1). "
        f"{sum(1 for b in bars if b.is_orphan)} orphan + "
        f"{sum(1 for b in bars if not b.is_orphan)} live bars rendered."
    )
