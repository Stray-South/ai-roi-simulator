"""Decorative capability multipliers (Phase 9 / Option D per DL-8 / DL-24).

Both multipliers return 1.0 in v1. Day-90 calibration with org-measured
baselines replaces the bodies. The wrapper API is the contract.
"""

from __future__ import annotations

from roi_calc.models import PeopleInputs, PortfolioResult


__all__ = [
    "compute_training_multiplier",
    "compute_manager_multiplier",
    "apply_capability_multipliers",
]


def compute_training_multiplier(training_spend_ppt: float) -> float:
    """DL-16: EY 5.9 ppt anchor failed source verification. v1 returns 1.0×.
    Day-90 calibration with your L&D budget + measured productivity replaces."""
    return 1.0


def compute_manager_multiplier(manager_support_score: int) -> float:
    """DL-8 / DL-24: Gallup 8.7× is a likelihood ratio, not a productivity multiplier.
    v1 returns 1.0×. Day-90 calibration replaces."""
    return 1.0


def apply_capability_multipliers(
    portfolio: PortfolioResult, inputs: PeopleInputs
) -> PortfolioResult:
    """Decorative pass-through in v1 — multipliers are 1.0×.

    Risks are NEVER multiplied (only gross savings would be in a calibrated
    v2). Returns a new PortfolioResult; PortfolioResult is frozen.
    """
    training = compute_training_multiplier(inputs.training_spend_ppt)
    manager = compute_manager_multiplier(inputs.manager_support_score)
    combined = training * manager
    return PortfolioResult(
        gross_savings_after_verification_tax=(
            portfolio.gross_savings_after_verification_tax * combined
        ),
        risk_costs=portfolio.risk_costs,  # risks not multiplied
        net_annual_value=(
            portfolio.gross_savings_after_verification_tax * combined
            - portfolio.risk_costs
        ),
    )
