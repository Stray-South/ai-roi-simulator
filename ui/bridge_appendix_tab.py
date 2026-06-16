"""Bridge Appendix tab (Phase 11.5) — DORA → CFO transform table.

VERBATIM from v4.2 §8.7. Same content renders in BOTH People and Engineering
modes (Gate 12). Row 8 ("7 AI Capabilities") uses the v4.2 text — NOT the v4.1
"Training spend (EY)" formulation.

Regression tests in `tests/test_bridge_appendix_tab.py` guard verbatim text.
"""

from __future__ import annotations

import streamlit as st


_BRIDGE_TABLE_MARKDOWN = """
| DORA metric (engineering language) | CFO / CPO translation (business language) | What it measures in People Mode |
|---|---|---|
| **Deployment Frequency** | Cycle time of value delivery | HR events processed per period (hires onboarded/month) |
| **Lead Time for Changes** | Time from request to value | Time from offer-accept to Day-0 productive (onboarding lead time) |
| **Change Failure Rate (CFR)** | Rework rate / quality cost | Decision-point error rate (per T·T·D primitive) |
| **Failed Deployment Recovery Time** | Mean time to remediate | Time from compliance error to remediation closure |
| **J-Curve (productivity dip)** | Tuition cost of transformation | Investment-phase region on the break-even chart |
| **Instability Tax** *(industry-common label for DORA's CFR delta × deploys × incident cost; distinct from row below)* | Cost-per-incident × CFR delta | Decision-point compliance risk delta (§5.5) |
| **Verification Tax** *(Workday/Hanover 37%; distinct from row above — different measured population, different work type)* | % of gross savings absorbed by re-work | Workday/Hanover 37% universal net-down |
| **7 AI Capabilities** | Org-readiness gates that amplify or attenuate AI ROI | Manager support (Gallup, decorative — Day-90 calibration); training spend (decorative, no source-verified coefficient) |
| **7 Team Archetypes** | Operating-model maturity bands | Not yet mapped to People — flagged as v2 work |
| **METR Self-Report Discount** | Honest correction for self-reported gains | Not yet HR-published — flagged as calibrated |
"""

_BRIDGE_CAPTION = (
    "This table is the bridge. The engineering org reads the left column. "
    "Finance and HR read the right column. The People-Mode column shows where "
    "each metric has a published HR analog and where it is still pending. "
    "Day 90 of the 90-day plan resolves the pending rows with org-specific measurement."
)


def render() -> None:
    st.header("Bridge Appendix — DORA → CFO Transform")
    st.markdown(
        "A reference appendix tab available in **both modes**. The single best "
        "CIO/CFO-credibility artifact in the calculator. Translates DORA's "
        "engineering metrics into CFO/CPO language so the interviewer can read "
        "the same calculator from either stakeholder's perspective."
    )
    st.markdown(_BRIDGE_TABLE_MARKDOWN)
    st.caption(_BRIDGE_CAPTION)
