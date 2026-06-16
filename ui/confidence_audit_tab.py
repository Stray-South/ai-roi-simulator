"""Confidence Audit tab (Phase 9) — iterates CITATIONS and renders the audit surface.

Single source of truth: ``roi_calc.constants.CITATIONS``. The Citation dataclass
exposes ``value``, ``source``, ``tier``, ``flag`` — Phase 9 iterates once.
T5 rows render with the amber background per DL-12.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from roi_calc.constants import CITATIONS


def render() -> None:
    st.header("Confidence Audit — every parameter, every source")

    st.markdown(
        "Every numeric anchor and calibrated parameter in the engine, with its "
        "tier (T1–T5), source citation, and amber flag where applicable."
    )

    # Cast Value to str (same Arrow-serialization fix as inputs_review_tab):
    # CITATIONS contains a mix of int (1151, 26) and float (0.37, 5.9) values.
    # PyArrow can usually unify int+float but stringification is the safe display.
    rows = [
        {
            "Value": (f"{c.value:,.4g}" if isinstance(c.value, float) and c.value < 1
                      else f"{c.value:,.2f}" if isinstance(c.value, float)
                      else f"{c.value:,}"),
            "Tier": c.tier,
            "Source": c.source,
            "Flag": c.flag or "",
        }
        for c in CITATIONS
    ]
    df = pd.DataFrame(rows)

    # Group by tier — T1 first, T5 amber last so the calibrated set is bottom-of-tab
    tier_order = {"T1": 0, "T2": 1, "T3": 2, "T4": 3, "T5": 4}
    df = df.sort_values("Tier", key=lambda col: col.map(tier_order))

    # DL-12 + spec §8.4 "no exceptions": T5 rows render with amber background
    styled = df.style.apply(
        lambda row: [
            "background-color: #FFF7ED; color: #92400E;"
            if row["Tier"] == "T5"
            else ""
            for _ in row
        ],
        axis=1,
    )
    st.dataframe(styled, width="stretch", hide_index=True)

    # Gate 11 + DL-18 disclosure inline
    st.markdown("---")
    st.subheader("Tail-risk disclosure (Gate 11)")
    st.markdown(
        "The `decision_point_risk_delta` calculation anchors on a $5K-per-error "
        "administrative remediation cost. **Bias-tail exposure is uncapped.** "
        "Active class-action precedent:\n\n"
        "- *Mobley v. Workday* — class certified May 2025; bench trial Jan 2026.\n"
        "- *Kistler v. Eightfold AI* — pending; similar AI-hiring discrimination claims.\n\n"
        "A single substantiated bias-tail event could exceed the entire annual "
        "decision-point risk by 1-2 orders of magnitude."
    )

    st.subheader("EY anchor — removed in v4.2")
    st.markdown(
        "v4.1 listed an EY '+5.9 ppt per ppt training spend' coefficient as T1. "
        "Independent source verification across EY's Work Reimagined Survey 2024/2025, "
        "US AI Pulse Survey, and press releases failed to confirm the figure. "
        "Per the project's verification policy *'if we can't verify, we don't include it'*, the anchor "
        "is removed entirely from v4.2. `training_spend_ppt` remains as a "
        "decorative slider per Option D."
    )
