"""Phase 6 tests for ui/components.py — pure-function helpers (no Streamlit context)."""

from __future__ import annotations

from roi_calc.constants import (
    PIPELINE_PER_REQ,
    SAMPLE_ORG_EMPLOYEES,
    VERIFICATION_TAX_RATE,
)
from ui.components import (
    AMBER_BG,
    FRIENDLY_LABELS,
    citation_tooltip,
    friendly_label,
)


def test_amber_bg_color_matches_spec_section_8_4() -> None:
    """Spec §8.4: T5 widget background must be #FFF7ED."""
    assert AMBER_BG == "#FFF7ED"


def test_citation_tooltip_for_t1_no_flag() -> None:
    """T1 citation: tooltip shows tier + source, no flag prefix."""
    tip = citation_tooltip(VERIFICATION_TAX_RATE)
    assert "[T1]" in tip
    assert "Workday" in tip
    assert tip.startswith("[T1]")  # no flag prefix for T1


def test_citation_tooltip_for_t5_prefixes_flag() -> None:
    """T5 citation: tooltip starts with the amber flag."""
    tip = citation_tooltip(PIPELINE_PER_REQ)
    assert tip.startswith("⚠️")
    assert "[T5]" in tip


def test_friendly_label_returns_mapped_value() -> None:
    assert friendly_label("employees") == "Employees (headcount)"
    assert friendly_label("fully_loaded_cost_per_fte") == "Fully-loaded cost per FTE ($)"


def test_friendly_label_falls_back_to_field_name() -> None:
    """If a field is unmapped (e.g. new Phase N field), fall back to raw name."""
    assert friendly_label("some_unknown_field") == "some_unknown_field"


def test_friendly_labels_covers_every_peopleinputs_field() -> None:
    """Schema lock: every PeopleInputs field must have a friendly label."""
    from dataclasses import fields
    from roi_calc.models import PeopleInputs
    missing = [f.name for f in fields(PeopleInputs) if f.name not in FRIENDLY_LABELS]
    assert not missing, f"PeopleInputs fields missing from FRIENDLY_LABELS: {missing}"


def test_friendly_labels_covers_every_engineeringinputs_field() -> None:
    """Schema lock: every EngineeringInputs field must have a friendly label."""
    from dataclasses import fields
    from roi_calc.models import EngineeringInputs
    missing = [f.name for f in fields(EngineeringInputs) if f.name not in FRIENDLY_LABELS]
    assert not missing, f"EngineeringInputs fields missing from FRIENDLY_LABELS: {missing}"
