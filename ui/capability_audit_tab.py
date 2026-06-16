"""Capability Audit tab (Phase 9 / Option D per DL-8 / DL-24).

Surfaces the two decorative wrappers (training_spend_ppt + manager_support_score)
with explicit "v1 ships decorative; Day-90 calibrates" disclosure so the demo
audience can SEE the honesty.
"""

from __future__ import annotations

import streamlit as st

from roi_calc.constants import MANAGER_MULTIPLIER_MAX


def render() -> None:
    st.header("Capability Audit (decorative multipliers)")
    st.markdown(
        "v1 ships **decorative multipliers** (training spend, manager support both 1.0×). "
        "Day 90 calibrates them against org-measured baselines. This tab surfaces what "
        "is still pending."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Training spend coefficient")
        st.markdown(
            "**Status:** decorative wrapper (1.0×)\n\n"
            "**Why:** the EY '+5.9 ppt per ppt training spend' anchor failed "
            "independent source verification across Work Reimagined Survey 2024/2025, "
            "EY US AI Pulse Survey, and press releases. Per the project's verification policy "
            "*'if we can't verify, we don't include it'*, the constant is absent "
            "from `constants.py`. The slider remains for v2 calibration."
        )

    with col2:
        st.subheader("Manager support multiplier")
        st.markdown(
            f"**Status:** decorative wrapper (1.0×)\n\n"
            f"**Reference:** Gallup State of Global Workplace 2026 — "
            f"**{MANAGER_MULTIPLIER_MAX.value}×** likelihood ratio for "
            f"'AI transformed work' (NOT a productivity multiplier).\n\n"
            f"**Why decorative:** likelihood ratios on binary outcomes don't compose "
            f"with dollar-denominated productivity math. Linear interpolation would "
            f"inflate the portfolio from $475K to $2.29M — not defensible."
        )

    st.markdown("---")
    st.info(
        "**Day-90 deliverable:** replace these decorative wrappers with "
        "calibrated multipliers derived from your organization's measured training spend, "
        "manager-1-on-1 frequency, and productivity baselines."
    )
