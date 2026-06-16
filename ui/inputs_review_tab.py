"""Inputs Review tab (Phase 11) — mode-aware read-only summary.

Per spec §8.2 row 6 / §8.3 row 4: every input field rendered as a table with
friendly label / current value / tier / citation. T5 rows are amber-highlighted.

Field-to-citation mapping is the explicit dict per Sprint 4 R11.1 — no
string-matching, no decorators.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Literal

import pandas as pd
import streamlit as st

from roi_calc.constants import (
    BENEFITS_RECOVERY_PCT,
    CFR_AFTER_DORA_SAMPLE,
    CFR_BEFORE_DORA_SAMPLE,
    Citation,
    DECISION_POINT_ERROR_COST,
    DECISION_POINTS_PER_EVENT,
    DEPLOYS_PER_YEAR_DORA,
    DP_ERROR_RATE_BASELINE,
    DP_ERROR_RATE_WITH_AI,
    ENGINEERS_BENCHMARK,
    HORIZON_MONTHS,
    HR_MANAGER_LOADED_HOURLY,
    HR_SPECIALIST_LOADED_HOURLY,
    INCIDENT_COST_DORA,
    IT_SPECIALIST_LOADED_HOURLY,
    LEARNING_CURVE_MONTHS,
    METR_SELF_REPORT_DISCOUNT,
    ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
    ONBOARDING_TOUCHES_PER_EVENT_BASELINE,
    SAMPLE_ANNUAL_HIRES,
    SAMPLE_ORG_EMPLOYEES,
    SAMPLE_LOADED_COST_PER_FTE,
    TIME_PER_TOUCH_REDUCTION_PCT,
    TIME_TO_STEADY_STATE_MONTHS,
    TOUCHES_AUTOMATED_PCT,
    TRAINING_SPEND_PPT_DECORATIVE,
)
from roi_calc.models import EngineeringInputs, PeopleInputs
from ui.components import friendly_label


# Explicit field → Citation mapping (Sprint 4 R11.1: no string-matching).
FIELD_TO_CITATION: dict[str, Citation] = {
    # People organization
    "employees": SAMPLE_ORG_EMPLOYEES,
    "annual_hires": SAMPLE_ANNUAL_HIRES,
    "fully_loaded_cost_per_fte": SAMPLE_LOADED_COST_PER_FTE,
    "hr_specialist_loaded_hourly": HR_SPECIALIST_LOADED_HOURLY,
    "it_specialist_loaded_hourly": IT_SPECIALIST_LOADED_HOURLY,
    "manager_loaded_hourly": HR_MANAGER_LOADED_HOURLY,
    # T·T·D primitives
    "onboarding_touches_per_event_baseline": ONBOARDING_TOUCHES_PER_EVENT_BASELINE,
    "onboarding_avg_minutes_per_touch_baseline": ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
    "decision_points_per_event_baseline": DECISION_POINTS_PER_EVENT,
    "decision_point_error_cost_avg": DECISION_POINT_ERROR_COST,
    # AI automation
    "touches_automated_pct": TOUCHES_AUTOMATED_PCT,
    "time_per_touch_reduction_pct": TIME_PER_TOUCH_REDUCTION_PCT,
    "decision_point_error_rate_baseline": DP_ERROR_RATE_BASELINE,
    "decision_point_error_rate_with_ai": DP_ERROR_RATE_WITH_AI,
    # J-Curve timing
    "learning_curve_months": LEARNING_CURVE_MONTHS,
    "time_to_steady_state_months": TIME_TO_STEADY_STATE_MONTHS,
    "horizon_months": HORIZON_MONTHS,
    # Capability multipliers (decorative under Option D)
    "training_spend_ppt": TRAINING_SPEND_PPT_DECORATIVE,
    # Engineering Mode
    "engineers": ENGINEERS_BENCHMARK,
    "cfr_before": CFR_BEFORE_DORA_SAMPLE,
    "cfr_after": CFR_AFTER_DORA_SAMPLE,
    "deploys_per_year": DEPLOYS_PER_YEAR_DORA,
    "incident_cost": INCIDENT_COST_DORA,
    "self_report_discount": METR_SELF_REPORT_DISCOUNT,
    # Benefits decorative
    # (BENEFITS_RECOVERY_PCT is engine-internal, not user-editable)
    # archetype + 7 capability scores are user-editable Option B / DL-14 fields
    # with no Citation backing — they render as "(user-editable / decorative)".
}


def render(mode: Literal["People", "Engineering"]) -> None:
    st.header(f"{mode} Mode — Inputs Review")
    st.markdown(
        "Read-only summary of every input field with its citation, tier, "
        "and amber flag (if T5). Phase 9 Confidence Audit drills into every "
        "Citation in `constants.py`; this tab maps each input field to its source."
    )

    if mode == "People":
        inputs = st.session_state.get("people_inputs", PeopleInputs())
    else:
        inputs = st.session_state.get("engineering_inputs", EngineeringInputs())

    rows = []
    for f in fields(inputs):
        citation = FIELD_TO_CITATION.get(f.name)
        # Cast Value to str — PyArrow can't infer a column type when ints,
        # floats, and strings (pipeline_scenario, archetype) coexist. The audit
        # tab is display-only so str-cast is safe and stops the
        # "Serialization of dataframe to Arrow table was unsuccessful" log spam.
        raw_value = getattr(inputs, f.name)
        if isinstance(raw_value, float):
            display_value = f"{raw_value:,.4g}" if raw_value < 1 else f"{raw_value:,.2f}"
        elif isinstance(raw_value, int):
            display_value = f"{raw_value:,}"
        else:
            display_value = str(raw_value)
        rows.append({
            "Field": friendly_label(f.name),
            "Value": display_value,
            "Tier": citation.tier if citation else "—",
            "Source": citation.source if citation else "(user-editable / decorative)",
            "Flag": (citation.flag if citation else "") or "",
        })
    df = pd.DataFrame(rows)
    # DL-12 + spec §8.4 "no exceptions": T5 rows render with amber background
    styled = df.style.apply(
        lambda row: [
            "background-color: #FFF7ED; color: #92400E;"
            if row["Tier"] == "T5"
            else ""
            for _ in row
        ],
        axis=1,
    )
    st.dataframe(styled, width="stretch", hide_index=True)
