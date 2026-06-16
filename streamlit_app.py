"""AI ROI Simulator — entrypoint.

Mode toggle is the demo opener. People Mode is the default + primary;
Engineering Mode is the credibility-check half of the dual-mode framework.

Design: light theme + per-mode CSS-only accent swap via
``ui.theme.inject_theme``; HTML header replaces the bare ``st.title``; mode
toggle uses ``st.segmented_control`` (Streamlit ≥1.39) for native chrome.
Math / citations / footer / amber-flag rules LOCKED.
"""

from __future__ import annotations

import streamlit as st

from ui.mode_router import (
    initialize_session_state,
    invalidate_results_for_other_mode,
    render,
)
from ui.theme import inject_theme


def main() -> None:
    st.set_page_config(
        page_title="AI ROI Simulator",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    initialize_session_state()

    # Inject theme FIRST so it applies on first paint. Idempotent — re-runs
    # on every Streamlit script run.
    prior_mode = st.session_state.get("mode", "People")
    inject_theme(prior_mode)

    # --- Header. theme.css provides the h1 sizing.
    # IMPORTANT: do NOT indent the HTML content. Streamlit's markdown parser
    # treats any line indented ≥4 spaces as a code block, which leaks the raw
    # HTML as visible monospace text.
    # The .app-header__meta column uses one <div> per line. <br> tags get
    # collapsed by Streamlit's markdown sanitizer on some builds; explicit
    # <div> children guarantee three lines render on three lines.
    st.markdown(
        """
<div class="app-header">
  <div class="app-header__brand">
    <div class="app-header__mark">LF</div>
    <div>
      <div class="eyebrow">AI ROI Simulator · v1.0</div>
      <h1>Hard-dollar economics for regulated consumer finance</h1>
    </div>
  </div>
  <div class="app-header__meta">
    <div>Methodology template · 90-day calibration</div>
    <div>Sample defaults · 1,151 employees · 230 hires/yr</div>
    <div>Open source · LF</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Single lede — sets up the mode toggle the reader is about to encounter.
    st.markdown(
        "*Same scaffolding, different data: People Mode is the primary "
        "pitch, Engineering Mode the credibility check. Day 90 of the "
        "90-day plan replaces every amber flag with org-measured baselines.*"
    )

    # Reader-anchor with 5-beat structure (AuDHD-friendly scan-path).
    # Five bolded inline labels: What you're looking at / The investment /
    # The before/after / The number / What's amber-flagged.
    # Purely descriptive — no rhetorical framing.
    st.markdown(
        """
<div class="reader-anchor">
  <p><strong>What you're looking at.</strong>
  This calculates the dollar return on implementing an AI-assisted layer for
  one specific workflow at a mid-market regulated consumer-finance lender:
  <em>Infrastructure Onboarding</em> — the end-to-end process of getting a
  new hire from offer-accept to fully productive
  (sample defaults: 1,151 employees, 230 hires/year).</p>

  <p><strong>The investment.</strong>
  $57,550 upfront (setup, integrations, configuration) + $34,530/year recurring
  (license, maintenance). About $127K invested over 24 months.</p>

  <p><strong>The before/after.</strong>
  Five hard-dollar effects, each comparing the current manual onboarding
  against the same workflow with an AI layer: faster new-hire ramp
  (8.5 → 5.9 weeks, the largest single line), HR help-desk deflection,
  benefits-billing recovery, and two honest risk lines — recruiting attrition
  AI doesn't fix in v1, and decision-point compliance errors that go up
  before the oversight layer is fully wired.</p>

  <p><strong>The number.</strong>
  $472,503 net/year at the sample defaults. Break-even at Month 8.
  Workday 37% verification tax already applied — these are net, not gross.</p>

  <p><strong>What's amber-flagged.</strong>
  Parameters where no published HR data exists are calibrated against
  engineering-side analogs (DORA) and flagged ⚠. Day 90 of the implementation
  engagement replaces them with your organization's measured baselines.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # Mode toggle. st.segmented_control gives native segmented chrome that
    # theme.css tints to follow var(--accent).
    mode = st.segmented_control(
        "Mode",
        options=["People", "Engineering"],
        default=prior_mode,
        help=(
            "People Mode is the primary demo. "
            "Engineering Mode demonstrates DORA framework fluency."
        ),
        key="mode_segmented",
        label_visibility="collapsed",
    )
    # segmented_control returns None if no selection — fall back to prior_mode.
    if mode is None:
        mode = prior_mode

    # Invalidate the prior mode's cached results on toggle.
    # Re-inject within this render so the accent swap (terracotta ↔ navy)
    # takes effect on the same frame as the toggle (no one-frame flash).
    if mode != prior_mode:
        invalidate_results_for_other_mode(current_mode=mode)
        st.session_state["mode"] = mode
        inject_theme(mode)

    render(mode)


if __name__ == "__main__":
    main()
