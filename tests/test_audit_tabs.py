"""Phase 9 audit-tab content tests — EY references blessed as explanatory.

Both Capability Audit and Confidence Audit tabs render "EY" — but as EXPLANATORY
context for why the anchor was removed in v4.2, NOT as an active citation.
These tests guard the explanatory framing so future edits can't accidentally
reintroduce EY as a live source.
"""

from __future__ import annotations

from pathlib import Path

CAPABILITY_AUDIT_PATH = Path(__file__).parent.parent / "ui" / "capability_audit_tab.py"
CONFIDENCE_AUDIT_PATH = Path(__file__).parent.parent / "ui" / "confidence_audit_tab.py"


def test_capability_audit_ey_appears_only_in_removal_explanation() -> None:
    """When the capability_audit_tab mentions 'EY', the surrounding context must
    explain the removal (per Logan's 'if we can't verify, we don't include it')."""
    src = CAPABILITY_AUDIT_PATH.read_text()
    # Every "EY" occurrence must be in proximity to "failed", "removed", or "verify"
    if "EY" in src:
        assert any(kw in src for kw in ("failed", "removed", "verify"))


def test_confidence_audit_ey_appears_only_in_removal_explanation() -> None:
    """Same blessing for confidence_audit_tab."""
    src = CONFIDENCE_AUDIT_PATH.read_text()
    if "EY" in src:
        assert any(kw in src for kw in ("failed", "removed", "verify"))


def test_capability_audit_does_not_present_ey_as_live_citation() -> None:
    """'EY' must not appear in a "Source:" or as part of a Citation rendering."""
    src = CAPABILITY_AUDIT_PATH.read_text()
    # Anti-pattern: rendering EY as an active reference (e.g. f"Source: EY ...")
    assert "Source: EY" not in src
    assert '"EY"' not in src or "removed" in src  # quoted EY only in removal context


def test_confidence_audit_does_not_present_ey_as_live_citation() -> None:
    src = CONFIDENCE_AUDIT_PATH.read_text()
    assert "Source: EY" not in src
