"""Input + output dataclasses for the AI ROI Simulator.

All shapes are ``frozen=True`` so mode-toggle session-state invalidation
(DL-22 / Cascade 8) doesn't have to defensively copy.

Cascade-locked decisions (see ``docs/DECISION_LOG.md``):
  * DL-7  — ``PortfolioResult`` and ``BreakEvenResult`` are frozen dataclasses
            (spec §5.6 used a dict; switched to typed shape for composability)
  * DL-17 — ``PeopleInputs`` has **no** ``discount_rate_annual`` field
            (orphan in spec — no §5/§6 function references it)
  * DL-19 — ``pipeline_scenario`` is a user-editable input; portfolio total
            hardcodes Conservative per spec §5.6; toggle drives risk-tile only
  * Gate 10 — ``PortfolioResult`` does NOT have a ``compensation_multiple``
              field; no $145K comparison anywhere in engine output
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from roi_calc.constants import (
    AI_ADOPTION_PCT,
    AI_HOURS_PER_WORKDAY,
    DECISION_POINT_ERROR_COST,
    DECISION_POINTS_PER_EVENT,
    DEPLOYS_PER_YEAR_DORA,
    DP_ERROR_RATE_BASELINE,
    DP_ERROR_RATE_WITH_AI,
    ENGINEERING_VERIFICATION_TAX,
    HORIZON_MONTHS,
    HR_MANAGER_LOADED_HOURLY,
    HR_SPECIALIST_LOADED_HOURLY,
    INCIDENT_COST_DORA,
    IT_SPECIALIST_LOADED_HOURLY,
    LEARNING_CURVE_MONTHS,
    METR_SELF_REPORT_DISCOUNT,
    ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
    ONBOARDING_TOUCHES_PER_EVENT_BASELINE,
    PCT_WORK_GREENFIELD,
    PRODUCTIVITY_GAIN_GREENFIELD,
    PRODUCTIVITY_GAIN_LEGACY,
    SAMPLE_ANNUAL_HIRES,
    SAMPLE_ORG_EMPLOYEES,
    SAMPLE_LOADED_COST_PER_FTE,
    TIME_PER_TOUCH_REDUCTION_PCT,
    TIME_TO_STEADY_STATE_MONTHS,
    TOUCHES_AUTOMATED_PCT,
    WORKDAYS_PER_YEAR,
)


PipelineScenario = Literal["Conservative", "Realistic", "Aggressive"]

# DL-11: 7 DORA archetypes. "Pragmatic Performers" is the default per v3 §4.2.
Archetype = Literal[
    "Foundational Challenges",
    "Legacy Bottleneck",
    "Constrained by Process",
    "High Impact Low Cadence",
    "Stable and Methodical",
    "Pragmatic Performers",
    "Harmonious High-Achievers",
]


__all__ = [
    "PeopleInputs",
    "EngineeringInputs",
    "PortfolioResult",
    "BreakEvenResult",
    "PipelineScenario",
    "Archetype",
]


@dataclass(frozen=True)
class PeopleInputs:
    """Inputs for People Mode — Infrastructure Onboarding workflow.

    Defaults pull ``.value`` from ``roi_calc.constants`` Citations so
    Phase 9 Confidence Audit can trace every input back to its source.
    """

    # Organization (§4.1) — all T1 from sample 10-K disclosure + BLS OEWS May 2024
    employees: int = SAMPLE_ORG_EMPLOYEES.value
    annual_hires: int = SAMPLE_ANNUAL_HIRES.value
    fully_loaded_cost_per_fte: float = SAMPLE_LOADED_COST_PER_FTE.value
    hr_specialist_loaded_hourly: float = HR_SPECIALIST_LOADED_HOURLY.value
    it_specialist_loaded_hourly: float = IT_SPECIALIST_LOADED_HOURLY.value
    manager_loaded_hourly: float = HR_MANAGER_LOADED_HOURLY.value

    # T·T·D primitives (§4.2) — all T5 amber
    onboarding_touches_per_event_baseline: int = ONBOARDING_TOUCHES_PER_EVENT_BASELINE.value
    onboarding_avg_minutes_per_touch_baseline: float = ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE.value
    decision_points_per_event_baseline: int = DECISION_POINTS_PER_EVENT.value
    decision_point_error_cost_avg: float = DECISION_POINT_ERROR_COST.value

    # AI automation (§4.3) — mostly T2, error-rate primitives T5 amber
    touches_automated_pct: float = TOUCHES_AUTOMATED_PCT.value
    time_per_touch_reduction_pct: float = TIME_PER_TOUCH_REDUCTION_PCT.value
    decision_point_error_rate_baseline: float = DP_ERROR_RATE_BASELINE.value
    decision_point_error_rate_with_ai: float = DP_ERROR_RATE_WITH_AI.value

    # J-Curve timing (§4.4) — all T5 amber.
    # NOTE: spec §4.4 also lists ``discount_rate_annual = 0.10`` but DL-17 drops
    # it for v1 (orphan field — no §5/§6 function references it; v2 backlog).
    learning_curve_months: int = LEARNING_CURVE_MONTHS.value
    time_to_steady_state_months: int = TIME_TO_STEADY_STATE_MONTHS.value
    horizon_months: int = HORIZON_MONTHS.value

    # Capability multipliers (§4.5) — decorative under Option D (DL-8 / DL-24).
    # Phase 9 ``compute_*_multiplier`` returns 1.0× in v1; Day-90 calibration
    # replaces with org-measured baselines. No Citation default — these are
    # user-controlled inputs with neutral starting values.
    training_spend_ppt: float = 1.0
    manager_support_score: int = 3

    # Scenario (DL-19) — drives risk-tile display only; portfolio total
    # hardcodes Conservative per spec §5.6.
    pipeline_scenario: PipelineScenario = "Conservative"


@dataclass(frozen=True)
class EngineeringInputs:
    """Engineering Mode inputs — DORA J-Curve + instability tax + capability radar.

    Phase 4 (Option B per DL-14): structural shell ships at deploy time.
    Instability tax + default J-Curve render with REAL numbers. Archetype +
    capability multiplier-derived dollar values render as "v3-calibration
    pending" annotations rather than dollar figures (per ``engineering_engine.py``
    ``engineering_portfolio``).

    Defaults that reproduce DORA's $344K instability tax exactly:
      ``cfr_before=0.05``, ``cfr_after=0.06``, ``deploys_per_year=100``,
      ``incident_cost=344_000`` → 0.01 × 100 × $344,000 = $344,000.
    """

    # DORA J-Curve + instability tax
    engineers: int = 300  # T5 calibrated, industry peer benchmark
    cfr_before: float = 0.05  # T2 DORA 2026 sample
    cfr_after: float = 0.06  # T2 DORA 2026 sample
    deploys_per_year: int = DEPLOYS_PER_YEAR_DORA.value  # T5 (DL-9)
    incident_cost: float = INCIDENT_COST_DORA.value  # T5 (DL-10 / Phase 14 A2 — DORA calculator output reproduced; see constants.py)

    # METR self-report discount (T5; v3 §4.3)
    self_report_discount: float = METR_SELF_REPORT_DISCOUNT.value

    # 7 DORA archetypes (DL-11); default per v3 §4.2
    archetype: Archetype = "Pragmatic Performers"

    # 7 DORA capability scores (1-5 ints). Decorative under Option B (DL-14):
    # compute_capability_multiplier returns 1.0 in v1; v3 calibrations replace.
    # Defaults from v3 §4.8 (clear_ai_stance=3, etc.).
    clear_ai_stance: int = 3
    healthy_data_ecosystem: int = 2
    ai_accessible_data: int = 2
    version_control: int = 4
    small_batches: int = 3
    user_centric_focus: int = 3  # DL-13: ≤ 2 triggers value-attenuation gate
    quality_platform: int = 3

    # v3 §5.1 productivity-formula inputs (Phase 14 Stream B2 / DL-29).
    # Fully-loaded engineering FTE cost — uses People-side anchor (sample 10-K
    # personnel cost / consolidated headcount) since regulated lenders typically don't disclose
    # engineering-specific compensation.
    fully_loaded_cost_per_fte: float = SAMPLE_LOADED_COST_PER_FTE.value
    ai_adoption_pct: float = AI_ADOPTION_PCT.value
    ai_hours_per_workday: float = AI_HOURS_PER_WORKDAY.value
    productivity_gain_greenfield: float = PRODUCTIVITY_GAIN_GREENFIELD.value
    productivity_gain_legacy: float = PRODUCTIVITY_GAIN_LEGACY.value
    pct_work_greenfield: float = PCT_WORK_GREENFIELD.value
    engineering_verification_tax: float = ENGINEERING_VERIFICATION_TAX.value
    workdays_per_year: int = WORKDAYS_PER_YEAR.value


@dataclass(frozen=True)
class PortfolioResult:
    """Output of ``people_mode_portfolio`` (Phase 3) and Engineering equivalent.

    Spec §5.6 returns a dict; DL-7 switches to a typed frozen dataclass for
    composability with the break-even chart and tests.

    **Gate 10:** no ``compensation_multiple`` field. No $145K comparison anywhere
    in engine output. ``test_portfolio_result_no_compensation_multiple_field``
    is the regression guard.
    """

    gross_savings_after_verification_tax: float
    risk_costs: float
    net_annual_value: float


@dataclass(frozen=True)
class BreakEvenResult:
    """Output of ``cumulative_cost_vs_savings`` (Phase 3) for the break-even chart.

    ``breakeven_month`` is ``None`` if savings never cross cost within ``horizon_months``.

    Sequence fields are ``tuple``, not ``list`` — ``frozen=True`` only blocks
    attribute reassignment, not in-place mutation of mutable containers.
    Phase 3 builds the series with lists internally then passes ``tuple(...)``
    to the constructor; downstream readers (Phase 7 charts) get a truly
    immutable snapshot.
    """

    months: tuple[int, ...] = field(default_factory=tuple)
    cumulative_cost: tuple[float, ...] = field(default_factory=tuple)
    cumulative_savings: tuple[float, ...] = field(default_factory=tuple)
    breakeven_month: int | None = None

    def __post_init__(self) -> None:
        # Python doesn't enforce type annotations at runtime — a caller passing
        # ``list`` for a ``tuple`` field gets a mutable BreakEvenResult silently.
        # Normalize at construction so Phase 3's loop-built lists become tuples
        # automatically, and Phase 7 chart code can't corrupt the snapshot.
        # ``object.__setattr__`` is required because ``frozen=True`` blocks
        # direct attribute assignment.
        if not isinstance(self.months, tuple):
            object.__setattr__(self, "months", tuple(self.months))
        if not isinstance(self.cumulative_cost, tuple):
            object.__setattr__(self, "cumulative_cost", tuple(self.cumulative_cost))
        if not isinstance(self.cumulative_savings, tuple):
            object.__setattr__(self, "cumulative_savings", tuple(self.cumulative_savings))
