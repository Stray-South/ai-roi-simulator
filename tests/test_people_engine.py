"""Phase 3 tests — five hard-dollar calculations + portfolio reconciliation.

Pinned-value tests use ``abs=10`` tolerance per DL-20 — math reconciles to
within $10 of the expected values at sample defaults (handoff figures, not
unified plan's rounding-drifted variants).
"""

from __future__ import annotations

import pytest

from roi_calc.people_engine import (
    apply_verification_tax,
    benefits_billing_recovery_value,
    candidate_pipeline_risk,
    decision_point_risk_delta,
    help_desk_deflection_value,
    onboarding_productivity_delta_value,
    people_mode_portfolio,
)
from roi_calc.models import PeopleInputs, PortfolioResult


# ---------------------------------------------------------------------------
# Pinned expected values @ sample defaults (DL-20, abs=10)
# ---------------------------------------------------------------------------

def test_help_desk_deflection_value_pinned() -> None:
    """1151 × 26 × 0.425 × $13 × 0.63 = $104,164.92 → $104,165."""
    assert help_desk_deflection_value(PeopleInputs()) == pytest.approx(104_165, abs=10)


def test_onboarding_productivity_delta_value_pinned() -> None:
    """230 × 2.6 × ($124,615/52) × 0.63 = $902,835.67 → $902,836."""
    assert onboarding_productivity_delta_value(PeopleInputs()) == pytest.approx(902_836, abs=10)


def test_benefits_billing_recovery_value_pinned() -> None:
    """(1151/500) × $1M × 0.20 × 0.63 = $290,052.20 → $290,052."""
    assert benefits_billing_recovery_value(PeopleInputs()) == pytest.approx(290_052, abs=10)


def test_candidate_pipeline_risk_conservative_pinned() -> None:
    """230 × 5 × 0.12 × $5,475 = $755,550 exact."""
    assert candidate_pipeline_risk(PeopleInputs(), "Conservative") == pytest.approx(755_550, abs=10)


def test_candidate_pipeline_risk_realistic_pinned() -> None:
    """230 × 5 × 0.22 × $5,475 = $1,385,175 exact."""
    assert candidate_pipeline_risk(PeopleInputs(), "Realistic") == pytest.approx(1_385_175, abs=10)


def test_candidate_pipeline_risk_aggressive_pinned() -> None:
    """230 × 5 × 0.31 × $5,475 = $1,951,837.50 → $1,951,838."""
    assert candidate_pipeline_risk(PeopleInputs(), "Aggressive") == pytest.approx(1_951_838, abs=10)


def test_decision_point_risk_delta_pinned() -> None:
    """230 × 4 × 0.015 × $5,000 = $69,000 exact."""
    assert decision_point_risk_delta(PeopleInputs()) == pytest.approx(69_000, abs=10)


def test_people_mode_portfolio_pinned_at_sample_defaults() -> None:
    """End-to-end reconciliation: gross $1,297,053 − risk $824,550 = net $472,503."""
    result = people_mode_portfolio(PeopleInputs())
    assert isinstance(result, PortfolioResult)
    assert result.gross_savings_after_verification_tax == pytest.approx(1_297_053, abs=10)
    assert result.risk_costs == pytest.approx(824_550, abs=10)
    assert result.net_annual_value == pytest.approx(472_503, abs=10)


# ---------------------------------------------------------------------------
# DL-19 — portfolio total hardcodes Conservative even when input.pipeline_scenario differs
# ---------------------------------------------------------------------------

def test_portfolio_total_ignores_pipeline_scenario_input() -> None:
    """DL-19 + spec §5.6: portfolio uses Conservative anchor regardless of
    ``inputs.pipeline_scenario``. Toggle drives risk-tile + tornado only."""
    inp_cons = PeopleInputs(pipeline_scenario="Conservative")
    inp_real = PeopleInputs(pipeline_scenario="Realistic")
    inp_aggr = PeopleInputs(pipeline_scenario="Aggressive")
    p_cons = people_mode_portfolio(inp_cons)
    p_real = people_mode_portfolio(inp_real)
    p_aggr = people_mode_portfolio(inp_aggr)
    # All three must produce identical portfolio totals — demo-safe.
    assert p_cons.net_annual_value == pytest.approx(p_real.net_annual_value, abs=1)
    assert p_cons.net_annual_value == pytest.approx(p_aggr.net_annual_value, abs=1)
    assert p_cons.net_annual_value == pytest.approx(472_503, abs=10)


def test_candidate_pipeline_risk_honors_scenario_when_called_directly() -> None:
    """The scenario parameter is honored when callers (Phase 6 risk-tile,
    Phase 5 tornado) pass it explicitly."""
    inp = PeopleInputs()
    cons = candidate_pipeline_risk(inp, "Conservative")
    real = candidate_pipeline_risk(inp, "Realistic")
    aggr = candidate_pipeline_risk(inp, "Aggressive")
    assert cons < real < aggr
    assert cons == pytest.approx(755_550, abs=10)
    assert aggr == pytest.approx(1_951_838, abs=10)


def test_candidate_pipeline_risk_defaults_to_inputs_scenario() -> None:
    """When scenario=None, falls back to ``inputs.pipeline_scenario`` (Phase 6
    risk-tile pattern)."""
    aggr_input = PeopleInputs(pipeline_scenario="Aggressive")
    risk_default = candidate_pipeline_risk(aggr_input)
    risk_explicit = candidate_pipeline_risk(aggr_input, "Aggressive")
    assert risk_default == risk_explicit


# ---------------------------------------------------------------------------
# Gate 10 regression
# ---------------------------------------------------------------------------

def test_gate10_portfolio_result_no_compensation_in_engine_output() -> None:
    """The engine returns a PortfolioResult shaped per Phase 2 contract.
    PortfolioResult has no compensation_multiple field; this is the Phase 3
    consumer-side guard that the engine doesn't return a dict with a comp key."""
    result = people_mode_portfolio(PeopleInputs())
    # PortfolioResult is a dataclass; introspect its fields not as dict keys
    from dataclasses import fields
    field_names = {f.name for f in fields(result)}
    for name in field_names:
        lname = name.lower()
        assert "compensation" not in lname
        assert "comp" not in lname
        assert "salary" not in lname
        assert "145" not in name


# ---------------------------------------------------------------------------
# Engine sanity: results are non-negative + finite
# ---------------------------------------------------------------------------

def test_all_savings_calcs_return_positive_floats() -> None:
    inp = PeopleInputs()
    for fn in (
        help_desk_deflection_value,
        onboarding_productivity_delta_value,
        benefits_billing_recovery_value,
    ):
        val = fn(inp)
        assert isinstance(val, float)
        assert val > 0


def test_all_risk_calcs_return_positive_floats() -> None:
    inp = PeopleInputs()
    pipeline = candidate_pipeline_risk(inp, "Conservative")
    dp = decision_point_risk_delta(inp)
    assert isinstance(pipeline, float)
    assert isinstance(dp, float)
    assert pipeline > 0
    assert dp > 0


def test_decision_point_risk_returns_negative_when_ai_reduces_errors() -> None:
    """Sign-convention test: with_ai - baseline. If AI improves error rates
    (with_ai < baseline), the risk delta is negative — credits the portfolio
    rather than charging it. This is economically correct and intentional.
    Phase 5 tornado may sweep this regime."""
    inp = PeopleInputs(
        decision_point_error_rate_baseline=0.05,
        decision_point_error_rate_with_ai=0.02,  # AI is BETTER than baseline
    )
    result = decision_point_risk_delta(inp)
    assert result < 0
    # Magnitude check: 230 × 4 × (0.02 - 0.05) × 5000 = 230 × 4 × -0.03 × 5000 = -$138,000
    assert result == pytest.approx(-138_000, abs=10)


def test_zero_employees_and_hires_produces_zero_portfolio() -> None:
    """Edge: employees=0 and annual_hires=0 zero out every calc.
    Result is degenerate but not crashy — Phase 6 UI may receive this if the
    user clears the org inputs."""
    inp = PeopleInputs(employees=0, annual_hires=0)
    assert help_desk_deflection_value(inp) == 0
    assert onboarding_productivity_delta_value(inp) == 0
    assert benefits_billing_recovery_value(inp) == 0
    assert candidate_pipeline_risk(inp, "Conservative") == 0
    assert decision_point_risk_delta(inp) == 0
    portfolio = people_mode_portfolio(inp)
    assert portfolio.gross_savings_after_verification_tax == 0
    assert portfolio.risk_costs == 0
    assert portfolio.net_annual_value == 0
