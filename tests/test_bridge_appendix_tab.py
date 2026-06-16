"""Phase 11.5 Bridge Appendix tab tests — v4.2 §8.7 verbatim regression + Gate 12."""

from __future__ import annotations

import pytest

from ui.bridge_appendix_tab import _BRIDGE_CAPTION, _BRIDGE_TABLE_MARKDOWN


def test_bridge_appendix_contains_all_10_metric_rows() -> None:
    """All 10 DORA metrics must appear in the table."""
    expected = [
        "Deployment Frequency",
        "Lead Time for Changes",
        "Change Failure Rate",
        "Failed Deployment Recovery",
        "J-Curve",
        "Instability Tax",
        "Verification Tax",
        "7 AI Capabilities",
        "7 Team Archetypes",
        "METR Self-Report Discount",
    ]
    for metric in expected:
        assert metric in _BRIDGE_TABLE_MARKDOWN, f"Missing metric: {metric}"


def test_bridge_appendix_row_8_uses_v4_2_text_not_v4_1() -> None:
    """v4.1 said 'Training spend (EY) + manager support (Gallup) as v1 reduced set'.
    Sanitized v1: "Manager support (Gallup, decorative — Day-90 calibration); training spend
    (decorative, no source-verified coefficient)'. Regression guard."""
    assert "decorative — Day-90 calibration" in _BRIDGE_TABLE_MARKDOWN
    assert "no source-verified coefficient" in _BRIDGE_TABLE_MARKDOWN
    assert "v1 reduced set" not in _BRIDGE_TABLE_MARKDOWN


def test_bridge_appendix_does_not_contain_ey() -> None:
    """DL-16: EY anchor removed; Bridge Appendix table must not mention EY."""
    assert "EY" not in _BRIDGE_TABLE_MARKDOWN


def test_bridge_appendix_caption_mentions_day_90() -> None:
    """Day-90 deliverable is the closing line."""
    assert "Day 90" in _BRIDGE_CAPTION


def test_bridge_appendix_caption_mentions_left_right_columns() -> None:
    """The pitch is: engineering reads left, finance reads right."""
    assert "left column" in _BRIDGE_CAPTION
    assert "right column" in _BRIDGE_CAPTION


def test_gate12_bridge_appendix_renders_in_both_modes() -> None:
    """Gate 12: Bridge Appendix tab is in BOTH PEOPLE_TABS and ENGINEERING_TABS.
    Already covered by test_gate12_bridge_appendix_in_both_modes in
    test_mode_router.py; this is a Phase 11.5 cross-reference guard."""
    from ui.mode_router import ENGINEERING_TABS, PEOPLE_TABS
    assert "Bridge Appendix" in PEOPLE_TABS
    assert "Bridge Appendix" in ENGINEERING_TABS
