"""Tornado sensitivity data for both modes (Phase 5).

Generates per-field sensitivity by varying each input ±variation and recomputing
the portfolio net via the supplied ``engine_fn``. Returns top-N bars by absolute
swing magnitude.

DL-19 / DL-22 / Cascade 8 sibling: orphan fields (those with no engine effect
in v1 — ``training_spend_ppt`` and ``manager_support_score`` under Option D)
are flagged ``is_orphan=True`` so Phase 8 tornado chart can render them as
gray bars with "wires in Phase 9" annotation. Honest > clean.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Any, Callable

from roi_calc.models import EngineeringInputs, PeopleInputs


__all__ = ["TornadoBar", "tornado_for_people", "tornado_for_engineering"]


# Explicit 1-5 scale fields (DORA / DL-13). Listed by name rather than detected
# by `1 <= value <= 5` heuristic so count-ints (e.g. `learning_curve_months=4`)
# don't accidentally get the ±1 clamp treatment.
_SCALE_1_5_FIELDS = frozenset(
    {
        "manager_support_score",
        # 7 DORA capability scores
        "clear_ai_stance",
        "healthy_data_ecosystem",
        "ai_accessible_data",
        "version_control",
        "small_batches",
        "user_centric_focus",
        "quality_platform",
    }
)

# Orphan fields per DL-19 / Cascade 8 sibling:
#   * ``training_spend_ppt`` — Option D decorative; Phase 9 capability wrapper returns 1.0
#   * ``manager_support_score`` — Option D decorative; same
#   * ``pipeline_scenario`` — DL-19 drives risk-tile + tornado only, NOT portfolio total,
#     so varying it shows zero swing on the portfolio engine; rendered as orphan.
_PEOPLE_ORPHAN_FIELDS = frozenset(
    {"training_spend_ppt", "manager_support_score", "pipeline_scenario"}
)

# Engineering Mode orphans under Option B (DL-14):
#   * The 7 capability scores + archetype contribute via decorative multipliers
#     (return 1.0). Zero swing on portfolio.instability_tax_annual in v1.
#   * The 8 v3 §5.1 productivity-formula fields (engineers, ai_adoption_pct,
#     hours/day, gain_greenfield, gain_legacy, pct_greenfield, verification_tax,
#     workdays_per_year, fully_loaded_cost_per_fte, self_report_discount)
#     drive `engineering_annual_value` but NOT the `engineering_portfolio.
#     instability_tax_annual` metric the tornado measures. Marked as orphan
#     here so they render gray instead of stealing top_n=10 slots with
#     zero-swing bars. Day-90 / v2: switch the Engineering tornado metric to
#     engineering_annual_value to surface true productivity-formula sensitivity.
_ENGINEERING_ORPHAN_FIELDS = frozenset(
    {
        # Decorative capability multipliers (Option B / DL-14)
        "clear_ai_stance",
        "healthy_data_ecosystem",
        "ai_accessible_data",
        "version_control",
        "small_batches",
        "user_centric_focus",
        "quality_platform",
        "archetype",
        # v3 §5.1 productivity-formula fields — affect engineering_annual_value,
        # NOT the instability_tax_annual metric this tornado graphs.
        "self_report_discount",
        "engineers",
        "fully_loaded_cost_per_fte",
        "ai_adoption_pct",
        "ai_hours_per_workday",
        "productivity_gain_greenfield",
        "productivity_gain_legacy",
        "pct_work_greenfield",
        "engineering_verification_tax",
        "workdays_per_year",  # also cancels mathematically in gross product
    }
)

# Phase 8 performance note: each ``tornado_for_*`` call invokes ``engine_fn``
# 2× per numeric field (≈26 calls for PeopleInputs, ≈22 for EngineeringInputs).
# At Streamlit slider cadence wrap the engine in ``functools.lru_cache`` or
# ``@st.cache_data`` to avoid recomputing on every slider tick.


@dataclass(frozen=True)
class TornadoBar:
    """One row in the tornado chart.

    ``swing`` is ``high - low`` (signed). Phase 8 sorts by ``abs(swing)``.
    ``is_orphan`` flags fields with zero engine effect in v1 — rendered gray
    with a "wires in Phase 9" annotation per DL-19.
    """

    field_name: str
    low_value_output: float
    high_value_output: float
    swing: float
    is_orphan: bool = False


def _vary_numeric_field(
    inputs: Any,
    field_name: str,
    variation: float,
) -> tuple[Any, Any] | None:
    """Return (low_inputs, high_inputs) with one numeric field varied; None if non-numeric.

    Variation rules:
      * float fields: ±variation. If current value is in [0, 1] (rate / probability),
        the high side is clamped to 1.0 so we never invent out-of-domain values
        like a 110% automation rate.
      * int fields in ``_SCALE_1_5_FIELDS``: ±1 clamped to [1, 5]
      * other int fields (counts): ±variation rounded; low clamped to 0
    """
    current = getattr(inputs, field_name)
    if isinstance(current, bool) or not isinstance(current, (int, float)):
        return None

    if isinstance(current, float):
        low = current * (1 - variation)
        high = current * (1 + variation)
        # Rate/probability clamp: any float in [0, 1] stays in [0, 1] post-variation
        if 0 <= current <= 1:
            low = max(0.0, low)
            high = min(1.0, high)
    elif isinstance(current, int):
        if field_name in _SCALE_1_5_FIELDS:
            low = max(1, current - 1)
            high = min(5, current + 1)
        else:
            low = max(0, int(round(current * (1 - variation))))
            high = int(round(current * (1 + variation)))
    else:
        return None

    return replace(inputs, **{field_name: low}), replace(inputs, **{field_name: high})


def _tornado_for(
    inputs: Any,
    engine_fn: Callable[[Any], Any],
    orphan_fields: frozenset[str],
    variation: float,
    top_n: int,
) -> list[TornadoBar]:
    """Generic tornado generator. ``engine_fn(inputs) -> result`` must produce
    an object with a ``.net_annual_value`` (PortfolioResult) or
    ``.instability_tax_annual`` (EngineeringPortfolioResult) attribute.

    Numeric fields → vary ±variation. String fields in the orphan set →
    emit a zero-swing orphan bar so DL-19's honest-display contract is met
    even for non-numeric inputs like ``pipeline_scenario`` (whose effect on
    the portfolio total is zero by design per spec §5.6 hardcode).
    """
    if not is_dataclass(inputs):
        raise TypeError(f"inputs must be a dataclass, got {type(inputs).__name__}")
    if top_n < 1:
        raise ValueError(f"top_n must be ≥ 1, got {top_n}")

    # Compute the baseline output once so string-orphan bars can record a
    # meaningful "no-effect" snapshot.
    baseline_output = _extract_metric(engine_fn(inputs))

    bars: list[TornadoBar] = []
    for f in fields(inputs):
        current = getattr(inputs, f.name)

        # String-typed orphan field (e.g. pipeline_scenario, archetype):
        # emit zero-swing orphan bar so it surfaces in the audit despite
        # producing no engine swing.
        if isinstance(current, str) and f.name in orphan_fields:
            bars.append(
                TornadoBar(
                    field_name=f.name,
                    low_value_output=baseline_output,
                    high_value_output=baseline_output,
                    swing=0.0,
                    is_orphan=True,
                )
            )
            continue

        varied = _vary_numeric_field(inputs, f.name, variation)
        if varied is None:
            continue
        low_inputs, high_inputs = varied
        try:
            low_result = engine_fn(low_inputs)
            high_result = engine_fn(high_inputs)
        except (ValueError, TypeError, ZeroDivisionError):
            # Field perturbations that violate engine invariants (e.g.
            # learning_curve_months=0 → ValueError, or a bool slipping through →
            # TypeError) are skipped rather than crashing the whole tornado.
            continue

        low_output = _extract_metric(low_result)
        high_output = _extract_metric(high_result)
        swing = high_output - low_output

        bars.append(
            TornadoBar(
                field_name=f.name,
                low_value_output=low_output,
                high_value_output=high_output,
                swing=swing,
                is_orphan=f.name in orphan_fields,
            )
        )

    # Partition non-orphan from orphan. Slice top_n on non-orphan only — orphan
    # bars ALWAYS pass through regardless of top_n. Honest > clean (DL-19):
    # cutting orphans at top_n=10 silently violates the "wires in P9" contract.
    # Phase 8 chart renders the orphans as gray bars at the bottom.
    non_orphan_bars = [b for b in bars if not b.is_orphan]
    orphan_bars = [b for b in bars if b.is_orphan]
    non_orphan_bars.sort(key=lambda b: abs(b.swing), reverse=True)
    return non_orphan_bars[:top_n] + orphan_bars


def _extract_metric(result: Any) -> float:
    """Pull the headline dollar from either PortfolioResult or EngineeringPortfolioResult."""
    if hasattr(result, "net_annual_value"):
        return float(result.net_annual_value)
    if hasattr(result, "instability_tax_annual"):
        return float(result.instability_tax_annual)
    raise TypeError(
        f"engine_fn return value has no recognizable metric (need .net_annual_value or "
        f".instability_tax_annual); got {type(result).__name__}"
    )


def tornado_for_people(
    inputs: PeopleInputs,
    engine_fn: Callable[[PeopleInputs], Any] | None = None,
    variation: float = 0.20,
    top_n: int = 10,
) -> list[TornadoBar]:
    """Tornado for People Mode — portfolio.net_annual_value sensitivity."""
    if engine_fn is None:
        from roi_calc.people_engine import people_mode_portfolio  # late import: P5 ↔ P3
        engine_fn = people_mode_portfolio
    return _tornado_for(inputs, engine_fn, _PEOPLE_ORPHAN_FIELDS, variation, top_n)


def tornado_for_engineering(
    inputs: EngineeringInputs,
    engine_fn: Callable[[EngineeringInputs], Any] | None = None,
    variation: float = 0.20,
    top_n: int = 10,
) -> list[TornadoBar]:
    """Tornado for Engineering Mode — instability_tax sensitivity (Option B)."""
    if engine_fn is None:
        from roi_calc.engineering_engine import engineering_portfolio  # late import: P5 ↔ P4
        engine_fn = engineering_portfolio
    return _tornado_for(inputs, engine_fn, _ENGINEERING_ORPHAN_FIELDS, variation, top_n)
