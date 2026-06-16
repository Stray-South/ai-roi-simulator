# AI ROI Simulator

A defensible-to-CFO framework for calculating the dollar return on
implementing an AI-assisted layer in HR operations at a regulated
consumer-finance lender. Streamlit app, fully self-contained,
methodology adapted from DORA's J-Curve research.

**This is a methodology template, not a tool-vendor ROI claim.** The
amber-flagged parameters in the simulator get replaced with your
organization's measured baselines at Day 90 of an implementation
engagement — that's when this becomes a real ROI projection. Today it's
the framework, defensible to a CFO, that the real numbers plug into.

## What it does

Calculates the dollar return on implementing an AI-assisted layer for
one specific workflow: **Infrastructure Onboarding** — the end-to-end
process of getting a new hire from offer-accept to fully productive.
Five hard-dollar effects, each comparing the current manual workflow
against the same workflow with an AI layer:

| Effect | Direction | Source |
|---|---|---|
| Faster new-hire ramp (8.5 → 5.9 weeks) | +savings | Mewayz 2026 |
| HR help-desk deflection (42.5% of tickets) | +savings | Unthread 2025 |
| Benefits billing recovery (20% of exposure) | +savings | Beneration Nov 2025 |
| Recruiting attrition AI doesn't fix in v1 | −risk | Greenhouse 2025 · SHRM 2025 |
| Decision-point compliance errors (3.0 → 4.5%) | −risk | T·T·D primitive (calibrated) |

Net at sample defaults: **$472,503/year**, break-even at Month 8.
Workday 37% verification tax applied universally.

**Engineering Mode** is a credibility check — the same engine and chart
running on DORA's published engineering data. The $344K instability-tax
tile reproduces DORA's published calculator output exactly with default
inputs. If the engine handles DORA's data correctly, the People-Mode
math (same engine, HR data) is sound.

## Sample defaults

Headline numbers reflect a mid-market regulated consumer-finance lender:

- 1,151 operating-subsidiary employees, 230 hires/year
- $124,615 fully-loaded cost per FTE (personnel cost ÷ consolidated headcount)
- BLS OEWS May 2024 mean-derived hourly rates (HR Specialist $49.83,
  IT Specialist $40.62, HR Manager $100.30, each × 1.30 fully-loaded
  burden ÷ 2,080 hr)

To use the framework against your own organization, replace these
defaults (or override them via the Setup tab inputs) with your 10-K
disclosure or HRIS-measured values.

## Local dev

```bash
# Preferred (sidesteps any system-pyexpat issues):
uv python install 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Fallback:
# python3.12 -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt

streamlit run streamlit_app.py
pytest -q
```

## Deploy

Deploys to [Streamlit Community Cloud](https://share.streamlit.io) (free).

1. New app → connect this repo → entry file `streamlit_app.py`
2. **Click "Advanced settings" → set Python version to 3.12 explicitly.**
   Streamlit Cloud reliably ignores `runtime.txt` as of 2025 and defaults
   new apps to Python 3.13; `numpy==1.26.4` has no 3.13 wheel and the
   deploy will fail with a source-build error without this step.
3. Submit. First-time build takes 2–5 minutes (plotly install dominates).
4. Set visibility to **Public** (no sign-in to view) or whitelist viewer
   emails for private access.

## Stack

- Streamlit 1.57+ (UI, segmented_control)
- pandas 2.2 / numpy 1.26 (engine math)
- plotly 6.7 (break-even chart + tornado)
- pytest 8.3 (393+ tests, pinned values byte-identical)

Single-file install via `requirements.txt`. No database, no secrets, no
external services beyond Google Fonts (Source Serif 4, IBM Plex Sans,
IBM Plex Mono).

## Math integrity guarantees

Three things are pinned and guarded by the test suite:

- **People-Mode portfolio net** = `$472,503` at sample defaults
- **Break-even month** = `8` at sample defaults
- **Engineering Mode instability tax** = `$344,000` (reproduces DORA's
  published calculator output exactly with default inputs)

These pinned values reconcile algebraically — every dollar traces from
`PeopleInputs` defaults through the engine to the asserted test value.
A change that breaks any of these fails CI.

## Design

Light theme, terracotta accent for People Mode, navy accent for
Engineering Mode. Source Serif 4 (editorial headlines), IBM Plex Sans
(body), IBM Plex Mono (numerals). WCAG 2.2 AA contrast verified at
14.3:1 ink-on-bg (AAA). Calibrated parameters render with an amber
⚠ T5 pill and a tinted row — the honesty signal.

## License

MIT — use the framework, fork the methodology, swap in your own data.

## Author

[LF](https://github.com/Stray-South). Built as a portfolio
artifact demonstrating defensible AI ROI calculation methodology for
the regulated-consumer-finance vertical.
