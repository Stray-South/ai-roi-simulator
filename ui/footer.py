"""Mode-aware persistent footer (Phase 11).

People-Mode footer text is VERBATIM from v4.2 §8.5 (DL-15 / Gate 13):
  * No "Five" before "Hard-dollar calculations" (dropped after EY removal)
  * No "EY" in the citation list
  * Day-90 sentence is bolded
Phase 11 regression tests guard the verbatim text.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st


PEOPLE_MODE_FOOTER = (
    "Hard-dollar calculations come from published HR research (Workday, Mewayz, "
    "Beneration, Unthread, SHRM, Gallup). Calibrated parameters are amber-flagged. "
    "The verification tax (37%) applies universally — Workday/Hanover n=3,200. "
    "**Day 90 of the 90-day plan replaces amber-flagged calibrated parameters with "
    "org-measured values from the org's own systems.**"
)

ENGINEERING_MODE_FOOTER = (
    "DORA J-Curve and instability tax from DORA 2025 ROI Report. 7-capability "
    "model from DORA 2025 Capabilities Model. METR 2025 RCT self-report discount "
    "applied. This is a high-uncertainty estimate meant to spark a conversation."
)


def render_footer(mode: Literal["People", "Engineering"]) -> None:
    """Phase 15 refresh: delegate to ``render_footer_html`` so the
    ``.app-footer`` CSS class in ``ui/assets/theme.css`` actually styles the
    footer. The markdown ``**...**`` bold in ``PEOPLE_MODE_FOOTER`` is
    converted to inline ``<strong>...</strong>`` HTML — semantically
    identical bolding, now visible inside the styled footer container.

    Footer TEXT remains locked (Phase 11 tests guard ``PEOPLE_MODE_FOOTER`` /
    ``ENGINEERING_MODE_FOOTER`` constants); only the rendering wrapper moved.
    """
    from ui.components import render_footer_html

    text = PEOPLE_MODE_FOOTER if mode == "People" else ENGINEERING_MODE_FOOTER
    st.markdown("---")
    render_footer_html(text)
