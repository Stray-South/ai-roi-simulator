"""Phase 3 tests — break-even chart series (spec §6.1)."""

from __future__ import annotations

import pytest

from roi_calc.constants import (
    IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR,
    IMPLEMENTATION_SETUP_PER_EMPLOYEE,
    RAMP_FLOOR,
)
from roi_calc.models import BreakEvenResult, PeopleInputs
from roi_calc.people_engine import (
    cumulative_cost_vs_savings,
    people_mode_portfolio,
)


# ---------------------------------------------------------------------------
# Pinned: M8 breakeven at sample defaults; +$566,394 at M24 (handoff figures)
# ---------------------------------------------------------------------------

def test_break_even_month_at_prog_defaults_is_8() -> None:
    """At sample defaults (1151 emp / $472,503 annual net / $50+$30 implementation /
    ramp 0/0.058...0.35 over 6 mo / 0.35..1.0 over 6 mo / 1.0 thereafter):
    cumulative savings ($88,594) first exceeds cumulative cost ($80,570) in month 8.
    """
    result = cumulative_cost_vs_savings(PeopleInputs())
    assert result.breakeven_month == 8


def test_break_even_savings_minus_cost_at_month_24_pinned() -> None:
    """Cumulative savings at M24 = $39,375.25 × 17.6 month-equivalents = $693,004.
    Cumulative cost at M24 = $57,550 + 24 × $2,877.50 = $126,610.
    Delta = $566,394."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    delta = result.cumulative_savings[23] - result.cumulative_cost[23]
    assert delta == pytest.approx(566_394, abs=10)


# ---------------------------------------------------------------------------
# BreakEvenResult shape invariants
# ---------------------------------------------------------------------------

def test_break_even_series_length_matches_horizon() -> None:
    inp = PeopleInputs()
    result = cumulative_cost_vs_savings(inp)
    assert len(result.months) == inp.horizon_months
    assert len(result.cumulative_cost) == inp.horizon_months
    assert len(result.cumulative_savings) == inp.horizon_months


def test_break_even_months_are_1_indexed_sequential() -> None:
    result = cumulative_cost_vs_savings(PeopleInputs())
    assert result.months[0] == 1
    assert result.months[-1] == 24
    assert list(result.months) == list(range(1, 25))


def test_break_even_series_are_tuples_not_lists() -> None:
    """Phase 2 DL: BreakEvenResult sequence fields are tuples for true immutability.
    Engine builds with lists, BreakEvenResult.__post_init__ normalizes at construction."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    assert isinstance(result.months, tuple)
    assert isinstance(result.cumulative_cost, tuple)
    assert isinstance(result.cumulative_savings, tuple)


def test_break_even_cumulative_series_are_monotonic_non_decreasing() -> None:
    """Both cumulative cost and cumulative savings only ever grow over time."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    costs = list(result.cumulative_cost)
    savings = list(result.cumulative_savings)
    assert all(costs[i] >= costs[i - 1] for i in range(1, len(costs)))
    assert all(savings[i] >= savings[i - 1] for i in range(1, len(savings)))


# ---------------------------------------------------------------------------
# Ramp shape (§6.1)
# ---------------------------------------------------------------------------

def test_ramp_reaches_floor_at_learning_curve_end() -> None:
    """At month == learning_curve_months, ramp = RAMP_FLOOR (0.35).
    Verify via the month-over-month savings delta at the boundary."""
    inp = PeopleInputs()  # learning_curve=6, steady=12, ramp_floor=0.35
    result = cumulative_cost_vs_savings(inp)
    annual_net = people_mode_portfolio(inp).net_annual_value
    monthly_net = annual_net / 12

    m6_savings_delta = result.cumulative_savings[5] - result.cumulative_savings[4]
    expected_m6 = monthly_net * RAMP_FLOOR.value  # full floor at month 6
    assert m6_savings_delta == pytest.approx(expected_m6, abs=1e-3)


def test_ramp_reaches_1_at_time_to_steady_state() -> None:
    """At month == time_to_steady_state, ramp = 1.0."""
    inp = PeopleInputs()
    result = cumulative_cost_vs_savings(inp)
    annual_net = people_mode_portfolio(inp).net_annual_value
    monthly_net = annual_net / 12

    m12_savings_delta = result.cumulative_savings[11] - result.cumulative_savings[10]
    assert m12_savings_delta == pytest.approx(monthly_net * 1.0, abs=1e-3)


def test_ramp_is_constant_1_after_steady_state() -> None:
    inp = PeopleInputs()
    result = cumulative_cost_vs_savings(inp)
    annual_net = people_mode_portfolio(inp).net_annual_value
    monthly_net = annual_net / 12

    # Months 13..24 all add the same monthly_net (ramp = 1.0)
    for m in range(13, 25):
        delta = result.cumulative_savings[m - 1] - result.cumulative_savings[m - 2]
        assert delta == pytest.approx(monthly_net, abs=1e-3)


# ---------------------------------------------------------------------------
# Cost shape
# ---------------------------------------------------------------------------

def test_implementation_cost_uses_lifted_constants() -> None:
    """DL-3 regression: cost formula pulls from constants, not inline literals."""
    inp = PeopleInputs()
    result = cumulative_cost_vs_savings(inp)
    expected_m1_cost = (
        inp.employees * IMPLEMENTATION_SETUP_PER_EMPLOYEE.value
        + inp.employees * IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR.value / 12
    )
    assert result.cumulative_cost[0] == pytest.approx(expected_m1_cost, abs=1e-3)


def test_cost_grows_by_monthly_recurring_after_month_1() -> None:
    inp = PeopleInputs()
    result = cumulative_cost_vs_savings(inp)
    monthly_recurring = inp.employees * IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR.value / 12
    for m in range(2, inp.horizon_months + 1):
        delta = result.cumulative_cost[m - 1] - result.cumulative_cost[m - 2]
        assert delta == pytest.approx(monthly_recurring, abs=1e-3)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_break_even_returns_none_if_horizon_too_short_to_recover() -> None:
    """If implementation cost dwarfs annual net, savings never cross within horizon.

    Fabricate by giving the org an absurdly high implementation cost via a
    1-month horizon (cost dominates month 1 setup; ramp barely starts)."""
    inp = PeopleInputs(horizon_months=1)
    result = cumulative_cost_vs_savings(inp)
    # Month 1: cost = 1151×$50 + ~$2,877 = ~$60,427; savings = monthly_net × (1/6 × 0.35)
    # ≈ $39,375 × 0.0583 ≈ $2,296. No crossing.
    assert result.breakeven_month is None


def test_break_even_breakeven_month_within_horizon_when_present() -> None:
    """When breakeven_month is set, it must be ≤ horizon_months."""
    inp = PeopleInputs()
    result = cumulative_cost_vs_savings(inp)
    assert result.breakeven_month is not None
    assert 1 <= result.breakeven_month <= inp.horizon_months


def test_break_even_raises_when_learning_exceeds_steady() -> None:
    """Guard against Phase 5 tornado / Phase 6 slider producing
    learning_curve > time_to_steady_state. Without this guard the engine
    silently produces an infinite-floor ramp."""
    inp = PeopleInputs(learning_curve_months=12, time_to_steady_state_months=6)
    with pytest.raises(ValueError, match="must not exceed"):
        cumulative_cost_vs_savings(inp)


def test_break_even_raises_when_learning_is_zero() -> None:
    """Guard: learning < 1 makes the floor formula (month/learning) divide-by-zero
    in spec §6.1 intent, even if the if-branch happens to skip month=1."""
    inp = PeopleInputs(learning_curve_months=0)
    with pytest.raises(ValueError, match="must be ≥ 1"):
        cumulative_cost_vs_savings(inp)


def test_break_even_handles_learning_equal_to_steady() -> None:
    """Spec §6.1 edge: learning == steady means no interpolation segment.
    Ramp jumps from 0.35 (at month=learning) directly to 1.0 (at month=learning+1).
    Spec-conformant and not guarded — documenting the behavior so it's an
    intentional design choice, not a latent surprise."""
    inp = PeopleInputs(learning_curve_months=6, time_to_steady_state_months=6)
    result = cumulative_cost_vs_savings(inp)
    annual_net = people_mode_portfolio(inp).net_annual_value
    monthly_net = annual_net / 12

    # Month 6 (last floor month): ramp = (6/6) × 0.35 = 0.35
    m6_savings_delta = result.cumulative_savings[5] - result.cumulative_savings[4]
    assert m6_savings_delta == pytest.approx(monthly_net * RAMP_FLOOR.value, abs=1e-3)
    # Month 7 (first steady month): ramp = 1.0 (skips elif since 7 > steady)
    m7_savings_delta = result.cumulative_savings[6] - result.cumulative_savings[5]
    assert m7_savings_delta == pytest.approx(monthly_net * 1.0, abs=1e-3)


def test_break_even_at_zero_inputs_returns_degenerate_result() -> None:
    """Edge: employees=0 and annual_hires=0. All five calcs = 0; portfolio = 0;
    monthly_net = 0; cumulative cost = 0 every month (no setup, no recurring);
    cumulative savings = 0. Breakeven trivially fires at month 1 because 0 >= 0.

    Documenting the degenerate behavior — Phase 7 chart code must NOT render
    'Break-even at Month 1' as a credible result when both series are flat zero."""
    inp = PeopleInputs(employees=0, annual_hires=0)
    result = cumulative_cost_vs_savings(inp)
    assert all(c == 0.0 for c in result.cumulative_cost)
    assert all(s == 0.0 for s in result.cumulative_savings)
    # 0 >= 0 satisfies the breakeven predicate at the first month
    assert result.breakeven_month == 1


def test_break_even_result_is_immutable_after_engine() -> None:
    """Phase 2 contract: BreakEvenResult returned by engine is truly immutable."""
    result = cumulative_cost_vs_savings(PeopleInputs())
    with pytest.raises(AttributeError):
        result.months.append(99)  # type: ignore[attr-defined]
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        result.breakeven_month = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DL-28 — shared-core extraction byte-identical regression
# ---------------------------------------------------------------------------

def test_dl28_shared_core_byte_identical_at_prog_defaults() -> None:
    """DL-28: `_build_break_even_series` was extracted from
    `cumulative_cost_vs_savings` so Engineering Mode (Stream B) can share the
    same J-Curve math. The refactor must be byte-identical for People Mode:
    breakeven Month 8, savings−cost at M24 = $566,394, both series 24-long.
    """
    result = cumulative_cost_vs_savings(PeopleInputs())
    assert result.breakeven_month == 8
    assert result.cumulative_savings[23] - result.cumulative_cost[23] == pytest.approx(
        566_394, abs=10
    )
    assert len(result.cumulative_cost) == 24
    assert len(result.cumulative_savings) == 24


def test_dl28_shared_core_invocable_directly_with_arbitrary_annual_net() -> None:
    """The shared core must accept arbitrary annual_net + cost shape — proving
    Engineering Mode (B3) can call it without going through PeopleInputs."""
    from roi_calc.people_engine import _build_break_even_series

    result = _build_break_even_series(
        annual_net=1_000_000.0,
        one_time_setup=50_000.0,
        monthly_recurring=2_500.0,
        learning=6,
        steady=12,
        horizon=24,
        ramp_floor=0.35,
    )
    assert len(result.months) == 24
    assert result.cumulative_cost[0] == pytest.approx(52_500.0, abs=1e-3)
    assert result.breakeven_month is not None and 1 <= result.breakeven_month <= 24
