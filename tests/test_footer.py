"""Phase 11 footer tests — v4.2 §8.5 verbatim regression.

DL-15: corrects two text-drift bugs from v4.1:
  * "Hard-dollar calculations" (no "Five" prefix) — Gate 13
  * Citation list contains "Gallup" but NOT "EY"
"""

from __future__ import annotations

from ui.footer import ENGINEERING_MODE_FOOTER, PEOPLE_MODE_FOOTER


def test_people_footer_does_not_contain_ey() -> None:
    """DL-16: EY anchor removed in v4.2 — footer citation list must not mention EY."""
    assert "EY" not in PEOPLE_MODE_FOOTER


def test_people_footer_does_not_contain_five_hard_dollar() -> None:
    """v4.1 said 'Five hard-dollar calculations' before EY removal made it 'Hard-dollar' generic.
    Regression guard against re-prefixing 'Five'."""
    assert "Five hard-dollar" not in PEOPLE_MODE_FOOTER


def test_people_footer_contains_day_90_bolded() -> None:
    """Gate 13: Day-90 sentence is bolded markdown."""
    assert "**Day 90" in PEOPLE_MODE_FOOTER


def test_people_footer_citation_list_includes_gallup() -> None:
    """Gallup is the remaining T1 reference (decorative under Option D)."""
    assert "Gallup" in PEOPLE_MODE_FOOTER


def test_people_footer_mentions_verification_tax() -> None:
    assert "37%" in PEOPLE_MODE_FOOTER
    assert "Workday/Hanover" in PEOPLE_MODE_FOOTER


def test_engineering_footer_mentions_dora_and_metr() -> None:
    assert "DORA" in ENGINEERING_MODE_FOOTER
    assert "METR" in ENGINEERING_MODE_FOOTER


def test_engineering_footer_calls_out_high_uncertainty_disclaimer() -> None:
    """v4.2 §8.5 verbatim ending."""
    assert "high-uncertainty estimate" in ENGINEERING_MODE_FOOTER
    assert "spark a conversation" in ENGINEERING_MODE_FOOTER
