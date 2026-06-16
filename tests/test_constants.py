"""Phase 1 tests — Citation dataclass + every constant + DL regressions.

Cascade regressions guarded here:
  * DL-1  — PIPELINE_PER_REQ == 5 (spec patch from 50)
  * DL-3  — RAMP_FLOOR / IMPLEMENTATION_* lifted from §6.1 inline literals
  * DL-16 — TRAINING_COEFFICIENT absent (EY anchor failed source verification)
  * DL-21 — DROPOUT tiers: Conservative=T1 (RCT), Realistic=T2, Aggressive=T2
  * DL-23 — both SAMPLE_ORG_EMPLOYEES and SAMPLE_ORG_CONSOLIDATED_HEADCOUNT present
  * DL-24 — MANAGER_MULTIPLIER_MAX present as T1 reference (decorative-only per §0.00)
  * Cascade 5 — Citation.value is int | float only (structural, asserted on every Citation)
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from roi_calc import constants
from roi_calc.constants import CITATIONS, Citation


VALID_TIERS = {"T1", "T2", "T3", "T4", "T5"}


def _all_module_citations() -> list[tuple[str, Citation]]:
    """Return every module-level Citation by (name, instance)."""
    return [
        (name, getattr(constants, name))
        for name in dir(constants)
        if isinstance(getattr(constants, name), Citation)
    ]


# ---------------------------------------------------------------------------
# Citation dataclass structural invariants
# ---------------------------------------------------------------------------

def test_citation_is_frozen() -> None:
    c = Citation(value=1.0, source="x", tier="T1")
    with pytest.raises(FrozenInstanceError):
        c.value = 2.0  # type: ignore[misc]


def test_citation_accepts_int_and_float() -> None:
    Citation(value=1, source="x", tier="T1")
    Citation(value=1.0, source="x", tier="T1")


def test_citation_post_init_rejects_non_numeric() -> None:
    """Runtime contract enforcement (added after 3rd adversarial pass): str / dict /
    list / bool values must raise TypeError at construction, not just at test time."""
    with pytest.raises(TypeError, match="must be int or float"):
        Citation(value="0.45", source="x", tier="T1")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must be int or float"):
        Citation(value={"a": 1}, source="x", tier="T1")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must be int or float"):
        Citation(value=[1, 2], source="x", tier="T1")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must be int or float"):
        Citation(value=True, source="x", tier="T1")  # bool excluded despite being int subclass


def test_citation_flag_defaults_to_none() -> None:
    c = Citation(value=1, source="x", tier="T1")
    assert c.flag is None


# ---------------------------------------------------------------------------
# Per-citation invariants (parameterized walk over the module)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,citation", _all_module_citations())
def test_citation_has_nonempty_source(name: str, citation: Citation) -> None:
    assert citation.source.strip(), f"{name}.source is empty"


@pytest.mark.parametrize("name,citation", _all_module_citations())
def test_citation_tier_is_valid(name: str, citation: Citation) -> None:
    assert citation.tier in VALID_TIERS, f"{name}.tier = {citation.tier!r} not in {VALID_TIERS}"


@pytest.mark.parametrize("name,citation", _all_module_citations())
def test_citation_value_is_int_or_float(name: str, citation: Citation) -> None:
    # Cascade 5: no str, no dict, no list — only numeric.
    assert isinstance(citation.value, (int, float)) and not isinstance(citation.value, bool), (
        f"{name}.value type = {type(citation.value).__name__}, must be int|float"
    )


def test_t5_citations_have_amber_flag() -> None:
    offenders = [
        name
        for name, c in _all_module_citations()
        if c.tier == "T5" and not (c.flag and c.flag.strip())
    ]
    assert not offenders, f"T5 citations missing amber flag: {offenders}"


def test_t5_citation_flag_starts_with_warning_emoji() -> None:
    """Phase 9 Confidence Audit + Phase 6 amber_flag_widget key on the ⚠️ prefix.

    A flag like ``flag="amber"`` would pass the empty-string check above but
    silently break the amber-rendering UI heuristic.
    """
    offenders = [
        name
        for name, c in _all_module_citations()
        if c.tier == "T5" and not c.flag.startswith("⚠️")  # type: ignore[union-attr]
    ]
    assert not offenders, f"T5 citation flags must start with ⚠️ : {offenders}"


def test_t5_citation_flag_contains_calibrated_marker() -> None:
    """Spec §2 rule: every T5 flag must contain ``[CALIBRATED`` (with the
    opening bracket) so the Confidence Audit tab can group + label calibrated
    parameters uniformly.

    The bracket is required to prevent strings like ``[NOT CALIBRATED — ...]``
    or ``[FOO CALIBRATED BAR]`` from accidentally passing.

    HORIZON_MONTHS keeps ``[CALIBRATED — STANDARD 24-MONTH NPV WINDOW]`` for
    consistency even though it's an NPV convention, not an HR-data calibration.
    """
    offenders = [
        name
        for name, c in _all_module_citations()
        if c.tier == "T5" and "[CALIBRATED" not in (c.flag or "")
    ]
    assert not offenders, f"T5 flags missing '[CALIBRATED' marker: {offenders}"


def test_non_t5_citations_have_no_flag() -> None:
    # Inverse discipline: only T5 carries an amber flag in v1.
    offenders = [name for name, c in _all_module_citations() if c.tier != "T5" and c.flag is not None]
    assert not offenders, f"Non-T5 citations should not have a flag: {offenders}"


# ---------------------------------------------------------------------------
# DL regression tests (every cascade resolution gets a guard)
# ---------------------------------------------------------------------------

def test_dl1_pipeline_per_req_is_5() -> None:
    """DL-1: spec §5.4 patch from 50 → 5; at 50 portfolio nets to −$6.3M."""
    assert constants.PIPELINE_PER_REQ.value == 5
    assert constants.PIPELINE_PER_REQ.tier == "T5"
    assert constants.PIPELINE_PER_REQ.flag is not None


def test_verification_tax_is_037() -> None:
    """Math anchor regression — every gross savings calc taxes by (1 − 0.37)."""
    assert constants.VERIFICATION_TAX_RATE.value == 0.37
    assert constants.VERIFICATION_TAX_RATE.tier == "T1"


def test_dl16_training_coefficient_absent() -> None:
    """DL-16: EY anchor failed source verification → constant must NOT exist in v4.2."""
    assert not hasattr(constants, "TRAINING_COEFFICIENT"), (
        "TRAINING_COEFFICIENT must not exist per DL-16 — EY 5.9 ppt anchor failed "
        "independent source verification across Work Reimagined Survey 2024/2025, "
        "US AI Pulse Survey, and press releases."
    )


def test_dl21_dropout_tiers() -> None:
    """DL-21: Conservative=T1 (RCT), Realistic=T2 (survey mid), Aggressive=T2 (survey upper).

    Unified plan had Aggressive=T1 which was wrong — survey-derived values are T2
    per §2 source authority hierarchy.
    """
    assert constants.DROPOUT_CONSERVATIVE.tier == "T1"
    assert constants.DROPOUT_REALISTIC.tier == "T2"
    assert constants.DROPOUT_AGGRESSIVE.tier == "T2"
    assert constants.DROPOUT_CONSERVATIVE.value == 0.12
    assert constants.DROPOUT_REALISTIC.value == 0.22
    assert constants.DROPOUT_AGGRESSIVE.value == 0.31


def test_dropout_values_monotonic() -> None:
    """Conservative < Realistic < Aggressive for the demo's sensitivity narrative."""
    assert (
        constants.DROPOUT_CONSERVATIVE.value
        < constants.DROPOUT_REALISTIC.value
        < constants.DROPOUT_AGGRESSIVE.value
    )


def test_dl23_both_employee_constants_present() -> None:
    """DL-23: scope clarity — both subsidiary (operating-subsidiary) and consolidated headcounts."""
    assert constants.SAMPLE_ORG_EMPLOYEES.value == 1_151
    assert constants.SAMPLE_ORG_CONSOLIDATED_HEADCOUNT.value == 1_235
    assert constants.SAMPLE_ORG_EMPLOYEES.tier == "T1"
    assert constants.SAMPLE_ORG_CONSOLIDATED_HEADCOUNT.tier == "T1"


def test_dl27_bls_rates_reconciled_to_mean() -> None:
    """DL-27: all three BLS loaded-hourly rates corrected to May 2024 national MEAN.
    Supersedes Cascade 9. Means triangulated across deep research + Perplexity + Gemini,
    reconciled against BLS OOH medians. Display-only constants; engine impact zero."""
    assert constants.HR_SPECIALIST_LOADED_HOURLY.value == 49.83
    assert constants.IT_SPECIALIST_LOADED_HOURLY.value == 40.62
    assert constants.HR_MANAGER_LOADED_HOURLY.value == 100.30
    # Source strings must contain their mean dollar bases (the reconciliation evidence)
    assert "$79,730" in constants.HR_SPECIALIST_LOADED_HOURLY.source
    assert "$64,990" in constants.IT_SPECIALIST_LOADED_HOURLY.source
    assert "$160,480" in constants.HR_MANAGER_LOADED_HOURLY.source
    # Honest evidence-grade caveat: oesm24nat.zip exact-confirm pending
    for c in (
        constants.HR_SPECIALIST_LOADED_HOURLY,
        constants.IT_SPECIALIST_LOADED_HOURLY,
        constants.HR_MANAGER_LOADED_HOURLY,
    ):
        assert "oesm24nat" in c.source


def test_dl10_incident_cost_dora_is_t5() -> None:
    """DL-10 / Cascade adversarial-review finding: INCIDENT_COST_DORA was
    initially classified T4 (derivation-tier from DORA sample), but the
    DEPLOYS_PER_YEAR_DORA denominator used in the construct is itself
    T5-calibrated. Per spec §2 a T4 derivation must come from T1/T2 only,
    so the constant lands at T5. Phase 14 A2 further reframes the source
    string from "reverse-engineered" to "DORA calculator output reproduced"
    — the tier classification (T5) is unchanged by that reframe.
    """
    assert constants.INCIDENT_COST_DORA.tier == "T5"
    assert constants.INCIDENT_COST_DORA.value == 344_000
    assert constants.INCIDENT_COST_DORA.flag is not None


def test_dl3_inline_literals_lifted_to_named_constants() -> None:
    """DL-3: spec §6.1 had RAMP_FLOOR / IMPLEMENTATION_* as inline numeric literals.

    Surfaced into Confidence Audit as named T5 amber Citations.
    """
    assert constants.RAMP_FLOOR.value == 0.35
    assert constants.RAMP_FLOOR.tier == "T5"
    assert constants.IMPLEMENTATION_SETUP_PER_EMPLOYEE.value == 50
    assert constants.IMPLEMENTATION_SETUP_PER_EMPLOYEE.tier == "T5"
    assert constants.IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR.value == 30
    assert constants.IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR.tier == "T5"


def test_helpdesk_resolution_anchors_present() -> None:
    """§3.2 informational anchors: 82 hr median, 17 hr top performer (Unthread 2025).

    Not used in §5 calcs but surfaced via CITATIONS for Confidence Audit completeness.
    Locked-value guard so the published anchors can't drift undetected.
    """
    assert constants.HELPDESK_RESOLUTION_MEDIAN_HOURS.value == 82
    assert constants.HELPDESK_RESOLUTION_MEDIAN_HOURS.tier == "T2"
    assert constants.HELPDESK_RESOLUTION_TOP_PERFORMER_HOURS.value == 17
    assert constants.HELPDESK_RESOLUTION_TOP_PERFORMER_HOURS.tier == "T2"
    assert constants.HELPDESK_RESOLUTION_MEDIAN_HOURS in CITATIONS
    assert constants.HELPDESK_RESOLUTION_TOP_PERFORMER_HOURS in CITATIONS


def test_dl24_manager_multiplier_max_is_decorative_reference() -> None:
    """DL-24 / Cascade 13: spec §4.5 says manager_support_score is T1 with
    Gallup 8.7× multiplier applied, but §0.00 changelog says Option D ships
    decorative wrappers in v1 (multiplier = 1.0). §0.00 wins.

    This constant lives in the audit surface (Confidence Audit shows it as a
    reference), but is NOT applied as a productivity multiplier in v1.
    The Phase 9 ``compute_manager_multiplier`` is the corresponding code guard.
    """
    assert constants.MANAGER_MULTIPLIER_MAX.value == 8.7
    assert constants.MANAGER_MULTIPLIER_MAX.tier == "T1"
    assert constants.MANAGER_MULTIPLIER_MAX in CITATIONS
    # Source string must surface the "likelihood ratio, NOT productivity multiplier"
    # disclaimer so the audit tab cannot silently mis-represent it.
    source = constants.MANAGER_MULTIPLIER_MAX.source.lower()
    assert "likelihood ratio" in source, (
        "MANAGER_MULTIPLIER_MAX.source must declare it as a likelihood ratio, "
        "not a productivity multiplier (DL-24 / Cascade 13)"
    )


# ---------------------------------------------------------------------------
# CITATIONS list invariants
# ---------------------------------------------------------------------------

def test_citations_list_contains_only_citations() -> None:
    assert all(isinstance(c, Citation) for c in CITATIONS)


def test_citations_list_no_duplicates() -> None:
    # Citations are frozen dataclasses → hashable; duplicates would silently bloat the audit list.
    assert len(CITATIONS) == len(set(CITATIONS))


def test_citations_list_includes_all_module_citations() -> None:
    """The audit surface (CITATIONS) must equal the set of module-level Citations.

    Catches the case where a new Citation is added at module-scope but forgotten
    in the CITATIONS list — silent loss of audit visibility.
    """
    module_citations = {c for _, c in _all_module_citations()}
    list_citations = set(CITATIONS)
    missing_from_list = module_citations - list_citations
    extra_in_list = list_citations - module_citations
    assert not missing_from_list, f"Module Citations missing from CITATIONS list: {missing_from_list}"
    assert not extra_in_list, f"CITATIONS list has entries not at module scope: {extra_in_list}"


def test_module_citations_have_no_field_duplicates() -> None:
    """Frozen-dataclass Citations are hashable on all fields; two Citations with
    identical (value, source, tier, flag) tuples would silently collapse to one set
    element in :func:`test_citations_list_includes_all_module_citations`. Add a
    direct name-count vs set-count guard to catch field-duplicate Citations at
    module scope before they become invisible to the audit surface."""
    names_and_citations = _all_module_citations()
    name_count = len(names_and_citations)
    unique_citation_count = len({c for _, c in names_and_citations})
    assert name_count == unique_citation_count, (
        f"Module has {name_count} Citation names but only {unique_citation_count} "
        f"unique field tuples — at least one pair shares (value, source, tier, flag) "
        f"and would silently collapse in set-based audit checks."
    )
