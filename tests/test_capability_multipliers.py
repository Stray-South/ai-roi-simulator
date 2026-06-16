"""Phase 9 tests — Option D decorative multipliers + apply wrapper."""

from __future__ import annotations

import pytest

from roi_calc.capability_multipliers import (
    apply_capability_multipliers,
    compute_manager_multiplier,
    compute_training_multiplier,
)
from roi_calc.models import PeopleInputs, PortfolioResult
from roi_calc.people_engine import people_mode_portfolio


def test_compute_training_multiplier_is_decorative_1x() -> None:
    """DL-16: EY anchor failed source verification → wrapper returns 1.0."""
    assert compute_training_multiplier(0.0) == 1.0
    assert compute_training_multiplier(1.0) == 1.0
    assert compute_training_multiplier(5.0) == 1.0  # max slider


def test_compute_manager_multiplier_is_decorative_1x() -> None:
    """DL-8 / DL-24: Gallup 8.7× is likelihood ratio, not productivity multiplier."""
    for score in range(1, 6):
        assert compute_manager_multiplier(score) == 1.0


def test_apply_capability_multipliers_at_defaults_preserves_portfolio() -> None:
    """Both multipliers 1.0× → output equals input portfolio."""
    inputs = PeopleInputs()
    portfolio = people_mode_portfolio(inputs)
    result = apply_capability_multipliers(portfolio, inputs)
    assert isinstance(result, PortfolioResult)
    assert result.gross_savings_after_verification_tax == pytest.approx(
        portfolio.gross_savings_after_verification_tax, abs=1e-6
    )
    assert result.risk_costs == portfolio.risk_costs
    assert result.net_annual_value == pytest.approx(portfolio.net_annual_value, abs=1e-6)


def test_apply_capability_multipliers_never_multiplies_risk() -> None:
    """Risks are exposure, not savings — even if multipliers were calibrated."""
    inputs = PeopleInputs()
    portfolio = people_mode_portfolio(inputs)
    result = apply_capability_multipliers(portfolio, inputs)
    assert result.risk_costs == portfolio.risk_costs


def test_apply_capability_multipliers_returns_frozen_dataclass() -> None:
    from dataclasses import FrozenInstanceError
    inputs = PeopleInputs()
    portfolio = people_mode_portfolio(inputs)
    result = apply_capability_multipliers(portfolio, inputs)
    with pytest.raises(FrozenInstanceError):
        result.net_annual_value = 999.0  # type: ignore[misc]
