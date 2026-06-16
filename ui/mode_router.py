"""Mode router — dispatches tabs based on the mode toggle (Phase 6).

DL-22 / Cascade 8: switching modes invalidates the prior mode's computed
portfolio + breakeven results so stale numbers never display.

Bridge Appendix (Phase 11.5) renders in BOTH modes per Gate 12 — the
mode-router lists it as a tab for each mode.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st

from roi_calc.models import EngineeringInputs, PeopleInputs


Mode = Literal["People", "Engineering"]

PEOPLE_TABS = (
    "Setup",
    "Results",
    "Sensitivity",
    "Capability Audit",
    "Confidence Audit",
    "Inputs Review",
    "Bridge Appendix",  # Gate 12
)

ENGINEERING_TABS = (
    "Setup",
    "Results",
    "Sensitivity",
    "Assessment",
    "Inputs Review",
    "Bridge Appendix",  # Gate 12
)


def tabs_for_mode(mode: Mode) -> tuple[str, ...]:
    """Return the tab ordering for a given mode.

    Phase 6 unit tests assert that ``"Bridge Appendix"`` is in both tuples
    (Gate 12 regression guard).
    """
    if mode == "People":
        return PEOPLE_TABS
    if mode == "Engineering":
        return ENGINEERING_TABS
    raise ValueError(f"Unknown mode {mode!r}; must be 'People' or 'Engineering'")


def invalidate_results_for_other_mode(current_mode: Mode) -> None:
    """DL-22: when the user toggles to ``current_mode``, the PREVIOUS mode's
    cached portfolio + breakeven must be cleared so a tab-switch doesn't show
    stale numbers from the mode we just left.

    Symmetric across modes — both ``portfolio`` and ``breakeven`` keys cleared.
    """
    other = "engineering" if current_mode == "People" else "people"
    keys_to_clear = (
        f"{other}_portfolio",
        f"{other}_breakeven",
    )
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None


def initialize_session_state() -> None:
    """Lazy-init session state on first page load."""
    defaults = {
        "mode": "People",
        "people_inputs": PeopleInputs(),
        "engineering_inputs": EngineeringInputs(),
        "people_portfolio": None,
        "people_breakeven": None,
        "engineering_portfolio": None,
        "engineering_breakeven": None,  # symmetric with people_breakeven (DL-22)
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render(mode: Mode) -> None:
    """Dispatch to the per-mode tab handlers.

    Phase 6 ships the shell + Setup tab. Phases 7-11.5 fill in the rest.
    Each tab handler is a late import so Phase 6 doesn't require those
    modules to exist yet.

    Footer renders below the tab containers (Streamlit top-to-bottom),
    making it persistent across all tabs per spec §8.5 + Gate 13.
    """
    initialize_session_state()
    tabs = tabs_for_mode(mode)
    tab_handles = st.tabs(tabs)
    for tab_name, tab_handle in zip(tabs, tab_handles):
        with tab_handle:
            _dispatch_tab(tab_name, mode)

    # Persistent footer below all tabs (Gate 13: Day-90 bolded in People Mode)
    from ui.footer import render_footer
    render_footer(mode)


def _dispatch_tab(tab_name: str, mode: Mode) -> None:
    """Late-import dispatcher. Phase 6 implements Setup; the rest stub with
    a "Coming in Phase N" message until those phases ship."""
    if tab_name == "Setup":
        from ui.setup_tab import render as render_setup
        render_setup(mode)
    elif tab_name == "Bridge Appendix":
        # Phase 11.5 — same content in both modes (Gate 12)
        try:
            from ui.bridge_appendix_tab import render as render_bridge
            render_bridge()
        except ImportError:
            st.info("Bridge Appendix — shipping in Phase 11.5")
    elif tab_name == "Results":
        try:
            if mode == "People":
                from ui.results_tab_people import render as render_results
            else:
                from ui.results_tab_engineering import render as render_results
            render_results()
        except ImportError:
            st.info(f"Results tab — shipping in Phase {'7' if mode == 'People' else '10'}")
    elif tab_name == "Sensitivity":
        try:
            from ui.sensitivity_tab import render as render_sens
            render_sens(mode)
        except ImportError:
            st.info("Sensitivity tab — shipping in Phase 8")
    elif tab_name == "Capability Audit":
        try:
            from ui.capability_audit_tab import render as render_cap
            render_cap()
        except ImportError:
            st.info("Capability Audit — shipping in Phase 9")
    elif tab_name == "Confidence Audit":
        try:
            from ui.confidence_audit_tab import render as render_conf
            render_conf()
        except ImportError:
            st.info("Confidence Audit — shipping in Phase 9")
    elif tab_name == "Assessment":
        try:
            from ui.assessment_tab import render as render_assess
            render_assess()
        except ImportError:
            st.info("Assessment radar — shipping in Phase 10")
    elif tab_name == "Inputs Review":
        try:
            from ui.inputs_review_tab import render as render_inputs
            render_inputs(mode)
        except ImportError:
            st.info("Inputs Review — shipping in Phase 11")
