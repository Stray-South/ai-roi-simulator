"""Citations and constants for the AI ROI Simulator.

Every numeric anchor and calibrated parameter lives here as a frozen ``Citation``
so the Confidence Audit tab (Phase 9) can iterate ``CITATIONS`` and render
source / tier / amber-flag without name-lookup.

Cascade-locked decisions (see ``docs/DECISION_LOG.md``):
  * DL-1  — ``PIPELINE_PER_REQ = 5`` (spec patch from 50)
  * DL-3  — ``RAMP_FLOOR``, ``IMPLEMENTATION_SETUP_PER_EMPLOYEE``,
            ``IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR`` lifted from §6.1
            inline literals into named T5 amber constants
  * DL-16 — ``TRAINING_COEFFICIENT`` deliberately absent (EY anchor failed
            source verification; regression test guards against re-introduction)
  * DL-21 — ``DROPOUT_*`` split into three Citations with tiers T1/T2/T2
            (Conservative RCT / Realistic survey-mid / Aggressive survey-upper)
  * DL-23 — both ``SAMPLE_ORG_EMPLOYEES`` and ``SAMPLE_ORG_CONSOLIDATED_HEADCOUNT``
            carried for scope clarity
  * Cascade 5 — ``Citation.value`` is ``int | float`` only (no str, no dict)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Tier = Literal["T1", "T2", "T3", "T4", "T5"]


@dataclass(frozen=True)
class Citation:
    value: int | float
    source: str
    tier: Tier
    flag: str | None = None

    def __post_init__(self) -> None:
        # Runtime enforcement of the type contract (Cascade 5 — no str / dict / list values).
        # Python annotations are not enforced at construction; without this, a Citation
        # could be built with a string-typed value and would only be caught at test time.
        # `bool` is a subclass of `int` in Python; reject it explicitly.
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise TypeError(
                f"Citation.value must be int or float, got {type(self.value).__name__}: {self.value!r}"
            )


# ---------------------------------------------------------------------------
# Universal verification tax (the single most-defensible number in the model)
# ---------------------------------------------------------------------------

VERIFICATION_TAX_RATE = Citation(
    value=0.37,
    source="Workday/Hanover Research 2024 (n=3,200; HR called out as highest-rework function)",
    tier="T1",
)

# ---------------------------------------------------------------------------
# HR help desk anchors (Unthread 2025) — §3.2 / §5.1
# ---------------------------------------------------------------------------

TICKETS_PER_EMPLOYEE_PER_YEAR = Citation(value=26, source="Unthread HR help desk 2025", tier="T2")
TICKET_COST_AGENT = Citation(value=13.50, source="Unthread 2025 — human-handled ticket", tier="T2")
TICKET_COST_AI = Citation(value=0.50, source="Unthread 2025 — AI-deflected ticket", tier="T2")
HELP_DESK_DEFLECTION_RATE = Citation(
    value=0.425,
    source="Unthread 2025 — midpoint of 40-45% deflection range",
    tier="T2",
)
# Informational anchors from §3.2 — not used in §5 calcs but surfaced in
# Confidence Audit so the published-anchor inventory is complete.
HELPDESK_RESOLUTION_MEDIAN_HOURS = Citation(
    value=82,
    source="Unthread 2025 — median HR ticket resolution time (hours)",
    tier="T2",
)
HELPDESK_RESOLUTION_TOP_PERFORMER_HOURS = Citation(
    value=17,
    source="Unthread 2025 — top-performer HR ticket resolution time (hours)",
    tier="T2",
)

# ---------------------------------------------------------------------------
# Onboarding anchors (Mewayz 2026) — §3.2 / §5.2
# ---------------------------------------------------------------------------

ONBOARDING_WEEKS_BASELINE = Citation(value=8.5, source="Mewayz 2026 — unautomated cohort", tier="T2")
ONBOARDING_WEEKS_AUTOMATED = Citation(value=5.9, source="Mewayz 2026 — automation cohort", tier="T2")

# ---------------------------------------------------------------------------
# Benefits anchors (Beneration Nov 2025) — §3.2 / §5.3
# ---------------------------------------------------------------------------

BENEFITS_EXPOSURE_PER_500 = Citation(
    value=1_000_000,
    source="Beneration Nov 2025 — discrepancy exposure per 500 employees",
    tier="T2",
)
BENEFITS_RECOVERY_PCT = Citation(
    value=0.20,
    source="calibrated conservative — AI-assisted enrollment verification captures fraction of exposure",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — RECOVERY %]",
)

# ---------------------------------------------------------------------------
# Candidate pipeline anchors (SHRM 2025 + Greenhouse) — §3.1 / §5.4
# ---------------------------------------------------------------------------

COST_PER_HIRE_NONEXEC = Citation(
    value=5_475,
    source="SHRM 2025 Recruiting Benchmarking — non-executive cost per hire",
    tier="T2",
)

# DL-1 patch: spec §5.4 had pipeline_per_req=50 in code but ~$756K stated expected
# output only reconciles at 5. At 50, portfolio nets to −$6.3M (demo-breaking).
PIPELINE_PER_REQ = Citation(
    value=5,
    source="calibrated industry rough 3:1-10:1 candidates-per-requisition ratio (PATCHED from spec's 50, DL-1)",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — INDUSTRY ROUGH ESTIMATE]",
)

# DL-21: Conservative is Greenhouse 2025 RCT (T1); Realistic + Aggressive are
# survey-derived midpoint and upper bound (T2 per §2 source authority hierarchy).
DROPOUT_CONSERVATIVE = Citation(
    value=0.12,
    source="Greenhouse 2025 RCT — candidate dropout, conservative anchor",
    tier="T1",
)
DROPOUT_REALISTIC = Citation(
    value=0.22,
    source="Greenhouse 2025 survey — midpoint between RCT 12% and survey-upper 31%",
    tier="T2",
)
DROPOUT_AGGRESSIVE = Citation(
    value=0.31,
    source="Greenhouse 2025 survey — upper-bound dropout",
    tier="T2",
)

# ---------------------------------------------------------------------------
# T·T·D primitives — §4.2, §5.5 (all T5 amber per spec)
# ---------------------------------------------------------------------------

ONBOARDING_TOUCHES_PER_EVENT_BASELINE = Citation(
    value=12,
    source="calibrated — IT access + HRIS profile + benefits + I-9 + payroll + ID badge + training + manager intro + ITSec + comp ack + handbook + compliance attestation",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — T·T·D PRIMITIVE]",
)
ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE = Citation(
    value=18.0,
    source="calibrated — 18 min × 12 touches ≈ 3.6 hr per onboarding, consistent with Workday/SHRM 30-90 min/event range",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — T·T·D PRIMITIVE]",
)
DECISION_POINTS_PER_EVENT = Citation(
    value=4,
    source="calibrated T·T·D primitive — I-9 verification, comp band, security access tier, regulatory attestation",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — T·T·D PRIMITIVE]",
)
DECISION_POINT_ERROR_COST = Citation(
    value=5_000,
    source="calibrated — EEOC $365K full-bias-incident / 73 ≈ low-end admin remediation floor",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — T·T·D PRIMITIVE]",
)

# ---------------------------------------------------------------------------
# AI automation parameters — §4.3 (mostly T2; error-rate primitives T5 amber)
# ---------------------------------------------------------------------------

TOUCHES_AUTOMATED_PCT = Citation(
    value=0.55,
    source="Workday Frontline Agent Sep 2025 — up to 90% on staffing changes; 55% is mid-conservative for full onboarding (not all touches automatable)",
    tier="T2",
)
TIME_PER_TOUCH_REDUCTION_PCT = Citation(
    value=0.40,
    source="Workday Recruiter Agent — mid-conservative of 57% screening time reduction",
    tier="T2",
)
DP_ERROR_RATE_BASELINE = Citation(
    value=0.03,
    source="calibrated — no published HR-specific decision-point error rate",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — AI AUTOMATION RATE]",
)
DP_ERROR_RATE_WITH_AI = Citation(
    value=0.045,
    source="calibrated — 0.03 baseline + 50% relative increase → 0.045. DORA CFR analog (0.05 → 0.06 = +20% relative) used as structural pattern only; this model widens the relative jump because regulated-fintech decision-point errors carry compliance tail risk that DORA's engineering CFR does not",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — MIRRORS DORA CFR PATTERN]",
)

# ---------------------------------------------------------------------------
# J-Curve timing — §4.4 (all T5 amber)
# ---------------------------------------------------------------------------

LEARNING_CURVE_MONTHS = Citation(
    value=6,
    source="DORA engineering default; healthcare RCM RPA 12-18 month payback (n=473) is closest HR analog but not direct",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — ENGINEERING ANALOG]",
)
TIME_TO_STEADY_STATE_MONTHS = Citation(
    value=12,
    source="DORA engineering default — calibrated from engineering analog",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — ENGINEERING ANALOG]",
)
# HORIZON_MONTHS is a finance convention (NPV window), not an HR-data calibration.
# Spec §2 strict rule is relaxed here for the one finance-convention case; the
# `[CALIBRATED — ...]` prefix is preserved so amber-flag detection still works.
HORIZON_MONTHS = Citation(
    value=24,
    source="standard analysis window — 24-month NPV horizon (finance convention, not HR-data calibration)",
    tier="T5",
    flag="⚠️ [CALIBRATED — STANDARD 24-MONTH NPV WINDOW]",
)

# DL-3 lifts: spec §6.1 had these as inline literals; surfaced into Confidence Audit.
RAMP_FLOOR = Citation(
    value=0.35,
    source="calibrated — savings ramp floor at end of learning curve (engineering analog)",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — ENGINEERING ANALOG]",
)
IMPLEMENTATION_SETUP_PER_EMPLOYEE = Citation(
    value=50,
    source="calibrated — one-time implementation setup cost per employee",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — IMPLEMENTATION COST]",
)
IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR = Citation(
    value=30,
    source="calibrated — annual recurring implementation cost per employee",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — IMPLEMENTATION COST]",
)

# ---------------------------------------------------------------------------
# Capability multiplier reference (Gallup) — §4.5 (decorative-only per DL-8/24)
# ---------------------------------------------------------------------------

# Listed for Confidence Audit transparency. Engine treats multiplier as 1.0 in v1
# under Option D; Day-90 calibration replaces with org-measured baselines.
MANAGER_MULTIPLIER_MAX = Citation(
    value=8.7,
    source="Gallup State of Global Workplace 2026 — likelihood ratio for 'AI transformed work' (NOT a productivity multiplier; decorative-only under Option D)",
    tier="T1",
)

# ---------------------------------------------------------------------------
# Compliance / bias-incident reference — §3.1 (EEOC) — T1
# ---------------------------------------------------------------------------

EEOC_BIAS_FLOOR = Citation(
    value=365_000,
    source="EEOC iTutorGroup 2023 enforcement — bias-incident penalty floor",
    tier="T1",
)

# ---------------------------------------------------------------------------
# Sample organization anchors — illustrative defaults for a mid-market
# regulated consumer-finance lender. Replace with your organization's
# measured values (10-K disclosure, HRIS, payroll system) at Day 90.
# ---------------------------------------------------------------------------

# Carry both headcounts: the operating-subsidiary headcount drives the calcs;
# the consolidated headcount is referenced in the $124,615 cost-per-FTE
# derivation (personnel cost line / consolidated headcount).
SAMPLE_ORG_EMPLOYEES = Citation(
    value=1_151,
    source="Sample default — operating-subsidiary headcount of a mid-market "
           "regulated consumer-finance lender. Replace with your organization's "
           "10-K Item 1 disclosure or HRIS headcount.",
    tier="T1",
)
SAMPLE_ORG_CONSOLIDATED_HEADCOUNT = Citation(
    value=1_235,
    source="Sample default — consolidated headcount of the same parent (operating "
           "subsidiary + smaller subsidiaries). Used only in the loaded-cost-per-FTE "
           "derivation. Replace with your consolidated 10-K headcount.",
    tier="T1",
)
SAMPLE_ANNUAL_HIRES = Citation(
    value=230,
    source="Sample default — derived as ~20% of subsidiary headcount, consistent "
           "with SHRM/JOLTS regulated-services turnover range (15-25%). Replace "
           "with your organization's last-12-months hire count.",
    tier="T2",
)
SAMPLE_LOADED_COST_PER_FTE = Citation(
    value=124_615,
    source="Sample default — representative loaded cost per FTE for a "
           "mid-market regulated consumer-finance lender (derived from a "
           "personnel cost line ÷ consolidated headcount). Replace with "
           "your organization's personnel cost ÷ consolidated headcount.",
    tier="T1",
)

# BLS OEWS May 2024 SOC 13-1071 (HR Specialists) + SOC 15-1232 (Computer Support)
# + SOC 11-3121 (HR Managers), each × 1.30 fully-loaded burden / 2,080 hours.
HR_SPECIALIST_LOADED_HOURLY = Citation(
    value=49.83,
    source="BLS OEWS May 2024 SOC 13-1071 (HR Specialists) national mean $79,730 "
           "x 1.30 fully-loaded burden / 2,080 hr = $49.83/hr. Exact-confirm against "
           "BLS bulk oesm24nat.zip; reconciles to OOH May 2024 median $72,910.",
    tier="T1",
)
IT_SPECIALIST_LOADED_HOURLY = Citation(
    value=40.62,
    source="BLS OEWS May 2024 SOC 15-1232 (Computer User Support Specialists) national "
           "mean $64,990 x 1.30 fully-loaded burden / 2,080 hr = $40.62/hr. 15-1232 is "
           "general IT help desk (distinct from 15-1231 network support). Exact-confirm "
           "against BLS bulk oesm24nat.zip; reconciles to OOH May 2024 median $60,340.",
    tier="T1",
)
HR_MANAGER_LOADED_HOURLY = Citation(
    value=100.30,
    source="BLS OEWS May 2024 SOC 11-3121 (HR Managers) national mean $160,480 "
           "x 1.30 fully-loaded burden / 2,080 hr = $100.30/hr. Prior $87.52 used the "
           "MEDIAN ($140,030) mislabeled as mean. Exact-confirm against BLS bulk "
           "oesm24nat.zip; reconciles to OOH May 2024 median $140,030.",
    tier="T1",
)


# ---------------------------------------------------------------------------
# Engineering Mode anchors (Phase 4 / v3 §4-5 — Option B per DL-14)
# ---------------------------------------------------------------------------

# DL-9 / DL-10: defaults that exactly reproduce DORA's $344K figure.
# DORA's own term for this construct is "verification tax"; "instability tax"
# is third-party phrasing used in some secondary sources. Phase 14 A2 reframes
# our public-facing copy to claim reproduction only, not derivation.
# 0.01 (CFR delta) × 100 (deploys) × $344,000 (incident) = $344,000.
DEPLOYS_PER_YEAR_DORA = Citation(
    value=100,
    source="DL-9 — cleanest deploys default that reproduces DORA $344K with incident_cost=$344,000",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO PUBLISHED HR DATA — DORA SAMPLE]",
)
INCIDENT_COST_DORA = Citation(
    value=344_000,
    source="DORA 2026 ROI Calculator output under DORA's own default assumptions "
           "(CFR delta 0.01, deploys_per_year=100): $344K annual figure. DORA's own "
           "term for this construct is 'verification tax'. We reproduce the published "
           "figure as the Engineering-Mode credibility check; this is NOT an "
           "independent derivation, NOT a measured constant, and NOT dependent on any "
           "secondary source's reading of DORA's internal math. (Phase 14 A2 reframe; "
           "supersedes earlier 'reverse-engineered' framing.)",
    tier="T5",
    flag="⚠️ [CALIBRATED — DORA CALCULATOR OUTPUT REPRODUCED]",
)
# METR 2025 RCT: developers felt +20% productivity but measured −19% — 39pp gap.
# DL-12: rounded to 0.50 self-report discount. METR is a published T3 RCT
# (external primary cited within DORA per spec §2), but the rounding choice
# from 39pp gap to flat 0.50 is the calibration — tier reflects the rounding,
# not the underlying study quality.
METR_SELF_REPORT_DISCOUNT = Citation(
    value=0.50,
    source="METR 2025 RCT (published T3 external primary; cited in DORA Jan 2026) — rounding from 39pp self-report-vs-measured gap to 0.50 is the calibration step (DL-12)",
    tier="T5",
    flag="⚠️ [CALIBRATED — ROUNDED FROM METR 2025 RCT 39pp GAP]",
)
# DORA 2026 sample CFR values — used as defaults so EngineeringInputs reproduces $344K out-of-the-box.
CFR_BEFORE_DORA_SAMPLE = Citation(
    value=0.05,
    source="DORA 2026 ROI Report sample CFR baseline",
    tier="T2",
)
CFR_AFTER_DORA_SAMPLE = Citation(
    value=0.06,
    source="DORA 2026 ROI Report sample CFR post-AI",
    tier="T2",
)
# Sample engineering headcount — not typically disclosed in regulated-lender
# 10-Ks; peer scaling (revenue × industry engineering-density ratio) gives a
# 230-345 band for a mid-market consumer-finance lender; default centered at 300.
ENGINEERS_BENCHMARK = Citation(
    value=300,
    source="Sample default — most regulated consumer-finance lenders don't "
           "disclose engineering headcount in 10-K. Peer-scaling (industry "
           "revenue × engineering density) for a mid-market consumer-finance "
           "lender gives a 230-345 band. Replace with your engineering org's "
           "headcount.",
    tier="T5",
    flag="⚠️ [CALIBRATED — SAMPLE DEFAULT, PEER-SCALING BAND]",
)
# DL-16 follow-up: training_spend_ppt is T5 (no source-verified coefficient
# after EY anchor removal). Citation surfaces the decorative-only status
# in Confidence Audit + drives the amber-flag treatment on the Setup slider.
TRAINING_SPEND_PPT_DECORATIVE = Citation(
    value=1.0,
    source="calibrated T5 — no source-verified HR training-to-productivity coefficient (EY anchor failed verification, DL-16); decorative wrapper under Option D",
    tier="T5",
    flag="⚠️ [CALIBRATED — NO SOURCE-VERIFIED HR TRAINING COEFFICIENT]",
)


# ---------------------------------------------------------------------------
# Engineering Mode v3 §5.1 productivity formula (Phase 14 Stream B2)
# ---------------------------------------------------------------------------

# AI adoption rate. DORA 2025 State of AI in Software Development reports ~90%
# global adoption; calibrated down to 75% for a regulated-lender lens (slower
# org-wide rollout vs. greenfield SaaS). The 0.75 number is the calibration;
# the 90% global figure is the T1 anchor it's calibrated from.
AI_ADOPTION_PCT = Citation(
    value=0.75,
    source="DORA 2025 State of AI in Software Development reports ~90% global "
           "adoption; calibrated to 0.75 as a regulated-consumer-finance-lender "
           "lens — slower org-wide rollout than greenfield SaaS.",
    tier="T5",
    flag="⚠️ [CALIBRATED — DORA 90% GLOBAL → 75% REGULATED-LENDER LENS]",
)
AI_HOURS_PER_WORKDAY = Citation(
    value=2.0,
    source="DORA 2025 State of AI median — engineers spend ~2 hours/workday on AI-augmented work",
    tier="T1",
)
PRODUCTIVITY_GAIN_GREENFIELD = Citation(
    value=0.375,
    source="Stanford SEPP / DORA 2026 ROI Report — greenfield productivity gain range 30-45%; midpoint 37.5%",
    tier="T3",
)
PRODUCTIVITY_GAIN_LEGACY = Citation(
    value=0.10,
    source="Stanford SEPP / DORA 2026 ROI Report — legacy/maintenance work productivity gain ~10%",
    tier="T3",
)
PCT_WORK_GREENFIELD = Citation(
    value=0.30,
    source="calibrated — regulated-lender work mix is mostly legacy maintenance + compliance; "
           "30% greenfield is a conservative starting point pending your org's sprint-tag data",
    tier="T5",
    flag="⚠️ [CALIBRATED — REGULATED-LENDER WORK MIX ESTIMATE]",
)
# DORA Insights publishes a ~15% verification overhead specific to engineering
# AI workflows (code review of AI-generated code). Distinct from People-Mode's
# 0.37 Workday/Hanover universal HR rework tax — different measured population,
# different work type. Both are real; they're different taxes on different work.
ENGINEERING_VERIFICATION_TAX = Citation(
    value=0.15,
    source="DORA Insights — engineering-specific AI verification overhead (code review of AI output); "
           "distinct from People-Mode's 0.37 Workday/Hanover HR rework tax",
    tier="T2",
)
WORKDAYS_PER_YEAR = Citation(
    value=235,
    source="standard — 260 weekdays − 15 PTO − 10 holidays = 235 productive workdays/yr",
    tier="T5",
    flag="⚠️ [CALIBRATED — STANDARD WORKDAY CONVENTION]",
)


# ---------------------------------------------------------------------------
# Audit-surface list — Confidence Audit tab (Phase 9) iterates this directly.
# ---------------------------------------------------------------------------

CITATIONS: list[Citation] = [
    # Universal tax
    VERIFICATION_TAX_RATE,
    # Help desk
    TICKETS_PER_EMPLOYEE_PER_YEAR, TICKET_COST_AGENT, TICKET_COST_AI, HELP_DESK_DEFLECTION_RATE,
    HELPDESK_RESOLUTION_MEDIAN_HOURS, HELPDESK_RESOLUTION_TOP_PERFORMER_HOURS,
    # Onboarding
    ONBOARDING_WEEKS_BASELINE, ONBOARDING_WEEKS_AUTOMATED,
    # Benefits
    BENEFITS_EXPOSURE_PER_500, BENEFITS_RECOVERY_PCT,
    # Pipeline
    COST_PER_HIRE_NONEXEC, PIPELINE_PER_REQ,
    DROPOUT_CONSERVATIVE, DROPOUT_REALISTIC, DROPOUT_AGGRESSIVE,
    # T·T·D
    ONBOARDING_TOUCHES_PER_EVENT_BASELINE, ONBOARDING_AVG_MINUTES_PER_TOUCH_BASELINE,
    DECISION_POINTS_PER_EVENT, DECISION_POINT_ERROR_COST,
    # AI automation
    TOUCHES_AUTOMATED_PCT, TIME_PER_TOUCH_REDUCTION_PCT,
    DP_ERROR_RATE_BASELINE, DP_ERROR_RATE_WITH_AI,
    # J-Curve timing
    LEARNING_CURVE_MONTHS, TIME_TO_STEADY_STATE_MONTHS, HORIZON_MONTHS,
    RAMP_FLOOR, IMPLEMENTATION_SETUP_PER_EMPLOYEE, IMPLEMENTATION_RECURRING_PER_EMPLOYEE_PER_YEAR,
    # Capability reference (decorative)
    MANAGER_MULTIPLIER_MAX,
    # Compliance reference
    EEOC_BIAS_FLOOR,
    # Sample organization anchors
    SAMPLE_ORG_EMPLOYEES, SAMPLE_ORG_CONSOLIDATED_HEADCOUNT, SAMPLE_ANNUAL_HIRES, SAMPLE_LOADED_COST_PER_FTE,
    HR_SPECIALIST_LOADED_HOURLY, IT_SPECIALIST_LOADED_HOURLY, HR_MANAGER_LOADED_HOURLY,
    # Engineering Mode anchors (Phase 4 / DL-9-12-14)
    DEPLOYS_PER_YEAR_DORA, INCIDENT_COST_DORA, METR_SELF_REPORT_DISCOUNT,
    CFR_BEFORE_DORA_SAMPLE, CFR_AFTER_DORA_SAMPLE, ENGINEERS_BENCHMARK,
    TRAINING_SPEND_PPT_DECORATIVE,
    # Engineering Mode v3 §5.1 productivity formula (Phase 14 Stream B2)
    AI_ADOPTION_PCT, AI_HOURS_PER_WORKDAY,
    PRODUCTIVITY_GAIN_GREENFIELD, PRODUCTIVITY_GAIN_LEGACY,
    PCT_WORK_GREENFIELD, ENGINEERING_VERIFICATION_TAX, WORKDAYS_PER_YEAR,
]
