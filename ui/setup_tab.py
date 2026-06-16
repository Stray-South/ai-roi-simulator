"""Setup tab — input widgets bound to PeopleInputs / EngineeringInputs (Phase 6).

Spec §8.6: order of widgets is mode selector → workflow selector → org →
T·T·D → capability multipliers → J-Curve timing → Calculate button.

T5 inputs render with the amber-flag widget treatment (DL-12 / Cascade 8 sibling).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

import streamlit as st

from roi_calc.constants import (
    BENEFITS_RECOVERY_PCT,
    DECISION_POINT_ERROR_COST,
    DECISION_POINTS_PER_EVENT,
    DEPLOYS_PER_YEAR_DORA,
    DP_ERROR_RATE_BASELINE,
    DP_ERROR_RATE_WITH_AI,
    HORIZON_MONTHS,
    HR_MANAGER_LOADED_HOURLY,
    HR_SPECIALIST_LOADED_HOURLY,
    INCIDENT_COST_DORA,
    IT_SPECIALIST_LOADED_HOURLY,
    LEARNING_CURVE_MONTHS,
    METR_SELF_REPORT_DISCOUNT,
    ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
    ONBOARDING_TOUCHES_PER_EVENT_BASELINE,
    PIPELINE_PER_REQ,
    SAMPLE_ANNUAL_HIRES,
    SAMPLE_ORG_EMPLOYEES,
    SAMPLE_LOADED_COST_PER_FTE,
    TIME_PER_TOUCH_REDUCTION_PCT,
    TIME_TO_STEADY_STATE_MONTHS,
    TOUCHES_AUTOMATED_PCT,
    TRAINING_SPEND_PPT_DECORATIVE,
)
from roi_calc.models import EngineeringInputs, PeopleInputs
from roi_calc.people_engine import (
    cumulative_cost_vs_savings,
    people_mode_portfolio,
)
from ui.components import amber_flag_widget, friendly_label


Mode = Literal["People", "Engineering"]


def render(mode: Mode) -> None:
    """Render the Setup tab for the given mode."""
    st.header(f"{mode} Mode — Setup")
    if mode == "People":
        _render_people_setup()
    else:
        _render_engineering_setup()
    _render_calculate_button(mode)


def _render_people_setup() -> None:
    inputs: PeopleInputs = st.session_state["people_inputs"]

    st.markdown(
        "Workflow: **Infrastructure Onboarding** — the v1 golden path. "
        "Other workflows (FCRA dispute, benefits enrollment, offboarding, "
        "knowledge management, manager Q&A, comp band approval) are v2 — "
        "same scaffolding applies."
    )

    with st.expander("Organization (sample defaults)", expanded=True):
        employees = amber_flag_widget(
            friendly_label("employees"),
            SAMPLE_ORG_EMPLOYEES,
            st.number_input,
            min_value=0,
            value=int(inputs.employees),
            step=10,
            key="people_employees",
        )
        annual_hires = amber_flag_widget(
            friendly_label("annual_hires"),
            SAMPLE_ANNUAL_HIRES,
            st.number_input,
            min_value=0,
            value=int(inputs.annual_hires),
            step=5,
            key="people_annual_hires",
        )
        fully_loaded = amber_flag_widget(
            friendly_label("fully_loaded_cost_per_fte"),
            SAMPLE_LOADED_COST_PER_FTE,
            st.number_input,
            min_value=0,
            value=int(inputs.fully_loaded_cost_per_fte),
            step=1000,
            key="people_loaded_cost",
        )

    with st.expander("T·T·D primitives (T5 amber — calibrated)", expanded=True):
        ttd_touches = amber_flag_widget(
            friendly_label("onboarding_touches_per_event_baseline"),
            ONBOARDING_TOUCHES_PER_EVENT_BASELINE,
            st.number_input,
            min_value=1,
            value=int(inputs.onboarding_touches_per_event_baseline),
            step=1,
            key="people_ttd_touches",
        )
        ttd_minutes = amber_flag_widget(
            friendly_label("onboarding_avg_minutes_per_touch_baseline"),
            ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
            st.number_input,
            min_value=0.0,
            value=float(inputs.onboarding_avg_minutes_per_touch_baseline),
            step=1.0,
            key="people_ttd_minutes",
        )
        dp_per_event = amber_flag_widget(
            friendly_label("decision_points_per_event_baseline"),
            DECISION_POINTS_PER_EVENT,
            st.number_input,
            min_value=1,
            value=int(inputs.decision_points_per_event_baseline),
            step=1,
            key="people_dp_per_event",
        )
        dp_error_cost = amber_flag_widget(
            friendly_label("decision_point_error_cost_avg"),
            DECISION_POINT_ERROR_COST,
            st.number_input,
            min_value=0,
            value=int(inputs.decision_point_error_cost_avg),
            step=500,
            key="people_dp_error_cost",
        )

    with st.expander("Capability multipliers (decorative under Option D)", expanded=True):
        st.caption(
            "These sliders are shown for context; they have no effect on the "
            "headline numbers yet. Day 90 of the implementation plan calibrates "
            "them against your organization's own data."
        )
        training_spend = amber_flag_widget(
            friendly_label("training_spend_ppt"),
            TRAINING_SPEND_PPT_DECORATIVE,
            st.slider,
            min_value=0.0,
            max_value=5.0,
            value=float(inputs.training_spend_ppt),
            step=0.1,
            key="people_training_spend",
        )
        manager_support = st.slider(
            friendly_label("manager_support_score"),
            min_value=1,
            max_value=5,
            value=int(inputs.manager_support_score),
            step=1,
            key="people_manager_support",
        )

    with st.expander("J-Curve timing (T5 amber — engineering analog)", expanded=True):
        st.caption(
            "These shape the break-even chart's curve. No HR-specific public "
            "data exists, so the defaults come from the engineering-side "
            "equivalent (DORA). Day 90 replaces them with org-measured values."
        )
        learning_curve = amber_flag_widget(
            friendly_label("learning_curve_months"),
            LEARNING_CURVE_MONTHS,
            st.number_input,
            min_value=1, max_value=24,
            value=int(inputs.learning_curve_months),
            step=1,
            key="people_learning_curve",
        )
        steady_state = amber_flag_widget(
            friendly_label("time_to_steady_state_months"),
            TIME_TO_STEADY_STATE_MONTHS,
            st.number_input,
            min_value=int(learning_curve), max_value=36,
            value=int(inputs.time_to_steady_state_months),
            step=1,
            key="people_steady_state",
        )
        horizon = amber_flag_widget(
            friendly_label("horizon_months"),
            HORIZON_MONTHS,
            st.number_input,
            min_value=int(steady_state), max_value=60,
            value=int(inputs.horizon_months),
            step=1,
            key="people_horizon",
        )

    with st.expander("Pipeline scenario (drives risk-tile + tornado only)", expanded=True):
        st.caption(
            "The portfolio total uses the Conservative scenario. This toggle "
            "changes only the pipeline-risk tile and the tornado chart — not "
            "the headline number."
        )
        pipeline_scenario = st.radio(
            friendly_label("pipeline_scenario"),
            options=("Conservative", "Realistic", "Aggressive"),
            index=("Conservative", "Realistic", "Aggressive").index(inputs.pipeline_scenario),
            key="people_pipeline_scenario",
        )

    # Persist updated inputs to session state
    st.session_state["people_inputs"] = replace(
        inputs,
        employees=int(employees),
        annual_hires=int(annual_hires),
        fully_loaded_cost_per_fte=float(fully_loaded),
        onboarding_touches_per_event_baseline=int(ttd_touches),
        onboarding_avg_minutes_per_touch_baseline=float(ttd_minutes),
        decision_points_per_event_baseline=int(dp_per_event),
        decision_point_error_cost_avg=float(dp_error_cost),
        learning_curve_months=int(learning_curve),
        time_to_steady_state_months=int(steady_state),
        horizon_months=int(horizon),
        training_spend_ppt=float(training_spend),
        manager_support_score=int(manager_support),
        pipeline_scenario=pipeline_scenario,
    )


def _render_engineering_setup() -> None:
    inputs: EngineeringInputs = st.session_state["engineering_inputs"]

    st.markdown(
        "DORA framework — instability tax + J-Curve. **Option B (DL-14):** "
        "instability tax + J-Curve render real values; archetype and capability "
        "multiplier-derived dollar values render as *v3-calibration pending* "
        "annotations until v3 spec is on disk."
    )

    with st.expander("DORA J-Curve + instability tax", expanded=True):
        engineers = st.number_input(
            "Engineering headcount (calibrated benchmark)",
            min_value=0,
            value=int(inputs.engineers),
            step=10,
            key="eng_engineers",
            help="T5 calibrated — most regulated lenders don't disclose engineering headcount; industry peer scaling gives 230-345 band.",
        )
        cfr_before = st.number_input(
            "CFR before AI",
            min_value=0.0, max_value=1.0,
            value=float(inputs.cfr_before),
            step=0.01,
            key="eng_cfr_before",
            help="T2 — DORA 2026 ROI Report sample baseline.",
        )
        cfr_after = st.number_input(
            "CFR after AI",
            min_value=0.0, max_value=1.0,
            value=float(inputs.cfr_after),
            step=0.01,
            key="eng_cfr_after",
            help="T2 — DORA 2026 sample post-AI value.",
        )
        deploys = amber_flag_widget(
            friendly_label("deploys_per_year"),
            DEPLOYS_PER_YEAR_DORA,
            st.number_input,
            min_value=0,
            value=int(inputs.deploys_per_year),
            step=10,
            key="eng_deploys",
        )
        incident_cost = amber_flag_widget(
            friendly_label("incident_cost"),
            INCIDENT_COST_DORA,
            st.number_input,
            min_value=0,
            value=int(inputs.incident_cost),
            step=5000,
            key="eng_incident_cost",
        )
        self_report_discount = amber_flag_widget(
            friendly_label("self_report_discount"),
            METR_SELF_REPORT_DISCOUNT,
            st.slider,
            min_value=0.0, max_value=1.0,
            value=float(inputs.self_report_discount),
            step=0.05,
            key="eng_self_report",
        )

    with st.expander("7 DORA capability scores (1–5; decorative under Option B)", expanded=True):
        st.caption("Multipliers v3-pending; sliders display but don't drive dollar output in v1.")
        clear_ai = st.slider("Clear AI stance", 1, 5, int(inputs.clear_ai_stance), key="eng_clear_ai")
        healthy_data = st.slider("Healthy data ecosystem", 1, 5, int(inputs.healthy_data_ecosystem), key="eng_healthy_data")
        ai_data = st.slider("AI-accessible data", 1, 5, int(inputs.ai_accessible_data), key="eng_ai_data")
        version = st.slider("Version control", 1, 5, int(inputs.version_control), key="eng_version")
        batches = st.slider("Small batches", 1, 5, int(inputs.small_batches), key="eng_batches")
        ucf = st.slider("User-centric focus (≤2 triggers DL-13 gate)", 1, 5, int(inputs.user_centric_focus), key="eng_ucf")
        quality = st.slider("Quality platform", 1, 5, int(inputs.quality_platform), key="eng_quality")

    archetype_options = (
        "Foundational Challenges", "Legacy Bottleneck", "Constrained by Process",
        "High Impact Low Cadence", "Stable and Methodical", "Pragmatic Performers",
        "Harmonious High-Achievers",
    )
    archetype = st.selectbox(
        "DORA archetype",
        options=archetype_options,
        index=archetype_options.index(inputs.archetype),
        key="eng_archetype",
    )

    st.session_state["engineering_inputs"] = replace(
        inputs,
        engineers=int(engineers),
        cfr_before=float(cfr_before),
        cfr_after=float(cfr_after),
        deploys_per_year=int(deploys),
        incident_cost=float(incident_cost),
        self_report_discount=float(self_report_discount),
        clear_ai_stance=int(clear_ai),
        healthy_data_ecosystem=int(healthy_data),
        ai_accessible_data=int(ai_data),
        version_control=int(version),
        small_batches=int(batches),
        user_centric_focus=int(ucf),
        quality_platform=int(quality),
        archetype=archetype,  # type: ignore[arg-type]
    )


def _render_calculate_button(mode: Mode) -> None:
    if st.button("Calculate", type="primary", key=f"{mode.lower()}_calculate"):
        try:
            if mode == "People":
                inputs = st.session_state["people_inputs"]
                st.session_state["people_portfolio"] = people_mode_portfolio(inputs)
                try:
                    st.session_state["people_breakeven"] = cumulative_cost_vs_savings(inputs)
                except ValueError as e:
                    st.error(f"Break-even chart: {e}")
                    st.session_state["people_breakeven"] = None
            else:
                from roi_calc.engineering_engine import engineering_portfolio
                inputs = st.session_state["engineering_inputs"]
                st.session_state["engineering_portfolio"] = engineering_portfolio(inputs)
            st.success(f"{mode} Mode results computed. Switch to Results tab.")
        except Exception as e:
            # Live-demo safety: catch any unhandled exception so the audience
            # sees a graceful error message instead of a Streamlit traceback.
            st.error(f"Calculation failed: {type(e).__name__}: {e}")
