"""Phase 6 pure-function tests for ui/mode_router.py + ui/components.py.

UI smoke (clicking through Streamlit tabs) cannot be exercised in pytest;
Surgical Engineer §"UI without browser" explicitly notes that. Phase 12 does
the manual smoke test against the deployed URL.
"""

from __future__ import annotations

import pytest

from ui.mode_router import (
    ENGINEERING_TABS,
    PEOPLE_TABS,
    tabs_for_mode,
)


def test_tabs_for_people_mode_includes_setup_and_results() -> None:
    tabs = tabs_for_mode("People")
    assert "Setup" in tabs
    assert "Results" in tabs


def test_tabs_for_engineering_mode_includes_setup_and_results() -> None:
    tabs = tabs_for_mode("Engineering")
    assert "Setup" in tabs
    assert "Results" in tabs


def test_gate12_bridge_appendix_in_both_modes() -> None:
    """Gate 12: Bridge Appendix tab MUST render in both modes."""
    assert "Bridge Appendix" in PEOPLE_TABS
    assert "Bridge Appendix" in ENGINEERING_TABS


def test_people_mode_has_capability_audit_tab() -> None:
    """Per spec §8.2: People Mode includes Capability Audit + Confidence Audit."""
    assert "Capability Audit" in PEOPLE_TABS
    assert "Confidence Audit" in PEOPLE_TABS


def test_engineering_mode_has_assessment_tab_not_capability_audit() -> None:
    """Per spec §8.3: Engineering Mode has Assessment radar, not Capability Audit."""
    assert "Assessment" in ENGINEERING_TABS
    assert "Capability Audit" not in ENGINEERING_TABS


def test_tabs_for_mode_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError, match="must be 'People' or 'Engineering'"):
        tabs_for_mode("Other")  # type: ignore[arg-type]


def test_tabs_ordering_setup_first_bridge_last() -> None:
    """Spec §8.6: Setup is the demo entry point. Bridge Appendix is the closing move."""
    assert PEOPLE_TABS[0] == "Setup"
    assert PEOPLE_TABS[-1] == "Bridge Appendix"
    assert ENGINEERING_TABS[0] == "Setup"
    assert ENGINEERING_TABS[-1] == "Bridge Appendix"
