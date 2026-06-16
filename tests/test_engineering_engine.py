"""Phase 4 tests — Engineering Mode engine (Option B per DL-14).

The headline gate: ``instability_tax`` reproduces DORA's $344K exactly with
DL-9/DL-10 defaults. Capability + archetype multipliers ship as decorative
1.0 wrappers; user-centric gate is real.
"""

from __future__ import annotations

import pytest

from roi_calc.constants import (
    DEPLOYS_PER_YEAR_DORA,
    INCIDENT_COST_DORA,
    METR_SELF_REPORT_DISCOUNT,
)
from roi_calc.engineering_engine import (
    EngineeringPortfolioResult,
    apply_user_centric_gate,
    compute_archetype_multiplier,
    compute_capability_multiplier,
    engineering_annual_value,
    engineering_cumulative_cost_vs_savings,
    engineering_portfolio,
    instability_tax,
    user_centric_gate_active,
)
from roi_calc.models import BreakEvenResult
from roi_calc.models import Archetype, EngineeringInputs


# ---------------------------------------------------------------------------
# Hard gate: $344K reproduction
# ---------------------------------------------------------------------------

def test_instability_tax_reproduces_344k_with_dl9_defaults() -> None:
    """T2 anchor: DL-9/10 defaults reproduce DORA $344K EXACTLY.
    0.01 × 100 × $344,000 = $344,000.

    NOTE: float precision — `(0.06 - 0.05) × 100 × 344_000` computes to
    343999.99999999983 in IEEE-754, not 344000.0 exactly. ``abs=1e-3`` is the
    correct tolerance (under a tenth of a cent, far below DORA's reporting precision).
    """
    result = instability_tax(
        cfr_before=0.05,
        cfr_after=0.06,
        deployments_per_year=100,
        incident_cost=344_000,
    )
    assert result == pytest.approx(344_000.0, abs=1e-3)


def test_instability_tax_reproduces_344k_within_1k_handoff_alternate() -> None:
    """Handoff alternate form: 2400 deploys × $14,333 incident.
    0.01 × 2400 × $14,333 = $343,992 — within $1K of DORA's stated $344K."""
    result = instability_tax(
        cfr_before=0.05,
        cfr_after=0.06,
        deployments_per_year=2400,
        incident_cost=14_333,
    )
    assert 343_000 <= result <= 345_000


def test_instability_tax_uses_engineering_inputs_defaults() -> None:
    """EngineeringInputs() defaults must produce the $344K reproduction."""
    inp = EngineeringInputs()
    result = instability_tax(
        cfr_before=inp.cfr_before,
        cfr_after=inp.cfr_after,
        deployments_per_year=inp.deploys_per_year,
        incident_cost=inp.incident_cost,
    )
    assert result == pytest.approx(344_000, abs=1_000)


def test_instability_tax_is_zero_when_cfr_unchanged() -> None:
    result = instability_tax(0.05, 0.05, 100, 344_000)
    assert result == 0.0


def test_instability_tax_is_negative_when_ai_reduces_cfr() -> None:
    """If AI deployments REDUCE the change failure rate, the tax goes negative —
    a credit, not a charge. Phase 10 Results tab renders this case if it occurs."""
    result = instability_tax(0.06, 0.05, 100, 344_000)
    assert result == pytest.approx(-344_000.0, abs=1e-3)


# ---------------------------------------------------------------------------
# Capability + archetype multipliers — decorative-only (Option B per DL-14)
# ---------------------------------------------------------------------------

def test_compute_capability_multiplier_is_1_in_v1() -> None:
    """DL-14 Option B: capability weights are v3-pending; v1 wrapper returns 1.0."""
    assert compute_capability_multiplier({"clear_ai_stance": 3, "healthy_data_ecosystem": 2}) == 1.0
    assert compute_capability_multiplier({}) == 1.0
    # Even at maximum scores, still decorative
    max_scores = {k: 5 for k in (
        "clear_ai_stance", "healthy_data_ecosystem", "ai_accessible_data",
        "version_control", "small_batches", "user_centric_focus", "quality_platform"
    )}
    assert compute_capability_multiplier(max_scores) == 1.0


def test_compute_archetype_multiplier_is_1_in_v1_for_every_archetype() -> None:
    """DL-14 Option B: archetype multipliers are v3-pending."""
    for archetype in (
        "Foundational Challenges",
        "Legacy Bottleneck",
        "Constrained by Process",
        "High Impact Low Cadence",
        "Stable and Methodical",
        "Pragmatic Performers",
        "Harmonious High-Achievers",
    ):
        assert compute_archetype_multiplier(archetype) == 1.0, (  # type: ignore[arg-type]
            f"Archetype {archetype!r} multiplier must be 1.0 in v1 (DL-14)"
        )


# ---------------------------------------------------------------------------
# User-centric focus gate — REAL (DL-13)
# ---------------------------------------------------------------------------

def test_user_centric_gate_zeros_multiplier_when_score_le_2() -> None:
    """DL-13: DORA 2025 finding — score ≤ 2 zeros AI value."""
    assert apply_user_centric_gate(1, 1.0) == 0.0
    assert apply_user_centric_gate(2, 1.5) == 0.0


def test_user_centric_gate_preserves_multiplier_when_score_gt_2() -> None:
    assert apply_user_centric_gate(3, 1.0) == 1.0
    assert apply_user_centric_gate(4, 1.25) == 1.25
    assert apply_user_centric_gate(5, 1.0) == 1.0


def test_user_centric_gate_raises_on_out_of_range_score() -> None:
    """Score range per v3 §4.8 is 1–5. Out-of-range fails loudly so Phase 6
    slider misconfiguration is caught at the engine layer, not silently passed."""
    with pytest.raises(ValueError, match="must be in 1..5"):
        apply_user_centric_gate(0, 1.0)
    with pytest.raises(ValueError, match="must be in 1..5"):
        apply_user_centric_gate(6, 1.0)
    with pytest.raises(ValueError, match="must be in 1..5"):
        apply_user_centric_gate(-1, 1.0)


def test_user_centric_gate_rejects_non_int_score() -> None:
    """Spec scale is integer 1-5. A float (e.g. 2.5 from a misconfigured slider
    with float step) would pass `1 <= 2.5 <= 5` silently and produce gate=False.
    Reject non-int types at the type-validator step.

    `bool` is rejected explicitly even though isinstance(True, int) is True."""
    with pytest.raises(TypeError, match="must be int"):
        apply_user_centric_gate(2.5, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must be int"):
        apply_user_centric_gate(True, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must be int"):
        apply_user_centric_gate("3", 1.0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# user_centric_gate_active — single-source predicate; both apply_user_centric_gate
# and engineering_portfolio delegate threshold checks to this function so the
# DL-13 threshold lives in exactly one place
# ---------------------------------------------------------------------------

def test_user_centric_gate_active_returns_true_at_score_1_and_2() -> None:
    assert user_centric_gate_active(1) is True
    assert user_centric_gate_active(2) is True


def test_user_centric_gate_active_returns_false_at_score_3_through_5() -> None:
    assert user_centric_gate_active(3) is False
    assert user_centric_gate_active(4) is False
    assert user_centric_gate_active(5) is False


def test_user_centric_gate_active_validates_input() -> None:
    """Same input discipline as apply_user_centric_gate (shares the validator)."""
    with pytest.raises(ValueError, match="must be in 1..5"):
        user_centric_gate_active(0)
    with pytest.raises(TypeError, match="must be int"):
        user_centric_gate_active(2.5)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Engineering portfolio (Option B composition)
# ---------------------------------------------------------------------------

def test_engineering_portfolio_returns_dataclass() -> None:
    result = engineering_portfolio(EngineeringInputs())
    assert isinstance(result, EngineeringPortfolioResult)


def test_engineering_portfolio_result_is_frozen() -> None:
    """Same frozen-dataclass discipline as PeopleInputs / PortfolioResult / BreakEvenResult."""
    from dataclasses import FrozenInstanceError
    result = engineering_portfolio(EngineeringInputs())
    with pytest.raises(FrozenInstanceError):
        result.instability_tax_annual = 999.0  # type: ignore[misc]


def test_engineering_portfolio_result_post_init_rejects_bad_sentinel() -> None:
    """The two ``*_status`` fields are Literal['v3-calibration pending'] but Python
    doesn't enforce Literal at runtime — __post_init__ enforces it explicitly so
    Phase 10 UI grep can rely on the exact sentinel string."""
    with pytest.raises(ValueError, match="archetype_adjusted_status"):
        EngineeringPortfolioResult(
            instability_tax_annual=0.0,
            archetype_adjusted_status="something else",  # type: ignore[arg-type]
            capability_adjusted_status="v3-calibration pending",
            user_centric_gate_triggered=False,
        )
    with pytest.raises(ValueError, match="capability_adjusted_status"):
        EngineeringPortfolioResult(
            instability_tax_annual=0.0,
            archetype_adjusted_status="v3-calibration pending",
            capability_adjusted_status="oops",  # type: ignore[arg-type]
            user_centric_gate_triggered=False,
        )


def test_engineering_portfolio_instability_tax_negative_when_cfr_improves() -> None:
    """Portfolio-level coverage: when AI reduces CFR (cfr_after < cfr_before),
    instability tax is negative — a credit. Phase 10 Results tab should render
    the credit case correctly."""
    inp = EngineeringInputs(cfr_before=0.06, cfr_after=0.05)
    result = engineering_portfolio(inp)
    assert result.instability_tax_annual == pytest.approx(-344_000, abs=1_000)


def test_engineering_portfolio_instability_tax_is_344k_at_defaults() -> None:
    """End-to-end: portfolio at sample defaults / DORA-sample defaults shows the $344K reproduction."""
    result = engineering_portfolio(EngineeringInputs())
    assert result.instability_tax_annual == pytest.approx(344_000, abs=1_000)


def test_engineering_portfolio_multiplier_statuses_are_v3_pending() -> None:
    """DL-14: archetype + capability dollar values must NOT be computed in v1.
    They render as the ``v3-calibration pending`` sentinel string."""
    result = engineering_portfolio(EngineeringInputs())
    assert result.archetype_adjusted_status == "v3-calibration pending"
    assert result.capability_adjusted_status == "v3-calibration pending"


def test_engineering_portfolio_user_centric_gate_not_triggered_at_default_score_3() -> None:
    result = engineering_portfolio(EngineeringInputs())  # user_centric_focus=3
    assert result.user_centric_gate_triggered is False


def test_engineering_portfolio_user_centric_gate_triggers_at_score_2() -> None:
    """Phase 10 Assessment radar paints user_centric_focus axis red when this flips."""
    inp = EngineeringInputs(user_centric_focus=2)
    result = engineering_portfolio(inp)
    assert result.user_centric_gate_triggered is True


def test_engineering_portfolio_user_centric_gate_triggers_at_score_1() -> None:
    inp = EngineeringInputs(user_centric_focus=1)
    result = engineering_portfolio(inp)
    assert result.user_centric_gate_triggered is True


# ---------------------------------------------------------------------------
# EngineeringInputs Phase 4 expansion (was 3 fields → now full set)
# ---------------------------------------------------------------------------

def test_engineering_inputs_has_dora_sample_defaults() -> None:
    inp = EngineeringInputs()
    assert inp.deploys_per_year == 100
    assert inp.incident_cost == 344_000
    assert inp.self_report_discount == 0.50
    assert inp.archetype == "Pragmatic Performers"


def test_engineering_inputs_capability_score_defaults() -> None:
    inp = EngineeringInputs()
    assert inp.clear_ai_stance == 3
    assert inp.healthy_data_ecosystem == 2
    assert inp.ai_accessible_data == 2
    assert inp.version_control == 4
    assert inp.small_batches == 3
    assert inp.user_centric_focus == 3
    assert inp.quality_platform == 3


def test_engineering_inputs_capability_defaults_source_from_constants() -> None:
    """The three Engineering-Mode Citation-sourced defaults must equal their Citation values."""
    inp = EngineeringInputs()
    assert inp.deploys_per_year == DEPLOYS_PER_YEAR_DORA.value
    assert inp.incident_cost == INCIDENT_COST_DORA.value
    assert inp.self_report_discount == METR_SELF_REPORT_DISCOUNT.value


# ---------------------------------------------------------------------------
# Gate 10 mirror on Engineering Mode output
# ---------------------------------------------------------------------------

def test_gate10_engineering_portfolio_result_no_compensation_fields() -> None:
    """Gate 10: no $145K comparison anywhere in engine output, Engineering Mode included."""
    from dataclasses import fields
    field_names = {f.name for f in fields(EngineeringPortfolioResult)}
    for name in field_names:
        lname = name.lower()
        assert "compensation" not in lname
        assert "comp" not in lname
        assert "salary" not in lname
        assert "145" not in name


# ---------------------------------------------------------------------------
# Stream B2 — engineering_annual_value (v3 §5.1 productivity formula, DL-29)
# ---------------------------------------------------------------------------

def test_engineering_annual_value_pinned_at_prog_defaults() -> None:
    """Pinned regression: at sample defaults the v3 §5.1 productivity formula
    plus instability tax subtracts to ~$199,682. Formula:
      raw_gain = 0.30×0.375 + 0.70×0.10 = 0.1825
      effective_gain = 0.1825 × 0.50 × 0.85 = 0.07756
      adopting = 300 × 0.75 = 225
      hours/yr = 2 × 235 × 0.07756 = 36.45
      hourly = 124,615 / 1,880 = 66.28
      gross = 225 × 36.45 × 66.28 = 543,682
      net   = 543,682 − 344,000 = 199,682
    """
    result = engineering_annual_value(EngineeringInputs())
    assert result == pytest.approx(199_682, abs=500)


def test_engineering_annual_value_plausible_range_at_prog_defaults() -> None:
    """Sanity bound: net annual value sits inside a plausibly defensible band.
    Upper bound derivation: v3 §5.1 publishes $400K–$1.5M for **gross**;
    net = gross − $344K instability tax → net ceiling ≈ $1.156M. We round
    up to $1.2M so the bound stays a sanity check, not a too-tight pin
    that breaks on minor parameter drift.
    Lower bound $100K catches the negative / near-zero regression class.
    """
    result = engineering_annual_value(EngineeringInputs())
    assert 100_000 <= result <= 1_200_000


def test_engineering_annual_value_gross_in_v3_section_5_1_spec_range() -> None:
    """v3 §5.1 publishes a $400K–$1.5M range for the **gross** productivity
    value (before instability tax). At sample defaults: gross = net + tax ≈
    $199,682 + $344,000 = $543,682, which sits inside the spec band.

    Caveat — this is a **band sanity check**, not an independent
    formula-correctness assertion. The formula itself is verified by
    ``test_engineering_annual_value_subtracts_instability_tax`` (which
    reconstructs gross from first principles and confirms self_report_discount
    and engineering_verification_tax are actually applied). The band test
    catches: (a) the formula breaking such that gross collapses to zero
    or balloons past $1.5M, and (b) spec-range regressions if v3 publishes
    a revised band.

    DL-14 divergence note: the spec's illustrative hand-calc at v3 §5.1
    uses ``capability_multiplier ≈ 0.875`` and produces gross ≈ $477K.
    The engine ships Option B with capability_multiplier = 1.0
    (decorative wrapper, calibration is Day-90 work), producing gross ≈ $543K.
    Both values sit inside the $400K–$1.5M spec band; the divergence is
    intentional and surfaced via the ``"v3-calibration pending"`` annotation
    on the multiplier-derived portfolio path.

    Net is below the band by design — the $344K instability tax is structural.
    """
    inp = EngineeringInputs()
    net = engineering_annual_value(inp)
    tax = instability_tax(
        cfr_before=inp.cfr_before,
        cfr_after=inp.cfr_after,
        deployments_per_year=inp.deploys_per_year,
        incident_cost=inp.incident_cost,
    )
    gross = net + tax
    assert 400_000 <= gross <= 1_500_000, (
        f"gross annual productivity value ${gross:,.0f} outside v3 §5.1 "
        f"published range $400K–$1.5M (net ${net:,.0f} + tax ${tax:,.0f})"
    )


def test_engineering_annual_value_workdays_per_year_cancellation_invariance() -> None:
    """Phase 14 cascade-fix: hourly_cost is now derived from
    ``inputs.workdays_per_year × 8`` at runtime (was hardcoded 1,880).
    Because workdays_per_year appears in BOTH the hours-saved numerator
    and the hourly-cost denominator, it cancels mathematically — the
    gross productivity value is invariant under workdays_per_year.

    This invariance IS the consistency guarantee: before the fix, the
    numerator used the user-edited value and the denominator was pinned
    to 1,880, creating math drift for non-default workdays. After the
    fix, both terms agree on whatever workdays value is used, so the
    output is stable across user edits.
    """
    default = engineering_annual_value(EngineeringInputs())
    low = engineering_annual_value(EngineeringInputs(workdays_per_year=200))
    high = engineering_annual_value(EngineeringInputs(workdays_per_year=260))
    assert default == pytest.approx(low, abs=1e-6)
    assert default == pytest.approx(high, abs=1e-6)


def test_engineering_annual_value_subtracts_instability_tax() -> None:
    """The formula must net the $344K instability tax — annual_net + tax == gross.
    Reconstruct gross from the inputs and confirm.
    """
    inp = EngineeringInputs()
    raw_gain = (
        inp.pct_work_greenfield * inp.productivity_gain_greenfield
        + (1.0 - inp.pct_work_greenfield) * inp.productivity_gain_legacy
    )
    effective_gain = raw_gain * inp.self_report_discount * (1.0 - inp.engineering_verification_tax)
    adopting = inp.engineers * inp.ai_adoption_pct
    hours_saved = inp.ai_hours_per_workday * inp.workdays_per_year * effective_gain
    # Pass-3 cascade fix: engine now derives hourly_cost from
    # `inputs.workdays_per_year × 8` (was hardcoded 1,880). Reconstruct using
    # the same formula so this test exercises the post-fix derivation, not the
    # stale constant.
    hourly_cost = inp.fully_loaded_cost_per_fte / (inp.workdays_per_year * 8)
    gross = adopting * hours_saved * hourly_cost

    net = engineering_annual_value(inp)
    tax = instability_tax(inp.cfr_before, inp.cfr_after, inp.deploys_per_year, inp.incident_cost)
    assert net == pytest.approx(gross - tax, abs=1e-3)
    assert tax == pytest.approx(344_000, abs=1e-3)


def test_engineering_annual_value_decorative_multipliers_unchanged() -> None:
    """DL-14 / DL-8 regression: the v3 §5.1 productivity formula MUST NOT
    fold capability or archetype multipliers into the annual value. They
    remain decorative wrappers returning 1.0 in v1; Day-90 calibration
    replaces them. This test guards against accidental multiplier coupling
    that would invalidate the 'v3-calibration pending' annotations.
    """
    assert compute_capability_multiplier({"clear_ai_stance": 5}) == 1.0
    assert compute_archetype_multiplier("Harmonious High-Achievers") == 1.0
    # Doubling either "multiplier" through the function still has no effect
    # because they're never called inside engineering_annual_value.
    inp1 = EngineeringInputs()
    inp2 = EngineeringInputs(clear_ai_stance=5, archetype="Harmonious High-Achievers")
    assert engineering_annual_value(inp1) == pytest.approx(engineering_annual_value(inp2), abs=1e-3)


def test_engineering_annual_value_scales_with_engineer_count() -> None:
    """Linear scaling check — doubling engineers approximately doubles gross,
    so net + tax must approximately double too (instability tax is invariant
    in engineers count by design — DORA's deploys/incident structure)."""
    inp_low = EngineeringInputs(engineers=150)
    inp_high = EngineeringInputs(engineers=300)
    tax = instability_tax(inp_low.cfr_before, inp_low.cfr_after, inp_low.deploys_per_year, inp_low.incident_cost)
    gross_low = engineering_annual_value(inp_low) + tax
    gross_high = engineering_annual_value(inp_high) + tax
    assert gross_high == pytest.approx(2 * gross_low, rel=1e-6)


def test_engineering_annual_value_zero_adoption_yields_negative_tax_only() -> None:
    """Edge: ai_adoption_pct=0 → no adopters → gross=0 → net = -instability_tax."""
    inp = EngineeringInputs(ai_adoption_pct=0.0)
    result = engineering_annual_value(inp)
    assert result == pytest.approx(-344_000, abs=1e-3)


# ---------------------------------------------------------------------------
# Stream B3 — engineering_cumulative_cost_vs_savings (shared DL-28 core)
# ---------------------------------------------------------------------------

def test_engineering_break_even_returns_break_even_result() -> None:
    """Type + shape contract — must return a BreakEvenResult with horizon-length series."""
    result = engineering_cumulative_cost_vs_savings(EngineeringInputs())
    assert isinstance(result, BreakEvenResult)
    assert len(result.months) == 24
    assert len(result.cumulative_cost) == 24
    assert len(result.cumulative_savings) == 24


def test_engineering_break_even_breakeven_within_horizon_at_prog_defaults() -> None:
    """At v3 §5.1 defaults Engineering Mode reaches breakeven inside the 24-month horizon."""
    result = engineering_cumulative_cost_vs_savings(EngineeringInputs())
    assert result.breakeven_month is not None
    assert 1 <= result.breakeven_month <= 24


def test_engineering_break_even_uses_engineers_not_employees_for_cost_base() -> None:
    """B3 contract: implementation cost is engineers × per-employee rate, NOT
    employees. Pin via month-1 cost = engineers×$50 + engineers×$30/12.
    At default engineers=300 → setup $15,000 + monthly recurring $750 = $15,750.
    """
    inp = EngineeringInputs()
    result = engineering_cumulative_cost_vs_savings(inp)
    expected_m1 = inp.engineers * 50 + inp.engineers * 30 / 12
    assert result.cumulative_cost[0] == pytest.approx(expected_m1, abs=1e-3)
    # And at horizon: total cost = setup + 24 months recurring
    expected_m24 = inp.engineers * 50 + inp.engineers * 30 * 2  # 2 years recurring
    assert result.cumulative_cost[23] == pytest.approx(expected_m24, abs=1e-3)


def test_engineering_break_even_savings_derive_from_annual_value() -> None:
    """The cumulative-savings series must reflect engineering_annual_value/12 monthly
    at steady-state (ramp=1.0). Pin via the month-13 delta — first month past steady."""
    inp = EngineeringInputs()
    result = engineering_cumulative_cost_vs_savings(inp)
    monthly_net = engineering_annual_value(inp) / 12
    m13_delta = result.cumulative_savings[12] - result.cumulative_savings[11]
    # Month 13: ramp == 1.0 (past steady)
    assert m13_delta == pytest.approx(monthly_net, abs=1e-3)


def test_engineering_break_even_pinned_at_prog_defaults() -> None:
    """Pinned regression for the integrated Engineering J-Curve:
      annual_net ≈ $199,682
      one-time setup = 300 × $50 = $15,000
      annual recurring = 300 × $30 = $9,000 (monthly $750)
      cumulative cost at M24 = $15,000 + 24 × $750 = $33,000
      breakeven month ≈ 6 (savings overtake the small setup cost early)
    """
    result = engineering_cumulative_cost_vs_savings(EngineeringInputs())
    assert result.cumulative_cost[23] == pytest.approx(33_000, abs=1)
    assert result.breakeven_month == 6


def test_engineering_break_even_negative_annual_net_yields_no_breakeven() -> None:
    """If gross productivity gain < $344K instability tax, annual_net is
    negative and savings never overtake cost. Force this via ai_adoption_pct=0."""
    inp = EngineeringInputs(ai_adoption_pct=0.0)
    result = engineering_cumulative_cost_vs_savings(inp)
    # All months: monthly_net = -344K/12 ≈ -$28,667; savings series goes negative
    # and never crosses the (positive) cost series.
    assert result.breakeven_month is None
    assert result.cumulative_savings[23] < 0
    assert result.cumulative_cost[23] > 0


def test_engineering_inputs_v3_section_5_1_defaults_source_from_constants() -> None:
    """v3 §5.1 productivity-formula defaults must trace back to the Citation values."""
    from roi_calc.constants import (
        AI_ADOPTION_PCT,
        AI_HOURS_PER_WORKDAY,
        ENGINEERING_VERIFICATION_TAX,
        PCT_WORK_GREENFIELD,
        PRODUCTIVITY_GAIN_GREENFIELD,
        PRODUCTIVITY_GAIN_LEGACY,
        WORKDAYS_PER_YEAR,
    )
    inp = EngineeringInputs()
    assert inp.ai_adoption_pct == AI_ADOPTION_PCT.value
    assert inp.ai_hours_per_workday == AI_HOURS_PER_WORKDAY.value
    assert inp.productivity_gain_greenfield == PRODUCTIVITY_GAIN_GREENFIELD.value
    assert inp.productivity_gain_legacy == PRODUCTIVITY_GAIN_LEGACY.value
    assert inp.pct_work_greenfield == PCT_WORK_GREENFIELD.value
    assert inp.engineering_verification_tax == ENGINEERING_VERIFICATION_TAX.value
    assert inp.workdays_per_year == WORKDAYS_PER_YEAR.value
