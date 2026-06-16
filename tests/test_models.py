"""Phase 2 tests — input/output dataclasses + cascade regressions.

Cascade regressions guarded here:
  * DL-7  — PortfolioResult / BreakEvenResult are frozen dataclasses
  * DL-17 — PeopleInputs has no ``discount_rate_annual`` field
  * DL-19 — pipeline_scenario default is "Conservative"
  * DL-23 — PeopleInputs defaults to the operating-subsidiary headcount, not consolidated
  * Gate 10 — PortfolioResult has no ``compensation_multiple`` field
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from typing import get_args

import pytest

from roi_calc.constants import (
    DECISION_POINT_ERROR_COST,
    DECISION_POINTS_PER_EVENT,
    DP_ERROR_RATE_BASELINE,
    DP_ERROR_RATE_WITH_AI,
    HORIZON_MONTHS,
    HR_MANAGER_LOADED_HOURLY,
    HR_SPECIALIST_LOADED_HOURLY,
    IT_SPECIALIST_LOADED_HOURLY,
    LEARNING_CURVE_MONTHS,
    ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
    ONBOARDING_TOUCHES_PER_EVENT_BASELINE,
    SAMPLE_ANNUAL_HIRES,
    SAMPLE_ORG_EMPLOYEES,
    SAMPLE_LOADED_COST_PER_FTE,
    TIME_PER_TOUCH_REDUCTION_PCT,
    TIME_TO_STEADY_STATE_MONTHS,
    TOUCHES_AUTOMATED_PCT,
)
from roi_calc.models import (
    BreakEvenResult,
    EngineeringInputs,
    PeopleInputs,
    PipelineScenario,
    PortfolioResult,
)


# ---------------------------------------------------------------------------
# PeopleInputs — structural + default values
# ---------------------------------------------------------------------------

def test_people_inputs_is_frozen() -> None:
    inp = PeopleInputs()
    with pytest.raises(FrozenInstanceError):
        inp.employees = 9999  # type: ignore[misc]


def test_people_inputs_sample_defaults_organization() -> None:
    """Sample defaults: the operating-subsidiary headcount drives the engine, not the consolidated headcount."""
    inp = PeopleInputs()
    assert inp.employees == 1_151
    assert inp.annual_hires == 230
    assert inp.fully_loaded_cost_per_fte == 124_615


def test_people_inputs_bls_hourly_rates() -> None:
    inp = PeopleInputs()
    assert inp.hr_specialist_loaded_hourly == 49.83
    assert inp.it_specialist_loaded_hourly == 40.62
    assert inp.manager_loaded_hourly == 100.30


def test_people_inputs_ttd_primitives() -> None:
    inp = PeopleInputs()
    assert inp.onboarding_touches_per_event_baseline == 12
    assert inp.onboarding_avg_minutes_per_touch_baseline == 18.0
    assert inp.decision_points_per_event_baseline == 4
    assert inp.decision_point_error_cost_avg == 5_000


def test_people_inputs_ai_automation() -> None:
    inp = PeopleInputs()
    assert inp.touches_automated_pct == 0.55
    assert inp.time_per_touch_reduction_pct == 0.40
    assert inp.decision_point_error_rate_baseline == 0.03
    assert inp.decision_point_error_rate_with_ai == 0.045


def test_people_inputs_jcurve_timing() -> None:
    inp = PeopleInputs()
    assert inp.learning_curve_months == 6
    assert inp.time_to_steady_state_months == 12
    assert inp.horizon_months == 24


def test_people_inputs_capability_multipliers_neutral_defaults() -> None:
    """Option D / DL-8 / DL-24: decorative wrappers, defaults are neutral."""
    inp = PeopleInputs()
    assert inp.training_spend_ppt == 1.0  # neutral
    assert inp.manager_support_score == 3  # spec scale midpoint (1-5)


def test_dl17_people_inputs_no_discount_rate_annual() -> None:
    """DL-17: orphan field removed for v1; spec §4.4 lists it but no §5/§6 fn uses it."""
    field_names = {f.name for f in fields(PeopleInputs)}
    assert "discount_rate_annual" not in field_names, (
        "discount_rate_annual must not be a PeopleInputs field per DL-17 — "
        "no §5/§6 function references it; v2 backlog."
    )


def test_dl19_people_inputs_pipeline_scenario_default_conservative() -> None:
    """DL-19: portfolio total hardcodes Conservative per spec §5.6;
    pipeline_scenario default matches so risk-tile loads consistently."""
    inp = PeopleInputs()
    assert inp.pipeline_scenario == "Conservative"


def test_people_inputs_defaults_sourced_from_constants() -> None:
    """Every PeopleInputs default must trace back to a constants.py Citation
    (or be a neutral capability-multiplier default per Option D).

    Cross-link audit — protects against Phase 1 / Phase 2 drifting silently.
    """
    inp = PeopleInputs()
    assert inp.employees == SAMPLE_ORG_EMPLOYEES.value
    assert inp.annual_hires == SAMPLE_ANNUAL_HIRES.value
    assert inp.fully_loaded_cost_per_fte == SAMPLE_LOADED_COST_PER_FTE.value
    assert inp.hr_specialist_loaded_hourly == HR_SPECIALIST_LOADED_HOURLY.value
    assert inp.it_specialist_loaded_hourly == IT_SPECIALIST_LOADED_HOURLY.value
    assert inp.manager_loaded_hourly == HR_MANAGER_LOADED_HOURLY.value
    assert inp.onboarding_touches_per_event_baseline == ONBOARDING_TOUCHES_PER_EVENT_BASELINE.value
    assert inp.onboarding_avg_minutes_per_touch_baseline == ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE.value
    assert inp.decision_points_per_event_baseline == DECISION_POINTS_PER_EVENT.value
    assert inp.decision_point_error_cost_avg == DECISION_POINT_ERROR_COST.value
    assert inp.touches_automated_pct == TOUCHES_AUTOMATED_PCT.value
    assert inp.time_per_touch_reduction_pct == TIME_PER_TOUCH_REDUCTION_PCT.value
    assert inp.decision_point_error_rate_baseline == DP_ERROR_RATE_BASELINE.value
    assert inp.decision_point_error_rate_with_ai == DP_ERROR_RATE_WITH_AI.value
    assert inp.learning_curve_months == LEARNING_CURVE_MONTHS.value
    assert inp.time_to_steady_state_months == TIME_TO_STEADY_STATE_MONTHS.value
    assert inp.horizon_months == HORIZON_MONTHS.value


def test_people_inputs_field_count() -> None:
    """Schema lock: 20 fields per spec §4.1-4.5 minus discount_rate_annual (DL-17)
    plus pipeline_scenario (DL-19).

    6 org + 4 T·T·D + 4 AI automation + 3 J-Curve + 2 capability + 1 scenario = 20.
    """
    assert len(fields(PeopleInputs)) == 20, (
        "PeopleInputs field count drift. Expected 20: 6 org + 4 T·T·D + 4 AI + "
        "3 J-Curve + 2 capability + 1 scenario. If you re-added "
        "`discount_rate_annual` you violated DL-17 (orphan field, v2 backlog)."
    )


def test_models_all_export_list() -> None:
    """``from roi_calc.models import *`` must NOT leak the 16 Citation names
    imported at module top. ``__all__`` whitelists exactly the 5 public types.
    Phase 6 UI may use wildcard imports — keep its namespace clean.
    """
    from roi_calc import models
    assert hasattr(models, "__all__")
    assert set(models.__all__) == {
        "PeopleInputs",
        "EngineeringInputs",
        "PortfolioResult",
        "BreakEvenResult",
        "PipelineScenario",
        "Archetype",  # added in Phase 4
    }


def test_pipeline_scenario_literal_values_and_order() -> None:
    """DL-19 + Phase 6 dependency: PipelineScenario must export the three values
    Conservative/Realistic/Aggressive in that exact order so the radio selector
    in Setup tab renders Conservative first (matches portfolio-hardcode default).
    """
    assert get_args(PipelineScenario) == ("Conservative", "Realistic", "Aggressive")


# ---------------------------------------------------------------------------
# EngineeringInputs — Phase 2 stub
# ---------------------------------------------------------------------------

def test_engineering_inputs_is_frozen() -> None:
    inp = EngineeringInputs()
    with pytest.raises(FrozenInstanceError):
        inp.cfr_before = 0.99  # type: ignore[misc]


def test_engineering_inputs_instantiates_with_stub_defaults() -> None:
    inp = EngineeringInputs()
    assert inp.engineers == 300
    assert inp.cfr_before == 0.05
    assert inp.cfr_after == 0.06


def test_engineering_inputs_cfr_delta_matches_dora_sample() -> None:
    """Phase 4 will compute instability tax = (cfr_after − cfr_before) × deploys × incident.
    Stub defaults must match DORA's sample CFR delta (0.06 − 0.05 = +0.01)."""
    inp = EngineeringInputs()
    assert inp.cfr_after - inp.cfr_before == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# PortfolioResult — DL-7 + Gate 10
# ---------------------------------------------------------------------------

def test_portfolio_result_is_frozen() -> None:
    r = PortfolioResult(gross_savings_after_verification_tax=0.0, risk_costs=0.0, net_annual_value=0.0)
    with pytest.raises(FrozenInstanceError):
        r.net_annual_value = 999.0  # type: ignore[misc]


def test_portfolio_result_fields() -> None:
    field_names = {f.name for f in fields(PortfolioResult)}
    assert field_names == {
        "gross_savings_after_verification_tax",
        "risk_costs",
        "net_annual_value",
    }


def test_gate10_portfolio_result_no_compensation_fields() -> None:
    """Gate 10: no $145K comparison anywhere in engine output. PortfolioResult
    must NOT have ANY field referencing compensation. Substring loop catches
    naming variants (compensation_multiple, comp_target, compensation_ratio, c145k).
    Mirror of `test_gate10_break_even_result_no_compensation_fields`.
    """
    field_names = {f.name for f in fields(PortfolioResult)}
    for name in field_names:
        lname = name.lower()
        assert "compensation" not in lname, f"Gate 10: PortfolioResult.{name} matches 'compensation'"
        assert "comp" not in lname, f"Gate 10: PortfolioResult.{name} contains 'comp' (any compensation-adjacent name)"
        assert "salary" not in lname, f"Gate 10: PortfolioResult.{name} contains 'salary'"
        assert "wage_target" not in lname, f"Gate 10: PortfolioResult.{name} contains 'wage_target'"
        assert "145" not in name, f"Gate 10: PortfolioResult.{name} contains '145' (comp target value)"


def test_portfolio_result_constructs_with_three_floats() -> None:
    r = PortfolioResult(
        gross_savings_after_verification_tax=1_297_053.0,
        risk_costs=824_550.0,
        net_annual_value=472_503.0,
    )
    assert r.gross_savings_after_verification_tax == 1_297_053.0
    assert r.risk_costs == 824_550.0
    assert r.net_annual_value == 472_503.0


# ---------------------------------------------------------------------------
# BreakEvenResult — DL-7
# ---------------------------------------------------------------------------

def test_break_even_result_is_frozen() -> None:
    r = BreakEvenResult()
    with pytest.raises(FrozenInstanceError):
        r.breakeven_month = 5  # type: ignore[misc]


def test_break_even_result_default_factory_is_empty_tuple() -> None:
    """Default for sequence fields is an empty tuple (immutable singleton in CPython —
    the ``is`` check below works because ``tuple()`` returns the same empty instance)."""
    a = BreakEvenResult()
    assert a.months == ()
    assert a.cumulative_cost == ()
    assert a.cumulative_savings == ()


def test_break_even_result_normalizes_list_input_to_tuple() -> None:
    """Phase 3 builds the series with lists in a loop (spec §6.1 reference impl).
    The constructor must normalize to tuple at __post_init__ so the returned
    BreakEvenResult is truly immutable regardless of how it was built.

    Without normalization, ``BreakEvenResult(months=[1,2,3], ...)`` would silently
    store a list (Python doesn't enforce type annotations) and ``.append`` would
    succeed — defeating the tuple-type contract.
    """
    r = BreakEvenResult(
        months=[1, 2, 3],  # type: ignore[arg-type]
        cumulative_cost=[1.0, 2.0, 3.0],  # type: ignore[arg-type]
        cumulative_savings=[0.1, 0.2, 0.3],  # type: ignore[arg-type]
        breakeven_month=2,
    )
    assert isinstance(r.months, tuple)
    assert isinstance(r.cumulative_cost, tuple)
    assert isinstance(r.cumulative_savings, tuple)
    assert r.months == (1, 2, 3)
    assert r.cumulative_cost == (1.0, 2.0, 3.0)
    assert r.cumulative_savings == (0.1, 0.2, 0.3)


def test_break_even_result_sequence_fields_are_truly_immutable() -> None:
    """``frozen=True`` alone only blocks attribute reassignment, NOT in-place
    mutation of mutable containers. Sequence fields are ``tuple`` so any
    ``.append()`` / ``[i] = x`` / ``+=`` attempt raises ``AttributeError`` or
    ``TypeError`` — protecting Phase 3 → Phase 7 from chart code accidentally
    corrupting a BreakEvenResult snapshot it received from the engine."""
    r = BreakEvenResult(months=(1, 2, 3), cumulative_cost=(1.0, 2.0, 3.0),
                       cumulative_savings=(0.1, 0.2, 0.3), breakeven_month=2)
    with pytest.raises(AttributeError):
        r.months.append(99)  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        r.cumulative_cost[0] = 99.0  # type: ignore[index]
    with pytest.raises(TypeError):
        r.cumulative_savings[0] = 99.0  # type: ignore[index]


def test_break_even_result_fields() -> None:
    field_names = {f.name for f in fields(BreakEvenResult)}
    assert field_names == {
        "months",
        "cumulative_cost",
        "cumulative_savings",
        "breakeven_month",
    }


def test_break_even_result_breakeven_month_accepts_none() -> None:
    """Spec §6.1: ``cumulative_cost_vs_savings`` returns ``None`` when savings
    never cross cost within ``horizon_months``."""
    r = BreakEvenResult(months=(1, 2, 3), cumulative_cost=(1.0, 2.0, 3.0),
                       cumulative_savings=(0.1, 0.2, 0.3), breakeven_month=None)
    assert r.breakeven_month is None


def test_break_even_result_breakeven_month_accepts_int() -> None:
    r = BreakEvenResult(months=(1, 2, 3), cumulative_cost=(1.0, 2.0, 3.0),
                       cumulative_savings=(5.0, 6.0, 7.0), breakeven_month=1)
    assert r.breakeven_month == 1


def test_gate10_break_even_result_no_compensation_fields() -> None:
    """Gate 10 mirror: BreakEvenResult must not have any compensation-related field.
    Same substring loop as the PortfolioResult guard (true symmetry)."""
    field_names = {f.name for f in fields(BreakEvenResult)}
    for name in field_names:
        lname = name.lower()
        assert "compensation" not in lname, f"Gate 10: BreakEvenResult.{name} matches 'compensation'"
        assert "comp" not in lname, f"Gate 10: BreakEvenResult.{name} contains 'comp' (any compensation-adjacent name)"
        assert "salary" not in lname, f"Gate 10: BreakEvenResult.{name} contains 'salary'"
        assert "wage_target" not in lname, f"Gate 10: BreakEvenResult.{name} contains 'wage_target'"
        assert "145" not in name, f"Gate 10: BreakEvenResult.{name} contains '145' (comp target value)"
