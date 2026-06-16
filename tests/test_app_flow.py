"""Phase 13 — Streamlit AppTest user-flow audit.

End-to-end tests that boot ``streamlit_app.py`` via ``AppTest`` and exercise
the actual user flow: mode toggle, Setup inputs, Calculate, Results tab,
Sensitivity tornado, Confidence Audit, Bridge Appendix, Engineering Mode.

These catch a class of bugs that the 324 unit tests cannot:
  * Widget key collisions
  * Session-state read-before-write
  * Tab-render exceptions
  * Plotly figure-build failures
  * Deprecated Streamlit API surface
  * Spec text leaks visible only in rendered markdown
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


_APP_PATH = str(Path(__file__).parent.parent / "streamlit_app.py")


def _all_markdown(at: AppTest) -> str:
    """Concatenate every markdown/caption/info/error/success/header block.

    AppTest exposes these as separate element collections; we mash them into
    one searchable string for content-grep assertions.
    """
    parts: list[str] = []
    for block in at.markdown:
        parts.append(str(block.value))
    for block in at.caption:
        parts.append(str(block.value))
    for block in at.info:
        parts.append(str(block.value))
    for block in at.error:
        parts.append(str(block.value))
    for block in at.success:
        parts.append(str(block.value))
    for block in at.header:
        parts.append(str(block.value))
    for block in at.subheader:
        parts.append(str(block.value))
    for block in at.text:
        parts.append(str(block.value))
    # Metric labels + values
    for m in at.metric:
        parts.append(f"{m.label}={m.value}")
    return "\n".join(parts)


def _boot() -> AppTest:
    """Boot the app at defaults; run one cycle."""
    at = AppTest.from_file(_APP_PATH, default_timeout=15)
    at.run()
    return at


# ---------------------------------------------------------------------------
# 1. Boot smoke
# ---------------------------------------------------------------------------

def test_app_loads_without_exceptions_at_defaults() -> None:
    """The most basic gate: app boots with no uncaught exceptions.

    Note: ``at.exception`` only captures exceptions that escape the script.
    Errors swallowed by ``try/except + st.error(...)`` show up in ``at.error``.
    We assert both to defeat the "silently caught" failure mode.
    """
    at = _boot()
    assert len(at.exception) == 0, f"App raised {len(at.exception)} exceptions: {at.exception}"
    # At default inputs nothing should st.error() either — break-even chart
    # builds cleanly at sample defaults, Engineering tab not yet visited.
    assert len(at.error) == 0, f"App rendered {len(at.error)} error blocks: {[e.value for e in at.error]}"


def test_app_initial_mode_is_people() -> None:
    """Gate 9: mode toggle defaults to People."""
    at = _boot()
    assert at.session_state["mode"] == "People"


def test_app_renders_7_people_tabs() -> None:
    """Spec §8.2: People Mode has 7 tabs (Setup, Results, Sensitivity,
    Capability Audit, Confidence Audit, Inputs Review, Bridge Appendix)."""
    at = _boot()
    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == [
        "Setup", "Results", "Sensitivity", "Capability Audit",
        "Confidence Audit", "Inputs Review", "Bridge Appendix",
    ]


# ---------------------------------------------------------------------------
# 2. Setup → session_state flow
# ---------------------------------------------------------------------------

def test_app_setup_employees_persists_to_session_state() -> None:
    """Setup tab widgets write to session_state on rerun (Streamlit native)."""
    at = _boot()
    # Locate the employees number_input by key
    emp_input = next(ni for ni in at.number_input if ni.key == "people_employees")
    emp_input.set_value(1500)
    at.run()
    assert at.session_state["people_inputs"].employees == 1500


def test_app_setup_calculate_button_populates_portfolio() -> None:
    """Clicking Calculate writes a PortfolioResult to session_state."""
    at = _boot()
    calc = next(b for b in at.button if b.key == "people_calculate")
    calc.click()
    at.run()
    portfolio = at.session_state["people_portfolio"]
    assert portfolio is not None
    assert portfolio.net_annual_value == pytest.approx(472_503, abs=10)


def test_app_setup_calculate_populates_breakeven() -> None:
    """Calculate also populates the BreakEvenResult."""
    at = _boot()
    calc = next(b for b in at.button if b.key == "people_calculate")
    calc.click()
    at.run()
    breakeven = at.session_state["people_breakeven"]
    assert breakeven is not None
    assert breakeven.breakeven_month == 8


# ---------------------------------------------------------------------------
# 3. Results tab content
# ---------------------------------------------------------------------------

def test_app_results_tab_contains_pinned_dollar_values() -> None:
    """Results tab tiles render Phase-3 pinned values verbatim in markdown."""
    at = _boot()
    md = _all_markdown(at)
    # Tile values formatted as $104,165 etc. (allow for slight formatting)
    assert "$104,165" in md
    assert "$902,836" in md
    assert "$290,052" in md
    assert "$472,503" in md  # portfolio net


def test_app_break_even_chart_renders_without_error() -> None:
    """Plotly chart builds + serializes without throwing."""
    at = _boot()
    # An exception during chart build would surface in at.exception
    assert len(at.exception) == 0
    # Caption beneath chart references Gate 6 framing
    md = _all_markdown(at)
    assert "visualization of cumulative cost vs savings" in md


# ---------------------------------------------------------------------------
# 4. Gate regression tests on rendered UI
# ---------------------------------------------------------------------------

def test_a4_subtitle_surfaces_methodology_lede() -> None:
    """Phase 14 A4.1 → v7 update: the .reader-anchor callout now uses the
    original v4-prompt 5-beat structure (What you're looking at / The
    investment / The before/after / The number / What's amber-flagged).
    Same methodology surfaced on page load; assertions match v7 copy.
    """
    at = _boot()
    md = _all_markdown(at)
    # The Number beat surfaces the Workday tax + pinned dollar.
    assert "Workday 37% verification tax already applied" in md
    assert "$472,503 net/year at the sample defaults" in md
    # What's amber-flagged beat surfaces the calibration + Day-90 framing.
    # Substrings asserted separately because the HTML payload preserves the
    # source-line break between "calibrated against" and "engineering-side
    # analogs" — a contiguous match would be false-negative.
    assert "no published HR data exists" in md
    assert "calibrated against" in md
    assert "engineering-side analogs" in md
    assert "Day 90 of the implementation" in md
    # The investment beat surfaces the $57,550 / $34,530 / $127K shape.
    assert "$57,550 upfront" in md
    assert "$34,530/year recurring" in md


def test_a4_results_header_calls_out_verification_tax() -> None:
    """Phase 14 A4.3: People Results header expanded to name the verification tax
    explicitly — the most-defensible single move in the model."""
    at = _boot()
    md = _all_markdown(at)
    assert "Workday 37% verification tax" in md
    assert "Workday/Hanover n=3,200" in md


def test_a3_decision_point_tile_caption_explains_ai_cfr_pattern() -> None:
    """Phase 14 A3: Decision-Point tile is preceded by a framing caption that
    explains why AI shows as worsening compliance (mirrors DORA's CFR-rises-with-AI
    finding). Without this, the red tile reads as a bug. With it, the tile is a
    planted credibility moment.
    """
    at = _boot()
    md = _all_markdown(at)
    assert "mirrors DORA's CFR-rises-with-AI" in md
    # v7: rephrased from "closes this gap" — same meaning, no "gap" language.
    assert "Day 90's deliverable wires that oversight layer" in md


def test_gate11_mobley_kistler_footnote_present_on_results() -> None:
    """Gate 11: Mobley + Kistler tail-risk footnote visible on Tile 5."""
    at = _boot()
    md = _all_markdown(at)
    assert "Mobley v. Workday" in md
    assert "Kistler v. Eightfold" in md


def test_gate12_bridge_appendix_table_v4_2_row_8_present() -> None:
    """Gate 12: Bridge Appendix renders row 8 (decorative calibration + no source-verified coefficient)."""
    at = _boot()
    md = _all_markdown(at)
    assert "decorative — Day-90 calibration" in md
    assert "no source-verified coefficient" in md
    # And NOT the v4.1 EY-flavored text
    assert "v1 reduced set" not in md


def test_gate10_no_compensation_text_anywhere_in_people_mode() -> None:
    """Gate 10: no $145K, comp_multiple, or compensation comparison anywhere."""
    at = _boot()
    md = _all_markdown(at)
    md_lower = md.lower()
    assert "compensation_multiple" not in md_lower
    assert "$145" not in md
    assert "145k" not in md_lower
    # 'compensation' may appear only in disclosure / removal context — not as live tile
    # (Capability Audit + Confidence Audit reference EY's removed comp-style anchor)
    if "compensation" in md_lower:
        # Verify it's in a removal / disclaimer / decorative context
        assert any(
            ctx in md_lower
            for ctx in ("decorative", "removed", "failed", "verify", "verification")
        )


def test_gate13_day_90_line_present_and_bolded() -> None:
    """Gate 13: Day-90 deliverable line in footer with bold emphasis.

    Phase 15 refresh: footer now renders via ``render_footer_html`` which
    converts the markdown ``**...**`` bold to inline ``<strong>...</strong>``
    HTML so the ``.app-footer`` CSS in ``ui/assets/theme.css`` can style it.
    Bold is preserved — implementation shifted from markdown to HTML.
    """
    at = _boot()
    md = _all_markdown(at)
    # Footer renders via render_footer at bottom of mode_router
    assert "Day 90" in md
    # Bolded — was markdown `**Day 90` pre-Phase 15, now HTML `<strong>Day 90`.
    assert "<strong>Day 90" in md


def test_ey_appears_only_in_removal_context() -> None:
    """DL-16: EY MUST appear in Capability/Confidence Audit AS explanatory
    removal context (paired with 'failed', 'removed', or 'verify').

    Proximity check: collect every text element containing "EY", assert each
    one ALSO contains a removal keyword. Whole-document `any(kw in md)` would
    pass vacuously if EY appears in a live tile and the audit text exists
    elsewhere with the keyword.
    """
    at = _boot()
    # Walk every text element type that may contain EY
    elements = (
        [str(m.value) for m in at.markdown]
        + [str(s.value) for s in at.subheader]
        + [str(i.value) for i in at.info]
        + [str(c.value) for c in at.caption]
        + [str(h.value) for h in at.header]
    )
    ey_elements = [e for e in elements if "EY" in e]
    assert ey_elements, (
        "EY string missing entirely — capability_audit_tab or confidence_audit_tab "
        "must surface the EY-anchor-removed disclosure (DL-16)."
    )
    ey_context_keywords = ("failed", "removed", "verify", "verification")
    for elem in ey_elements:
        assert any(kw in elem for kw in ey_context_keywords), (
            f"EY appears outside removal context in element: {elem[:200]!r}"
        )


def test_capability_audit_renders_ey_removal_disclosure() -> None:
    """Specific content check on the Capability Audit tab — the EY-removal
    narrative is the primary disclosure artifact. If the import silently
    stubs (ui/mode_router.py except-ImportError path), this test catches it."""
    at = _boot()
    md = _all_markdown(at)
    # Phrases lifted from ui/capability_audit_tab.py
    assert "5.9 ppt" in md or "failed independent source verification" in md
    # Manager-multiplier explanation
    assert "likelihood ratio" in md.lower()


def test_amber_flag_widget_block_renders_in_setup() -> None:
    """T5 inputs in Setup use amber_flag_widget which emits an HTML block
    containing the #FFF7ED background AND the F59E0B left border. If
    amber_flag_widget is silently bypassed for any T5 Setup input, this fires.

    Note: #FFF7ED alone is insufficient — the Confidence Audit dataframe Styler
    also emits #FFF7ED for T5 rows. The Setup-specific marker is the F59E0B
    left border which only render_amber_block uses.
    """
    at = _boot()
    md = _all_markdown(at)
    # Setup-specific amber block has both colors via render_amber_block CSS
    assert "#F59E0B" in md, (
        "Setup amber block missing — render_amber_block emits the F59E0B left "
        "border only when amber_flag_widget is called from Setup tab"
    )
    assert "#FFF7ED" in md
    # ⚠️ emoji appears in widget labels and amber-block content
    assert "⚠️" in md


def test_sensitivity_tornado_renders_plotly_chart() -> None:
    """Sensitivity tab builds + renders a tornado chart with non-empty bars.

    AppTest exposes plotly_chart elements as opaque ``UnknownElement`` whose
    ``.value`` is not introspectable via standard session-state lookup. The
    strongest available check is the integration path:
      (a) ≥2 plotly charts rendered after Sensitivity-tab dispatch
      (b) ``tornado_for_people`` at session-state defaults returns non-empty bars
    If (b) is empty and (a) still passes, that's the silent-empty regression.
    """
    at = _boot()
    plotly_charts = at.get("plotly_chart")
    assert len(plotly_charts) >= 2, (
        f"Expected ≥2 Plotly charts (break-even + tornado), got {len(plotly_charts)}"
    )

    # Direct engine assertion to catch the silent-empty case AppTest can't see
    from roi_calc.sensitivity import tornado_for_people
    bars = tornado_for_people(at.session_state["people_inputs"])
    assert len(bars) > 0, (
        "tornado_for_people returned no bars at session-state defaults — "
        "Sensitivity tab would render an empty figure"
    )
    # Must have at least some non-orphan bars (live engine fields swinging)
    live_bars = [b for b in bars if not b.is_orphan]
    assert len(live_bars) > 0, "All tornado bars are orphan — no live sensitivity"


# ---------------------------------------------------------------------------
# 5. Mode toggle integration
# ---------------------------------------------------------------------------

def test_app_toggle_to_engineering_swaps_tabs() -> None:
    """Mode toggle changes the tab set from 7 (People) to 6 (Engineering)."""
    at = _boot()
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    assert at.session_state["mode"] == "Engineering"
    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == [
        "Setup", "Results", "Sensitivity", "Assessment",
        "Inputs Review", "Bridge Appendix",
    ]


def test_engineering_mode_shows_344k_instability_tax() -> None:
    """Engineering Results tab shows the $344K reproduction.

    Positive-sign check: a sign-swapped regression would render "-$344,000"
    which contains "344000" as substring — vacuous-pass risk. Assert the
    underlying session_state value is positive AND the rendered string
    contains the positive form (no leading minus).
    """
    at = _boot()
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    md = _all_markdown(at)
    # Positive-sign + format check (rendered string)
    assert "$344,000" in md or "$344K" in md
    assert "-$344,000" not in md and "-$344K" not in md
    # Direct metric-value check — st.metric(value=...) is the rendered UI element
    instability_metrics = [
        m for m in at.metric if "Instability Tax" in str(m.label)
    ]
    assert instability_metrics, "No 'Instability Tax' metric rendered"
    metric_value = str(instability_metrics[0].value)
    assert not metric_value.startswith("-"), (
        f"Instability tax metric rendered with negative sign: {metric_value!r}. "
        "Sign-swap regression in the formatter."
    )


def test_dl14_engineering_shows_v3_pending_not_archetype_dollars() -> None:
    """DL-14 Option B: archetype + capability multipliers render as v3-pending
    sentinels, NOT as dollar values.

    The "archetype-adjusted" header is rendered via ``st.subheader``, which
    AppTest exposes as ``at.subheader`` (NOT ``at.markdown``). Walking ALL
    text element collections (info + subheader + markdown) so the assertion
    actually runs.
    """
    at = _boot()
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    md = _all_markdown(at)
    assert "v3-calibration pending" in md

    # DL-14 requires BOTH archetype_adjusted_status AND capability_adjusted_status
    # info blocks carry the sentinel. md.count >= 2 would count the intro paragraph
    # too (total 3) — count info blocks specifically.
    info_v3_count = sum(
        1 for i in at.info if "v3-calibration pending" in str(i.value)
    )
    assert info_v3_count >= 2, (
        f"Expected ≥2 info blocks with 'v3-calibration pending' sentinel "
        f"(archetype + capability), got {info_v3_count}"
    )

    # Verify the archetype-adjusted concept is rendered (subheader)
    subheader_texts = [str(s.value).lower() for s in at.subheader]
    assert any("archetype-adjusted" in s for s in subheader_texts), (
        "No 'Archetype-adjusted portfolio' subheader — Phase 10 Results tab regressed"
    )


def test_b4_engineering_j_curve_uses_real_engineering_annual_value() -> None:
    """Stream B4: Engineering Mode J-Curve renders with engineering_annual_value
    (v3 §5.1 productivity formula) — NOT the People-Mode placeholder.

    The placeholder previously rendered People Mode's $472,503 portfolio (via a
    ``PeopleInputs()`` instantiation inside the Engineering Results tab). This
    test guards against that pattern coming back: the Engineering tab must show
    the real "Engineering annual net value" metric (~$199,682 at defaults) and
    must NOT carry the placeholder caption.
    """
    at = _boot()
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    md = _all_markdown(at)

    # Real metric — engineering-specific annual net value
    eng_value_metrics = [
        m for m in at.metric if "Engineering annual net value" in str(m.label)
    ]
    assert eng_value_metrics, (
        "No 'Engineering annual net value' metric — B4 J-Curve regression "
        "(possibly reverted to People-Mode placeholder)"
    )
    # At v3 §5.1 defaults the formula produces ~$199,682
    metric_value = str(eng_value_metrics[0].value)
    assert "$199,68" in metric_value or "$199,69" in metric_value, (
        f"Engineering annual net value metric not in expected range: {metric_value!r}"
    )

    # Placeholder text must be gone — these phrases ONLY appeared in the
    # pre-B4 placeholder caption.
    assert "structural placeholder" not in md, (
        "B4 regression: Engineering J-Curve still rendering 'structural placeholder' "
        "language (was People-Mode default trajectory placeholder)"
    )
    assert "uses the People-Mode default trajectory" not in md


def test_gate12_bridge_appendix_renders_in_engineering_mode() -> None:
    """Gate 12: Bridge Appendix in BOTH modes. Specifically asserts the
    Engineering-mode render contains the Bridge header + the v4.2 row-8 text."""
    at = _boot()
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    md = _all_markdown(at)
    # Bridge Appendix header (rendered via st.header)
    assert "DORA → CFO Transform" in md
    # v4.2 row 8 markers
    assert "decorative — Day-90 calibration" in md
    assert "no source-verified coefficient" in md


def test_dl13_user_centric_focus_le_2_triggers_gate_error() -> None:
    """Assessment radar + Engineering Results both fire on user_centric_focus ≤ 2."""
    at = _boot()
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    ucf = next(s for s in at.slider if s.key == "eng_ucf")
    ucf.set_value(2)
    at.run()
    md = _all_markdown(at)
    # Engineering Results tab shows "gate triggered" error block
    assert "gate triggered" in md.lower() or "gate active" in md.lower()


def test_dl22_mode_toggle_invalidates_prior_portfolio() -> None:
    """DL-22: toggling away from People clears people_portfolio."""
    at = _boot()
    # Populate People portfolio
    calc = next(b for b in at.button if b.key == "people_calculate")
    calc.click()
    at.run()
    assert at.session_state["people_portfolio"] is not None

    # Toggle to Engineering — DL-22 should invalidate people_portfolio
    mode_radio = next(r for r in at.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at.run()
    assert at.session_state["people_portfolio"] is None


# ---------------------------------------------------------------------------
# 6. Footer persistence
# ---------------------------------------------------------------------------

def test_footer_renders_in_both_modes() -> None:
    """Spec §8.5: persistent footer in both modes. Mode-aware content.

    Both branches of the check execute unconditionally — no vacuous ternary.
    """
    # People mode
    at = _boot()
    people_md = _all_markdown(at)
    # v7: dropped "Built around the gap, not over it" rhetorical opener.
    # Footer now leads directly with the published-research summary.
    assert "Hard-dollar calculations come from published HR research" in people_md
    assert "Day 90" in people_md  # Gate 13 sentence
    # EY must not appear in the People footer slice specifically
    # (Capability/Confidence Audit tabs may legitimately mention EY removal)
    from ui.footer import PEOPLE_MODE_FOOTER
    assert "EY" not in PEOPLE_MODE_FOOTER  # source-of-truth check

    # Engineering mode
    at2 = _boot()
    mode_radio = next(r for r in at2.segmented_control if r.key == "mode_segmented")
    mode_radio.set_value("Engineering")
    at2.run()
    eng_md = _all_markdown(at2)
    assert "DORA J-Curve and instability tax" in eng_md
    assert "METR 2025 RCT" in eng_md
