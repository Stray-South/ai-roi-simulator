"""Engineering Mode engine — DORA J-Curve + instability tax + capability scoring.

Implements v3 spec §5 + DORA's published instability-tax math. Ships in
"Option B" form per DL-14:

  * ``instability_tax``: **real** — reproduces DORA's $344K exactly with
    defaults from DL-9/DL-10
  * ``compute_capability_multiplier`` + ``compute_archetype_multiplier``:
    **decorative-only** (return 1.0 in v1). v3 publishes neither
    numeric weights nor archetype multipliers; Phase 4 ships the API so
    Phase 10 UI can wire it, but Day-90 calibration with org-measured
    baselines is the actual deliverable
  * ``apply_user_centric_gate``: **real** — DORA 2025 finding that score ≤ 2
    on user-centric focus zeros out AI value (DL-13)
  * ``engineering_portfolio``: returns instability tax + ``"v3-pending"``
    annotations on multiplier-derived dollar fields (no fabricated numbers)

This is the credibility-check half of the dual-mode demo: real DORA math
visible, calibration claims surfaced as pending. Phase 10 wires the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from roi_calc.constants import (
    HORIZON_MONTHS,
    IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR,
    IMPLEMENTATION_SETUP_PER_EMPLOYEE,
    LEARNING_CURVE_MONTHS,
    RAMP_FLOOR,
    TIME_TO_STEADY_STATE_MONTHS,
)
from roi_calc.models import Archetype, BreakEvenResult, EngineeringInputs


__all__ = [
    "instability_tax",
    "compute_capability_multiplier",
    "compute_archetype_multiplier",
    "apply_user_centric_gate",
    "user_centric_gate_active",
    "engineering_portfolio",
    "engineering_annual_value",
    "engineering_cumulative_cost_vs_savings",
    "EngineeringPortfolioResult",
    "V3PendingStatus",
]


# Engineering working hours per FTE = workdays_per_year × 8, derived at
# runtime from EngineeringInputs.workdays_per_year so the hours-saved
# numerator and hourly-cost denominator stay consistent under user-edited
# workdays. At defaults (235 workdays) this equals 1,880 per v3 §5.1 table
# `working_hours_per_year=1880`.
#
# Intentionally distinct from the 2,080-hr divisor used in BLS OEWS
# loaded-hourly citation math (constants.py BLS rates): BLS uses 2,080
# because OEWS publishes annual mean wages assuming full-year employment;
# v3 §5.1 uses workdays × 8 because productivity gain is only realized
# during actual productive workdays (subtracts PTO + holidays).
_STANDARD_WORKDAY_HOURS = 8


# Status sentinel for multiplier-derived dollar values that depend on v3
# calibrations not yet on disk. Phase 10 UI renders this as the
# "v3-calibration pending" annotation instead of a dollar figure.
V3PendingStatus = Literal["v3-calibration pending"]


@dataclass(frozen=True)
class EngineeringPortfolioResult:
    """Output of Engineering Mode portfolio (Phase 4 Option B).

    ``instability_tax_annual`` is a REAL DORA-reproducible dollar figure.
    The two ``*_status`` fields carry the ``"v3-calibration pending"``
    sentinel for outputs that depend on un-sourced multipliers (DL-14).
    """

    instability_tax_annual: float
    archetype_adjusted_status: V3PendingStatus
    capability_adjusted_status: V3PendingStatus
    user_centric_gate_triggered: bool

    def __post_init__(self) -> None:
        # Runtime enforcement of the V3PendingStatus Literal — Python doesn't
        # enforce Literal types at runtime, so a caller could construct this
        # with any string and the type-checker wouldn't catch it. The whole
        # point of these fields is to be the exact sentinel Phase 10 UI greps for.
        _SENTINEL = "v3-calibration pending"
        if self.archetype_adjusted_status != _SENTINEL:
            raise ValueError(
                f"archetype_adjusted_status must be {_SENTINEL!r}, got {self.archetype_adjusted_status!r}"
            )
        if self.capability_adjusted_status != _SENTINEL:
            raise ValueError(
                f"capability_adjusted_status must be {_SENTINEL!r}, got {self.capability_adjusted_status!r}"
            )


# ---------------------------------------------------------------------------
# Instability tax — REAL (reproduces DORA's $344K exactly)
# ---------------------------------------------------------------------------

def instability_tax(
    cfr_before: float,
    cfr_after: float,
    deployments_per_year: int,
    incident_cost: float,
) -> float:
    """DORA 2026 instability tax: ``(cfr_after − cfr_before) × deploys × incident_cost``.

    At DL-9/DL-10 defaults — cfr 0.05 → 0.06, deploys=100, incident=$344,000 —
    this returns exactly $344,000 (the figure DORA publishes in InfoQ May 2026 +
    DORA ROI Report 2026.01).

    Test ``test_instability_tax_reproduces_344k`` is the T2 anchor regression.
    """
    return (cfr_after - cfr_before) * deployments_per_year * incident_cost


# ---------------------------------------------------------------------------
# Capability + Archetype multipliers — DECORATIVE (Option B per DL-14)
# ---------------------------------------------------------------------------

def compute_capability_multiplier(scores: dict[str, int]) -> float:
    """v3-pending decorative wrapper. Returns ``1.0`` in v1.

    v3 spec is expected to publish numeric weights for the 7 DORA capabilities
    (clear_ai_stance, healthy_data_ecosystem, ai_accessible_data, version_control,
    small_batches, user_centric_focus, quality_platform). Until those are on
    disk, Phase 10 UI renders multiplier-derived dollar values as
    ``"v3-calibration pending"``.

    Why the wrapper exists in v1: Phase 10 UI codes against this signature.
    When v3 lands, the body becomes the real calibration math.
    """
    return 1.0


def compute_archetype_multiplier(archetype: Archetype) -> float:
    """v3-pending decorative wrapper. Returns ``1.0`` in v1.

    v3 spec is expected to publish multipliers for the 7 DORA archetypes
    (Foundational Challenges through Harmonious High-Achievers). Same Option B
    rationale as ``compute_capability_multiplier``.
    """
    return 1.0


# ---------------------------------------------------------------------------
# User-centric focus gate — REAL (DORA 2025 finding)
# ---------------------------------------------------------------------------

def _validate_user_centric_score(score: int) -> None:
    """Score must be an int in 1..5 (DORA §4.8 scale).

    ``bool`` is rejected explicitly: ``isinstance(True, int)`` is True in Python,
    so without this guard ``apply_user_centric_gate(True, ...)`` would silently
    treat the boolean as score=1.
    """
    if isinstance(score, bool) or not isinstance(score, int):
        raise TypeError(
            f"user_centric_focus_score must be int, got {type(score).__name__}: {score!r}"
        )
    if not 1 <= score <= 5:
        raise ValueError(
            f"user_centric_focus_score must be in 1..5 (DORA scale), got {score}"
        )


def user_centric_gate_active(user_centric_focus_score: int) -> bool:
    """Single-source predicate for the DL-13 gate.

    Returns ``True`` when the user-centric focus score triggers the
    value-attenuation gate (score ≤ 2). Used by ``engineering_portfolio``
    so the threshold lives in exactly one place and isn't back-inferred
    from a float-equality probe.
    """
    _validate_user_centric_score(user_centric_focus_score)
    return user_centric_focus_score <= 2


def apply_user_centric_gate(user_centric_focus_score: int, multiplier: float) -> float:
    """DORA 2025: teams that score ≤ 2 on user-centric focus produce
    NEGATIVE value from AI adoption (the headline "AI can harm teams" finding).

    DL-13: gate is binary — score ≤ 2 zeros the multiplier; else passes through.
    This applies REGARDLESS of v3-pending multiplier calibration; the gate
    threshold itself is the headline DORA finding, not a calibration.

    Phase 10 Assessment radar shows a red highlight on the user_centric_focus
    axis when this triggers.

    Score range per v3 §4.8 is 1–5; ints only. Out-of-range or non-int scores
    fail loudly instead of silently producing nonsense.

    Delegates threshold check to ``user_centric_gate_active`` so the DL-13
    threshold lives in exactly one place — if the threshold ever shifts, both
    this function and ``engineering_portfolio`` pick up the change.
    """
    if user_centric_gate_active(user_centric_focus_score):
        return 0.0
    return multiplier


# ---------------------------------------------------------------------------
# Annual value — v3 §5.1 productivity formula (Phase 14 Stream B2 / DL-29)
# ---------------------------------------------------------------------------

def engineering_annual_value(inputs: EngineeringInputs) -> float:
    """Engineering Mode annual net value per v3 §5.1 productivity formula.

    Math:
        raw_gain         = pct_work_greenfield × productivity_gain_greenfield
                         + (1 − pct_work_greenfield) × productivity_gain_legacy
        effective_gain   = raw_gain × self_report_discount × (1 − engineering_verification_tax)
        adopting_eng     = engineers × ai_adoption_pct
        hours_saved/yr   = ai_hours_per_workday × workdays_per_year × effective_gain
        hourly_cost      = fully_loaded_cost_per_fte / (workdays_per_year × 8)
        gross_annual     = adopting_eng × hours_saved × hourly_cost
        annual_net       = gross_annual − instability_tax (at the inputs' CFR/deploys/incident)

    Per DL-14 Option B: ``compute_capability_multiplier`` and
    ``compute_archetype_multiplier`` are NOT folded into this value — they
    return 1.0 in v1 and the multiplier-derived portfolio is rendered as
    ``"v3-calibration pending"`` by ``engineering_portfolio``. This function
    is the real, v3-§5.1-published productivity formula; Day-90 work replaces
    the multiplier wrappers with calibrated weights.
    """
    raw_gain = (
        inputs.pct_work_greenfield * inputs.productivity_gain_greenfield
        + (1.0 - inputs.pct_work_greenfield) * inputs.productivity_gain_legacy
    )
    effective_gain = (
        raw_gain
        * inputs.self_report_discount
        * (1.0 - inputs.engineering_verification_tax)
    )
    adopting_engineers = inputs.engineers * inputs.ai_adoption_pct
    hours_saved_per_engineer = (
        inputs.ai_hours_per_workday * inputs.workdays_per_year * effective_gain
    )
    # Deriving hourly_cost from the same `workdays_per_year` that drives
    # hours_saved keeps the two terms consistent under user-edited workdays.
    # Mathematically `workdays_per_year` cancels in the gross-value product
    # (it appears in both the savings numerator and the cost denominator);
    # the cancellation IS the consistency guarantee — see test
    # `test_engineering_annual_value_workdays_per_year_cancellation_invariance`.
    hourly_cost = inputs.fully_loaded_cost_per_fte / (
        inputs.workdays_per_year * _STANDARD_WORKDAY_HOURS
    )
    gross_annual = adopting_engineers * hours_saved_per_engineer * hourly_cost
    tax = instability_tax(
        cfr_before=inputs.cfr_before,
        cfr_after=inputs.cfr_after,
        deployments_per_year=inputs.deploys_per_year,
        incident_cost=inputs.incident_cost,
    )
    return gross_annual - tax


# ---------------------------------------------------------------------------
# Engineering Mode J-Curve (Phase 14 Stream B3 / DL-29) — shares the DL-28
# core with People Mode; differs in annual_net (productivity formula) and
# implementation cost base (engineers × per-employee rate).
# ---------------------------------------------------------------------------

def engineering_cumulative_cost_vs_savings(inputs: EngineeringInputs) -> BreakEvenResult:
    """Engineering Mode J-Curve via the shared core extracted in DL-28.

    Differences vs People Mode:
      * ``annual_net`` comes from ``engineering_annual_value`` (v3 §5.1
        productivity formula), not the 5 hard-dollar People calcs
      * Cost base is ``engineers × IMPLEMENTATION_*_PER_EMPLOYEE``, not
        ``employees ×`` the same constants
      * J-Curve timing constants are shared (DORA engineering analog applies
        to both modes; v2 backlog: Engineering-specific J-Curve timing once
        your sprint-tag data is on disk)
    """
    # Function-local import: `_build_break_even_series` is private shared infra
    # in people_engine. There is no actual import cycle today (people_engine
    # doesn't import engineering_engine), but keeping it local avoids elevating
    # a leading-underscore implementation detail to a module-level dependency.
    from roi_calc.people_engine import _build_break_even_series

    annual_net = engineering_annual_value(inputs)
    one_time_setup = inputs.engineers * IMPLEMENTATION_SETUP_PER_EMPLOYEE.value
    annual_recurring = inputs.engineers * IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR.value

    return _build_break_even_series(
        annual_net=annual_net,
        one_time_setup=one_time_setup,
        monthly_recurring=annual_recurring / 12,
        learning=LEARNING_CURVE_MONTHS.value,
        steady=TIME_TO_STEADY_STATE_MONTHS.value,
        horizon=HORIZON_MONTHS.value,
        ramp_floor=RAMP_FLOOR.value,
    )


# ---------------------------------------------------------------------------
# Engineering portfolio (Option B composition)
# ---------------------------------------------------------------------------

def engineering_portfolio(inputs: EngineeringInputs) -> EngineeringPortfolioResult:
    """Compose Engineering Mode outputs per Option B (DL-14):

      * Instability tax → REAL dollar
      * Archetype-adjusted portfolio → "v3-calibration pending"
      * Capability-adjusted portfolio → "v3-calibration pending"
      * User-centric gate triggered → REAL bool (drives Assessment radar warning)
    """
    tax = instability_tax(
        cfr_before=inputs.cfr_before,
        cfr_after=inputs.cfr_after,
        deployments_per_year=inputs.deploys_per_year,
        incident_cost=inputs.incident_cost,
    )
    # Single-source the gate threshold via the dedicated predicate, not a
    # float-equality probe through apply_user_centric_gate.
    gate_triggered = user_centric_gate_active(inputs.user_centric_focus)
    return EngineeringPortfolioResult(
        instability_tax_annual=tax,
        archetype_adjusted_status="v3-calibration pending",
        capability_adjusted_status="v3-calibration pending",
        user_centric_gate_triggered=gate_triggered,
    )
