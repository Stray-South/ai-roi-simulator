"""People Mode engine — the five hard-dollar calculations + portfolio + break-even.

Implements v4.2 spec §5.1–5.7 (hard-dollar calcs + verification tax + portfolio)
and §6.1 (break-even chart). Pure Python; zero Streamlit imports.

Cascade-locked decisions (see ``docs/DECISION_LOG.md``):
  * DL-1  — ``candidate_pipeline_risk`` uses ``PIPELINE_PER_REQ = 5`` (spec
            patch from 50; at 50 portfolio nets to −$6.3M)
  * DL-3  — ``cumulative_cost_vs_savings`` pulls ``RAMP_FLOOR``,
            ``IMPLEMENTATION_SETUP_PER_EMPLOYEE``,
            ``IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR`` from constants
            (lifted from §6.1 inline literals into audit-visible Citations)
  * DL-19 — ``people_mode_portfolio`` hardcodes ``"Conservative"`` for the
            risk component per spec §5.6; the user-editable
            ``inputs.pipeline_scenario`` drives only the risk-tile display
            (and Phase 5 tornado), NOT the portfolio total
  * DL-20 — pinned expected outputs at sample defaults reconcile to within
            $10 of the math-exact values; tests in ``test_people_engine.py``
            assert with ``abs=10`` tolerance
  * Gate 10 — ``PortfolioResult`` carries no ``compensation_multiple`` field;
              this module produces no $145K comparison anywhere
"""

from __future__ import annotations

from roi_calc.constants import (
    BENEFITS_EXPOSURE_PER_500,
    BENEFITS_RECOVERY_PCT,
    COST_PER_HIRE_NONEXEC,
    DROPOUT_AGGRESSIVE,
    DROPOUT_CONSERVATIVE,
    DROPOUT_REALISTIC,
    HELP_DESK_DEFLECTION_RATE,
    IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR,
    IMPLEMENTATION_SETUP_PER_EMPLOYEE,
    ONBOARDING_WEEKS_AUTOMATED,
    ONBOARDING_WEEKS_BASELINE,
    PIPELINE_PER_REQ,
    RAMP_FLOOR,
    TICKET_COST_AGENT,
    TICKET_COST_AI,
    TICKETS_PER_EMPLOYEE_PER_YEAR,
    VERIFICATION_TAX_RATE,
)
from roi_calc.models import (
    BreakEvenResult,
    PeopleInputs,
    PipelineScenario,
    PortfolioResult,
)


__all__ = [
    "apply_verification_tax",
    "help_desk_deflection_value",
    "onboarding_productivity_delta_value",
    "benefits_billing_recovery_value",
    "candidate_pipeline_risk",
    "decision_point_risk_delta",
    "people_mode_portfolio",
    "cumulative_cost_vs_savings",
]


_DROPOUT_BY_SCENARIO: dict[PipelineScenario, float] = {
    "Conservative": DROPOUT_CONSERVATIVE.value,
    "Realistic": DROPOUT_REALISTIC.value,
    "Aggressive": DROPOUT_AGGRESSIVE.value,
}


# ---------------------------------------------------------------------------
# Universal verification tax (Workday/Hanover 2024 n=3,200)
# ---------------------------------------------------------------------------

def apply_verification_tax(
    gross: float, tax_rate: float = VERIFICATION_TAX_RATE.value
) -> float:
    """Net-down every gross savings figure by ``(1 − tax_rate)``.

    Default ``tax_rate=0.37`` per Workday/Hanover Research 2024.
    Applied to all three savings calcs; NOT applied to risk calcs.
    """
    return gross * (1 - tax_rate)


# ---------------------------------------------------------------------------
# Three hard-dollar SAVINGS calcs (taxed)
# ---------------------------------------------------------------------------

def help_desk_deflection_value(inputs: PeopleInputs) -> float:
    """§5.1 — Unthread 2025: tickets × deflection × (agent − AI cost) × (1 − tax)."""
    annual_tickets = inputs.employees * TICKETS_PER_EMPLOYEE_PER_YEAR.value
    deflected = annual_tickets * HELP_DESK_DEFLECTION_RATE.value
    cost_delta = TICKET_COST_AGENT.value - TICKET_COST_AI.value
    gross = deflected * cost_delta
    return apply_verification_tax(gross)


def onboarding_productivity_delta_value(inputs: PeopleInputs) -> float:
    """§5.2 — Mewayz 2026: weeks recovered × hires × weekly FTE cost × (1 − tax)."""
    weeks_recovered = ONBOARDING_WEEKS_BASELINE.value - ONBOARDING_WEEKS_AUTOMATED.value
    weekly_loaded_cost = inputs.fully_loaded_cost_per_fte / 52
    gross = inputs.annual_hires * weeks_recovered * weekly_loaded_cost
    return apply_verification_tax(gross)


def benefits_billing_recovery_value(
    inputs: PeopleInputs, recovery_pct: float | None = None
) -> float:
    """§5.3 — Beneration Nov 2025: $1M discrepancy per 500 employees × recovery%.

    ``recovery_pct`` defaults to ``BENEFITS_RECOVERY_PCT.value`` (0.20 T5 amber).
    """
    if recovery_pct is None:
        recovery_pct = BENEFITS_RECOVERY_PCT.value
    exposure = (inputs.employees / 500) * BENEFITS_EXPOSURE_PER_500.value
    gross = exposure * recovery_pct
    return apply_verification_tax(gross)


# ---------------------------------------------------------------------------
# Two RISK calcs (NOT taxed — these are exposure, not savings)
# ---------------------------------------------------------------------------

def candidate_pipeline_risk(
    inputs: PeopleInputs, scenario: PipelineScenario | None = None
) -> float:
    """§5.4 — Greenhouse 2025 + SHRM 2025: reqs × pipeline × dropout × cost-per-hire.

    NOT net of verification tax — this is risk exposure, not savings.

    ``scenario`` defaults to ``inputs.pipeline_scenario`` (Conservative). Phase 6
    radio drives this for the risk-tile display; ``people_mode_portfolio``
    hardcodes "Conservative" per DL-19 / spec §5.6.
    """
    if scenario is None:
        scenario = inputs.pipeline_scenario
    dropout_rate = _DROPOUT_BY_SCENARIO[scenario]
    return (
        inputs.annual_hires
        * PIPELINE_PER_REQ.value
        * dropout_rate
        * COST_PER_HIRE_NONEXEC.value
    )


def decision_point_risk_delta(inputs: PeopleInputs) -> float:
    """§5.5 — T·T·D primitive: decision points × error-rate delta × error cost.

    NOT net of verification tax — risk exposure, not savings.
    Mobley v. Workday + Kistler v. Eightfold tail-risk footnote rendered in
    Phase 7 Results tab per Gate 11.

    **Sign convention:** ``with_ai − baseline`` (not absolute value). If a
    deployment actually reduces error rates (``with_ai < baseline``) this returns
    a negative value, which subtracts from total risk in ``people_mode_portfolio``
    — effectively adding to net benefit. This is economically correct: if AI is
    *better* than baseline at compliance decisions, the risk-tile shows a credit,
    not an expense. Phase 5 tornado may probe this regime.
    """
    annual_decision_points = inputs.annual_hires * inputs.decision_points_per_event_baseline
    error_rate_increase = (
        inputs.decision_point_error_rate_with_ai
        - inputs.decision_point_error_rate_baseline
    )
    additional_errors = annual_decision_points * error_rate_increase
    return additional_errors * inputs.decision_point_error_cost_avg


# ---------------------------------------------------------------------------
# Portfolio combiner
# ---------------------------------------------------------------------------

def people_mode_portfolio(inputs: PeopleInputs) -> PortfolioResult:
    """§5.6 — sum the three savings (post-tax) and subtract the two risks.

    DL-19: portfolio total hardcodes "Conservative" for ``candidate_pipeline_risk``.
    The ``inputs.pipeline_scenario`` field exists for the Phase 6 risk-tile
    radio display + Phase 5 tornado sensitivity, NOT for the portfolio total.
    """
    gross = (
        help_desk_deflection_value(inputs)
        + onboarding_productivity_delta_value(inputs)
        + benefits_billing_recovery_value(inputs)
    )
    risk = (
        candidate_pipeline_risk(inputs, scenario="Conservative")  # DL-19 hardcode
        + decision_point_risk_delta(inputs)
    )
    return PortfolioResult(
        gross_savings_after_verification_tax=gross,
        risk_costs=risk,
        net_annual_value=gross - risk,
    )


# ---------------------------------------------------------------------------
# Break-even chart series (§6.1)
# ---------------------------------------------------------------------------

def _build_break_even_series(
    annual_net: float,
    one_time_setup: float,
    monthly_recurring: float,
    learning: int,
    steady: int,
    horizon: int,
    ramp_floor: float,
) -> BreakEvenResult:
    """Shared core used by both People Mode and Engineering Mode J-Curves (DL-28).

    Spec §6.1 ramp + cost shape:
      * months 1..learning: ramp = (month/learning) × ramp_floor
      * months (learning+1)..steady: linear from ramp_floor → 1.0
      * months thereafter: ramp = 1.0
      * month 1 cost: one_time_setup + monthly_recurring
      * months 2+ cost: monthly_recurring

    ``breakeven_month`` is the first month where cumulative savings ≥ cumulative
    cost; ``None`` if no crossing within horizon.

    Validation: learning must be in [1, steady] (otherwise raises ValueError).
    """
    if learning > steady:
        raise ValueError(
            f"learning_curve_months ({learning}) must not exceed "
            f"time_to_steady_state_months ({steady}); ramp shape is undefined."
        )
    if learning < 1:
        raise ValueError(
            f"learning_curve_months ({learning}) must be ≥ 1; "
            f"floor formula (month/learning) requires a positive denominator."
        )

    monthly_net = annual_net / 12

    cumulative_cost: list[float] = []
    cumulative_savings: list[float] = []

    for month in range(1, horizon + 1):
        month_cost = one_time_setup + monthly_recurring if month == 1 else monthly_recurring

        if month <= learning:
            ramp = (month / learning) * ramp_floor
        elif month <= steady:
            progress = (month - learning) / (steady - learning)
            ramp = ramp_floor + (1.0 - ramp_floor) * progress
        else:
            ramp = 1.0

        month_savings = monthly_net * ramp

        prev_cost = cumulative_cost[-1] if cumulative_cost else 0.0
        prev_savings = cumulative_savings[-1] if cumulative_savings else 0.0
        cumulative_cost.append(prev_cost + month_cost)
        cumulative_savings.append(prev_savings + month_savings)

    breakeven_month: int | None = next(
        (i + 1 for i, (c, s) in enumerate(zip(cumulative_cost, cumulative_savings)) if s >= c),
        None,
    )

    return BreakEvenResult(
        months=tuple(range(1, horizon + 1)),
        cumulative_cost=tuple(cumulative_cost),
        cumulative_savings=tuple(cumulative_savings),
        breakeven_month=breakeven_month,
    )


def cumulative_cost_vs_savings(inputs: PeopleInputs) -> BreakEvenResult:
    """§6.1 — People Mode J-Curve. Thin wrapper around ``_build_break_even_series``
    (DL-28 shared-core extraction). Pinned regression: $472,503 net / breakeven
    Month 8 byte-identical to pre-refactor (Phase 3 + Stream A verified).

    DL-3: ``RAMP_FLOOR``, ``IMPLEMENTATION_SETUP_PER_EMPLOYEE``, and
    ``IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR`` are Citation-sourced
    audit-visible constants.
    """
    annual_net = people_mode_portfolio(inputs).net_annual_value
    one_time_setup = inputs.employees * IMPLEMENTATION_SETUP_PER_EMPLOYEE.value
    annual_recurring = inputs.employees * IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR.value
    return _build_break_even_series(
        annual_net=annual_net,
        one_time_setup=one_time_setup,
        monthly_recurring=annual_recurring / 12,
        learning=inputs.learning_curve_months,
        steady=inputs.time_to_steady_state_months,
        horizon=inputs.horizon_months,
        ramp_floor=RAMP_FLOOR.value,
    )
