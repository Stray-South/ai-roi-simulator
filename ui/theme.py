"""Theme injection module — v3.

CHANGES from v2:
  * Loads Source Serif 4 + IBM Plex Sans + IBM Plex Mono from Google Fonts
    via a CSS @import at the top of the emitted <style> block. No webfont
    constraint — the canvas always used these fonts.
  * Mode-specific accent swap remains a Python-side <style> override
    (no <script>, which Streamlit sanitizes).

Usage in streamlit_app.py (unchanged from v2):
    from ui.theme import inject_theme
    inject_theme(mode)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import streamlit as st


Mode = Literal["People", "Engineering"]

_CSS_PATH = Path(__file__).parent / "assets" / "theme.css"

# CSS @import emits a real <link rel="stylesheet"> via the cascade — works
# inside a <style> block, doesn't need <script>.
_GOOGLE_FONTS_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2"
    "?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600"
    "&family=IBM+Plex+Sans:wght@400;500;600"
    "&family=IBM+Plex+Mono:wght@400;500"
    "&display=swap');"
)

# Mode-specific :root overrides emitted as a SECOND <style> block.
# CSS cascade resolves to whichever was emitted last.
_ENGINEERING_OVERRIDE = """
:root {
  --accent: #1F2A44;       /* deep navy */
  --accent-soft: #E6E9F0;
}
"""

_PEOPLE_OVERRIDE = """
:root {
  --accent: #B8542F;       /* terracotta — same as theme.css default */
  --accent-soft: #F4E5DC;
}
"""


def inject_theme(mode: Mode) -> None:
    """Inject the design-system CSS exactly once per render pass.

    Emits one combined <style> block containing:
      1. Google Fonts @import (Source Serif 4 · IBM Plex Sans · IBM Plex Mono)
      2. The full theme.css from disk
      3. The mode-specific :root override (terracotta or navy)

    No <script> — st.markdown's sanitizer strips it.
    """
    css = _CSS_PATH.read_text(encoding="utf-8")
    override = _ENGINEERING_OVERRIDE if mode == "Engineering" else _PEOPLE_OVERRIDE

    st.markdown(
        f"<style>{_GOOGLE_FONTS_IMPORT}\n{css}\n{override}</style>",
        unsafe_allow_html=True,
    )
