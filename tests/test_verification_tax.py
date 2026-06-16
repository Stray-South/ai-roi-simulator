"""Phase 3 tests — verification tax discipline (applies to gross savings only).

The 37% Workday/Hanover verification tax is the single most-defensible move in
the model. These tests enforce that:
  * apply_verification_tax always multiplies by (1 - tax_rate)
  * Default tax_rate is 0.37 (DL-1 anchor regression)
  * The three SAVINGS calcs are taxed
  * The two RISK calcs are NOT taxed (DL discipline — risk is exposure, not savings)
"""

from __future__ import annotations

import pytest

from roi_calc.constants import (
    BENEFITS_EXPOSURE_PER_500,
    BENEFITS_RECOVERY_PCT,
    COST_PER_HIRE_NONEXEC,
    DROPOUT_CONSERVATIVE,
    HELP_DESK_DEFLECTION_RATE,
    ONBOARDING_WEEKS_AUTOMATED,
    ONBOARDING_WEEKS_BASELINE,
    PIPELINE_PER_REQ,
    TICKET_COST_AGENT,
    TICKET_COST_AI,
    TICKETS_PER_EMPLOYEE_PER_YEAR,
    VERIFICATION_TAX_RATE,
)
from roi_calc.people_engine import (
    apply_verification_tax,
    benefits_billing_recovery_value,
    candidate_pipeline_risk,
    decision_point_risk_delta,
    help_desk_deflection_value,
    onboarding_productivity_delta_value,
)
from roi_calc.models import PeopleInputs


def test_verification_tax_default_rate_is_workday_037() -> None:
    """Spec §5.7 + DL-1 anchor: 37% per Workday/Hanover 2024 n=3,200."""
    assert VERIFICATION_TAX_RATE.value == 0.37
    assert apply_verification_tax(100.0) == pytest.approx(63.0, abs=1e-6)


def test_apply_verification_tax_at_zero_returns_gross() -> None:
    assert apply_verification_tax(1000.0, tax_rate=0.0) == 1000.0


def test_apply_verification_tax_at_one_returns_zero() -> None:
    assert apply_verification_tax(1000.0, tax_rate=1.0) == 0.0


def test_apply_verification_tax_is_linear() -> None:
    """Property: tax(a + b) == tax(a) + tax(b) (no fixed cost component)."""
    assert apply_verification_tax(1000.0) == pytest.approx(
        apply_verification_tax(400.0) + apply_verification_tax(600.0),
        abs=1e-6,
    )


# ---------------------------------------------------------------------------
# Tax applied to all three SAVINGS calcs
# ---------------------------------------------------------------------------

def test_help_desk_deflection_is_taxed() -> None:
    """help_desk gross = employees × tickets × deflection × cost_delta.
    Taxed value = gross × 0.63. Reconstruct gross and assert ratio."""
    inp = PeopleInputs()
    gross = (
        inp.employees
        * TICKETS_PER_EMPLOYEE_PER_YEAR.value
        * HELP_DESK_DEFLECTION_RATE.value
        * (TICKET_COST_AGENT.value - TICKET_COST_AI.value)
    )
    expected_net = gross * (1 - VERIFICATION_TAX_RATE.value)
    assert help_desk_deflection_value(inp) == pytest.approx(expected_net, abs=1e-3)


def test_onboarding_productivity_is_taxed() -> None:
    inp = PeopleInputs()
    weeks_recovered = ONBOARDING_WEEKS_BASELINE.value - ONBOARDING_WEEKS_AUTOMATED.value
    weekly_cost = inp.fully_loaded_cost_per_fte / 52
    gross = inp.annual_hires * weeks_recovered * weekly_cost
    expected_net = gross * (1 - VERIFICATION_TAX_RATE.value)
    assert onboarding_productivity_delta_value(inp) == pytest.approx(expected_net, abs=1e-3)


def test_benefits_billing_is_taxed() -> None:
    inp = PeopleInputs()
    exposure = (inp.employees / 500) * BENEFITS_EXPOSURE_PER_500.value
    gross = exposure * BENEFITS_RECOVERY_PCT.value
    expected_net = gross * (1 - VERIFICATION_TAX_RATE.value)
    assert benefits_billing_recovery_value(inp) == pytest.approx(expected_net, abs=1e-3)


# ---------------------------------------------------------------------------
# Tax NOT applied to RISK calcs (the critical discipline)
# ---------------------------------------------------------------------------

def test_candidate_pipeline_risk_is_NOT_taxed() -> None:
    """Risk is exposure, not savings. Tax must not be applied.
    Reconstruct full gross-equivalent value and assert pipeline_risk equals it (untaxed)."""
    inp = PeopleInputs()
    expected_raw = (
        inp.annual_hires
        * PIPELINE_PER_REQ.value
        * DROPOUT_CONSERVATIVE.value
        * COST_PER_HIRE_NONEXEC.value
    )
    assert candidate_pipeline_risk(inp, "Conservative") == pytest.approx(expected_raw, abs=1e-3)


def test_decision_point_risk_is_NOT_taxed() -> None:
    inp = PeopleInputs()
    annual_dp = inp.annual_hires * inp.decision_points_per_event_baseline
    error_delta = inp.decision_point_error_rate_with_ai - inp.decision_point_error_rate_baseline
    expected_raw = annual_dp * error_delta * inp.decision_point_error_cost_avg
    assert decision_point_risk_delta(inp) == pytest.approx(expected_raw, abs=1e-3)
