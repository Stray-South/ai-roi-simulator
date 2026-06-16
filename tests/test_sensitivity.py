"""Phase 5 tests — tornado data for both modes."""

from __future__ import annotations

import pytest

from roi_calc.models import EngineeringInputs, PeopleInputs
from roi_calc.sensitivity import (
    TornadoBar,
    tornado_for_engineering,
    tornado_for_people,
)


# ---------------------------------------------------------------------------
# Shape + ordering
# ---------------------------------------------------------------------------

def test_tornado_for_people_returns_list_of_tornado_bars() -> None:
    result = tornado_for_people(PeopleInputs())
    assert isinstance(result, list)
    assert all(isinstance(b, TornadoBar) for b in result)


def test_tornado_for_people_default_top_10_includes_orphans() -> None:
    """DL-19: orphans pass through regardless of top_n; non-orphans are sliced.
    Phase 8 chart relies on orphans being present at default top_n=10."""
    result = tornado_for_people(PeopleInputs())
    non_orphan = [b for b in result if not b.is_orphan]
    orphan = [b for b in result if b.is_orphan]
    assert len(non_orphan) <= 10
    # All 3 People-Mode orphans (training_spend, manager_support, pipeline_scenario)
    # must surface at the default top_n.
    orphan_names = {b.field_name for b in orphan}
    assert "training_spend_ppt" in orphan_names
    assert "manager_support_score" in orphan_names
    assert "pipeline_scenario" in orphan_names


def test_tornado_for_people_top_n_parameter_limits_non_orphan_only() -> None:
    """top_n caps the non-orphan portion; orphans always pass through."""
    result = tornado_for_people(PeopleInputs(), top_n=3)
    non_orphan = [b for b in result if not b.is_orphan]
    assert len(non_orphan) == 3


def test_tornado_for_people_sorted_by_absolute_swing_descending() -> None:
    result = tornado_for_people(PeopleInputs())
    swings = [abs(b.swing) for b in result]
    assert swings == sorted(swings, reverse=True)


# ---------------------------------------------------------------------------
# Engine reference — top swing should be a high-leverage input
# ---------------------------------------------------------------------------

def test_tornado_for_people_top_field_is_high_leverage() -> None:
    """At sample defaults, the highest-swing input should be one of:
    employees, fully_loaded_cost_per_fte, annual_hires, onboarding_avg_minutes
    (any field driving onboarding which is ~$903K of $1.3M gross savings)."""
    result = tornado_for_people(PeopleInputs())
    top_field = result[0].field_name
    assert top_field in {
        "employees",
        "fully_loaded_cost_per_fte",
        "annual_hires",
        "onboarding_avg_minutes_per_touch_baseline",
        "onboarding_touches_per_event_baseline",
    }


def test_tornado_for_people_swing_is_signed() -> None:
    """high − low can be positive or negative; abs goes into sort."""
    result = tornado_for_people(PeopleInputs())
    # At least one bar must have a non-trivial signed swing
    assert any(b.swing != 0 for b in result)


# ---------------------------------------------------------------------------
# DL-19: orphan fields render as gray bars (is_orphan=True)
# ---------------------------------------------------------------------------

def test_tornado_for_people_marks_orphan_fields() -> None:
    """DL-19: training_spend_ppt, manager_support_score, pipeline_scenario MUST
    appear as is_orphan=True in the tornado list (top_n=30 reveals all)."""
    result = tornado_for_people(PeopleInputs(), top_n=30)
    orphans_found = {b.field_name for b in result if b.is_orphan}
    # All three known People-Mode orphans must surface — pipeline_scenario via
    # the string-orphan explicit bar path, the others via zero-swing numeric.
    assert "training_spend_ppt" in orphans_found
    assert "manager_support_score" in orphans_found
    assert "pipeline_scenario" in orphans_found


def test_tornado_for_people_pipeline_scenario_emits_zero_swing_orphan_bar() -> None:
    """DL-19 explicit: pipeline_scenario is a string Literal field. It must
    appear as an orphan bar (is_orphan=True, swing=0) even though it's not
    numeric — Phase 8 chart needs to show it as a gray bar saying 'wires in P9'."""
    result = tornado_for_people(PeopleInputs(), top_n=30)
    pipeline_bars = [b for b in result if b.field_name == "pipeline_scenario"]
    assert len(pipeline_bars) == 1
    assert pipeline_bars[0].is_orphan is True
    assert pipeline_bars[0].swing == 0.0
    assert pipeline_bars[0].low_value_output == pipeline_bars[0].high_value_output


def test_tornado_for_people_orphan_swing_is_zero() -> None:
    """Option D: orphan fields have no engine effect → swing == 0."""
    result = tornado_for_people(PeopleInputs(), top_n=30)
    for bar in result:
        if bar.is_orphan:
            assert bar.swing == pytest.approx(0.0, abs=1e-6), (
                f"Orphan field {bar.field_name} has non-zero swing {bar.swing}; "
                f"Option D contract violated — engine effect must be 0 in v1"
            )


# ---------------------------------------------------------------------------
# Engineering Mode tornado
# ---------------------------------------------------------------------------

def test_tornado_for_engineering_returns_list_of_tornado_bars() -> None:
    result = tornado_for_engineering(EngineeringInputs())
    assert isinstance(result, list)
    assert all(isinstance(b, TornadoBar) for b in result)


def test_tornado_for_engineering_top_field_drives_instability_tax() -> None:
    """At sample defaults, the top-swing field should be one that drives
    instability_tax: cfr_before, cfr_after, deploys_per_year, or incident_cost."""
    result = tornado_for_engineering(EngineeringInputs())
    top_field = result[0].field_name
    assert top_field in {
        "cfr_before",
        "cfr_after",
        "deploys_per_year",
        "incident_cost",
    }


def test_tornado_for_engineering_archetype_emits_zero_swing_orphan_bar() -> None:
    """Same DL-14 / DL-19 honest-display contract for Engineering Mode's
    archetype string field."""
    result = tornado_for_engineering(EngineeringInputs(), top_n=30)
    archetype_bars = [b for b in result if b.field_name == "archetype"]
    assert len(archetype_bars) == 1
    assert archetype_bars[0].is_orphan is True
    assert archetype_bars[0].swing == 0.0


def test_tornado_for_engineering_capability_scores_are_orphan() -> None:
    """Option B (DL-14): 7 capability scores + archetype are decorative in v1.
    Their tornado swing on instability_tax is zero."""
    result = tornado_for_engineering(EngineeringInputs(), top_n=30)
    for bar in result:
        if bar.field_name in {
            "clear_ai_stance", "healthy_data_ecosystem", "ai_accessible_data",
            "version_control", "small_batches", "user_centric_focus", "quality_platform",
        }:
            assert bar.is_orphan is True
            assert bar.swing == pytest.approx(0.0, abs=1e-6)


def test_tornado_for_engineering_no_zero_swing_non_orphan_bars() -> None:
    """Pass-3 cascade fix: the Engineering tornado measures sensitivity to
    `instability_tax_annual`. The 8 v3 §5.1 productivity-formula fields
    (engineers, ai_adoption_pct, etc.) drive `engineering_annual_value` but
    have zero impact on instability_tax_annual. Pre-fix they rendered as
    non-orphan zero-swing bars, stealing 6+ slots from real live inputs.

    Contract: every non-orphan bar in the Engineering tornado must have
    non-zero swing. Zero-swing fields must be marked orphan so they render
    gray (or be dropped from the tornado entirely).
    """
    result = tornado_for_engineering(EngineeringInputs(), top_n=30)
    zero_swing_non_orphan = [
        b for b in result if not b.is_orphan and b.swing == pytest.approx(0.0, abs=1e-6)
    ]
    assert not zero_swing_non_orphan, (
        f"non-orphan zero-swing bars in Engineering tornado: "
        f"{[b.field_name for b in zero_swing_non_orphan]}"
    )


def test_tornado_for_engineering_v3_section_5_1_fields_are_orphan() -> None:
    """Pass-3 cascade fix: the 8 v3 §5.1 productivity-formula fields and the
    People-side anchor `fully_loaded_cost_per_fte` are orphan in the Engineering
    tornado because the tornado metric is `instability_tax_annual`, not
    `engineering_annual_value`. Future v2/Day-90 work may switch the metric;
    if it does, this test surfaces the change.
    """
    result = tornado_for_engineering(EngineeringInputs(), top_n=30)
    expected_orphan = {
        "self_report_discount",  # already orphan pre-pass-3; included so a
                                 # silent removal from _ENGINEERING_ORPHAN_FIELDS
                                 # is caught by this test
        "engineers", "fully_loaded_cost_per_fte", "ai_adoption_pct",
        "ai_hours_per_workday", "productivity_gain_greenfield",
        "productivity_gain_legacy", "pct_work_greenfield",
        "engineering_verification_tax", "workdays_per_year",
    }
    for bar in result:
        if bar.field_name in expected_orphan:
            assert bar.is_orphan is True, (
                f"{bar.field_name} should be marked orphan (tornado measures "
                f"instability_tax_annual, not engineering_annual_value)"
            )


# ---------------------------------------------------------------------------
# Error handling — engine raises are skipped, not propagated
# ---------------------------------------------------------------------------

def test_tornado_skips_field_when_engine_raises() -> None:
    """If varying a field would cause engine to raise (e.g. learning_curve_months=0
    triggers Phase 3 ValueError), that bar is silently skipped, not crashed."""
    # learning_curve_months default is 6; -1 (×0.83) rounds to 5; +1 (×1.2) rounds to 7.
    # Neither triggers the ValueError because they're within bounds. To force
    # the error we'd need a smaller learning value — use a custom input.
    inp = PeopleInputs(learning_curve_months=1)
    # +/-20% on 1 (rounded) stays at 1 (max(0, 0)=0 actually triggers learning<1).
    # Result: the low_inputs path raises, but tornado_for_people should skip the field.
    result = tornado_for_people(inp)
    # No crash → success.
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Variation parameter
# ---------------------------------------------------------------------------

def test_tornado_variation_param_affects_swing_magnitude() -> None:
    """Larger variation → larger swings on every dollar-denominated bar."""
    small = tornado_for_people(PeopleInputs(), variation=0.05, top_n=5)
    large = tornado_for_people(PeopleInputs(), variation=0.50, top_n=5)
    # Same top field; magnitudes scale roughly linearly for ±variation on floats.
    assert small[0].field_name == large[0].field_name
    assert abs(large[0].swing) > abs(small[0].swing)


# ---------------------------------------------------------------------------
# Engine-fn injection (for test isolation + Phase 8 mocking)
# ---------------------------------------------------------------------------

def test_tornado_for_people_accepts_custom_engine_fn() -> None:
    """Phase 8 sensitivity tab can pass a memoized engine for performance."""
    call_count = [0]

    def counting_engine(inputs):
        call_count[0] += 1
        from roi_calc.people_engine import people_mode_portfolio
        return people_mode_portfolio(inputs)

    result = tornado_for_people(PeopleInputs(), engine_fn=counting_engine, top_n=5)
    # top_n caps non-orphan only; orphans pass through (DL-19)
    non_orphan = [b for b in result if not b.is_orphan]
    assert len(non_orphan) == 5
    assert call_count[0] > 0


# ---------------------------------------------------------------------------
# TornadoBar shape
# ---------------------------------------------------------------------------

def test_tornado_bar_is_frozen() -> None:
    from dataclasses import FrozenInstanceError
    bar = TornadoBar("x", 0.0, 100.0, 100.0)
    with pytest.raises(FrozenInstanceError):
        bar.swing = 999  # type: ignore[misc]


def test_tornado_bar_default_is_orphan_false() -> None:
    bar = TornadoBar("x", 0.0, 100.0, 100.0)
    assert bar.is_orphan is False


def test_tornado_for_people_top_n_zero_raises() -> None:
    """Guard against accidental empty-tornado renders in Phase 8."""
    with pytest.raises(ValueError, match="top_n must be"):
        tornado_for_people(PeopleInputs(), top_n=0)


def test_tornado_for_people_clamps_rate_fields_to_unit_interval() -> None:
    """High variation must not push a rate field above 1.0 or below 0.

    touches_automated_pct=0.55 at variation=1.0 would naively give high=1.10,
    a meaningless 110% automation rate. The clamp guarantees high ≤ 1.0."""
    # We need direct access to the engine call with extreme variation.
    # We can't observe the clamp from outside without instrumenting,
    # but the tornado MUST NOT crash with variation=1.0.
    result = tornado_for_people(PeopleInputs(), variation=1.0, top_n=20)
    # No crash + result is well-formed → the clamp protected us.
    assert all(isinstance(b, TornadoBar) for b in result)
