from __future__ import annotations

import copy
import hashlib
import re
import textwrap
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import streamlit.components.v1 as components
from html import escape

from Utils.failure_analysis import retrieve_similar_failures
from Utils.indian_startups import retrieve_similar_indian_startups
from Utils.prediction import predict_startup_success
from Utils.genai import generate_concept_and_risks, generate_detailed_plan
from Utils.pdf_report import generate_pdf_report

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Startup Validator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# DESIGN SYSTEM
# Palette : paper #F1F3EF, ink #14262B, marigold #F2A900,
#           risk #B4382C, ok #1D7A57
# Type    : Bricolage Grotesque (headings) + IBM Plex Sans (body)
# Idea    : a MIXED theme. Light "report" pages for reading, dark panels
#           for the moments that matter (hero, verdict, flowchart).
#           Logos, banners and illustrations are generated as inline SVG.
# =========================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
    --paper: #F1F3EF;
    --surface: #FFFFFF;
    --ink: #14262B;
    --ink-2: #3B4F55;
    --muted: #66787D;
    --line: #D3DAD5;
    --gold: #F2A900;
    --gold-deep: #7A5200;
    --risk: #B4382C;
    --ok: #1D7A57;
    --panel: #14262B;
    --panel-2: #1D3A41;
    --mint: #6EE0B2;
    --display: 'Bricolage Grotesque', 'IBM Plex Sans', system-ui, sans-serif;
    --body: 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

/* ---------- Base ---------- */
html, body, .stApp { background: var(--paper) !important; color: var(--ink); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp div[data-testid="stMarkdownContainer"] { font-family: var(--body); }

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }

.block-container { max-width: 1080px !important; padding: 1.4rem 1.5rem 4rem !important; }

/* ---------- Top bar ---------- */
.nav { display: flex; align-items: center; justify-content: space-between; gap: 16px;
       padding: 6px 0 18px; border-bottom: 1px solid var(--line); margin-bottom: 40px; }
.brand { display: flex; align-items: center; gap: 10px; font-family: var(--display);
         font-weight: 700; font-size: 21px; letter-spacing: -0.01em; color: var(--ink); }
.steps { display: flex; align-items: center; gap: 4px; font-size: 14px; color: var(--muted); }
.step { display: flex; align-items: center; gap: 8px; padding: 4px 8px; }
.step i { width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center;
          justify-content: center; font-style: normal; font-size: 12px; font-weight: 600;
          border: 1.5px solid var(--line); background: var(--surface); }
.step.done i { background: var(--ink); border-color: var(--ink); color: #fff; }
.step.on { color: var(--ink); font-weight: 600; }
.step.on i { background: var(--gold); border-color: var(--gold); color: var(--ink); }
.step-sep { width: 20px; height: 1px; background: var(--line); }

/* ---------- Home hero ---------- */
.hero-title { font-family: var(--display); font-weight: 700; font-size: clamp(38px, 6vw, 68px);
              line-height: 1.04; letter-spacing: -0.025em; color: var(--ink);
              max-width: 840px; margin: 0 0 22px; }
.hero-sub { font-size: 19px; line-height: 1.6; color: var(--ink-2); max-width: 640px; margin: 0; }
.pulse { width: 100%; height: 64px; display: block; margin: 38px 0 26px; }
.pulse path { fill: none; stroke: var(--ink); stroke-width: 2; stroke-linejoin: round;
              vector-effect: non-scaling-stroke; stroke-dasharray: 1; stroke-dashoffset: 0;
              animation: trace 2.4s ease-out; }
@keyframes trace { from { stroke-dashoffset: 1; } }

/* ---------- Sections ---------- */
.section { margin-top: 68px; }
.h2 { font-family: var(--display); font-weight: 650; font-size: 30px; letter-spacing: -0.015em;
      color: var(--ink); margin: 0 0 8px; }
.lede { color: var(--ink-2); font-size: 17px; line-height: 1.6; max-width: 62ch; margin: 0; }
.trio { display: grid; grid-template-columns: repeat(3, 1fr); gap: 36px; margin-top: 28px; }
.trio > div { background: var(--surface); border: 1px solid var(--line); border-radius: 18px; padding: 22px 22px 24px; }
.t3 { font-family: var(--display); font-weight: 650; font-size: 20px; color: var(--ink); margin-bottom: 8px; }
.trio p { margin: 0; color: var(--ink-2); line-height: 1.65; font-size: 15.5px; }

.flow { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 30px; position: relative; }
.flow::before { content: ""; position: absolute; top: 17px; left: 17px; right: 17px; height: 1px;
                background: #fff; opacity: .3; }
.flow > div { position: relative; padding-right: 22px; }
.flow .n { width: 34px; height: 34px; border-radius: 50%; background: var(--gold); color: var(--ink);
           display: flex; align-items: center; justify-content: center; font-weight: 600;
           font-size: 14px; position: relative; z-index: 1; margin-bottom: 14px; }
.flow .ft { font-weight: 600; font-size: 16px; color: #fff; margin-bottom: 4px; }
.flow p { margin: 0; color: rgba(255,255,255,.72); font-size: 14.5px; line-height: 1.55; }

/* ---------- Page headers ---------- */
.page-title { font-family: var(--display); font-weight: 700; font-size: clamp(30px, 4.4vw, 46px);
              letter-spacing: -0.02em; line-height: 1.08; color: var(--ink); margin: 0 0 10px; }
.page-sub { color: var(--ink-2); font-size: 17px; line-height: 1.6; max-width: 62ch; margin: 0 0 30px; }

/* ---------- Input page ---------- */
.tips { border-left: 3px solid var(--gold); padding: 2px 0 2px 20px; margin-top: 30px; }
.tips .tt { font-weight: 600; font-size: 16px; margin-bottom: 10px; color: var(--ink); }
.tips ul { margin: 0; padding-left: 18px; color: var(--ink-2); line-height: 1.75; font-size: 15px; }
.tips .foot { margin-top: 12px; color: var(--muted); font-size: 14px; }

/* ---------- Results: verdict + concept ---------- */
.overview-grid { display: grid; grid-template-columns: minmax(250px, 1fr) 1.9fr; gap: 28px; align-items: start; }
.verdict { background: var(--panel); color: #fff; border-radius: 22px; padding: 30px 26px 24px; text-align: center; }
.dial { width: 100%; max-width: 290px; display: block; margin: 0 auto; }
.dial .track { stroke: rgba(255,255,255,.14); }
.dial .val { stroke-linecap: round; animation: sweep 1.5s cubic-bezier(.2,.7,.2,1); }
@keyframes sweep { from { stroke-dasharray: 0 100; } }
.dial text { font-family: var(--display); }
.dial .pct { font-weight: 700; font-size: 46px; fill: #fff; }
.dial .cap { font-family: var(--body); font-size: 12.5px; fill: rgba(255,255,255,.66); }
.verdict-status { font-family: var(--display); font-weight: 650; font-size: 23px; margin-top: 8px; }
.verdict-status.ok { color: #6EE0B2; }
.verdict-status.risky { color: #FFB4A8; }
.verdict-split { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 22px;
                 padding-top: 18px; border-top: 1px solid rgba(255,255,255,.16); }
.verdict-split b { display: block; font-family: var(--display); font-size: 24px; font-weight: 650; }
.verdict-split span { font-size: 13px; color: rgba(255,255,255,.66); }

.doc { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 28px 30px; }
.doc .lab { font-size: 13px; font-weight: 600; color: var(--muted); margin-bottom: 6px; }
.doc .orig { color: var(--ink-2); font-size: 15.5px; line-height: 1.65; margin: 0 0 26px; }
.doc .sharp { font-size: 18px; line-height: 1.6; color: var(--ink); margin: 0;
              border-left: 3px solid var(--gold); padding-left: 16px; }

.cols2 { display: grid; grid-template-columns: 1fr 1fr; gap: 44px; margin-top: 44px; }
ul.plain { list-style: none; padding: 0; margin: 14px 0 0; }
ul.plain li { padding: 12px 0; border-top: 1px solid var(--line); color: var(--ink-2); line-height: 1.55; }
ul.plain li:last-child { border-bottom: 1px solid var(--line); }
ul.plain li b { color: var(--ink); font-weight: 600; }
ul.plain .sub { color: var(--muted); font-size: 14.5px; margin-top: 2px; }
.pill { display: inline-block; font-size: 12px; font-weight: 600; background: var(--ink); color: #fff;
        border-radius: 999px; padding: 2px 9px; margin-left: 8px; vertical-align: 1px; }

.risk { background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--risk);
        border-radius: 12px; padding: 16px 20px; margin: 0 0 16px; }
.risk .rt { font-weight: 600; font-size: 17.5px; color: var(--ink); margin-bottom: 4px; }
.risk p { margin: 0; color: var(--ink-2); line-height: 1.65; max-width: 76ch; }
.note { color: var(--muted); font-size: 14px; line-height: 1.6; max-width: 70ch; margin-top: 18px; }

.gate { margin-top: 60px; padding-top: 28px; border-top: 2px solid var(--ink); }
.gate .gt { font-family: var(--display); font-weight: 650; font-size: 28px; letter-spacing: -0.01em; margin-bottom: 8px; }

/* ---------- Playbook ---------- */
.imp-head, .imp-row { display: grid; grid-template-columns: 1.4fr 1.6fr 2fr; gap: 28px; }
.imp-head { font-size: 13px; font-weight: 600; color: var(--muted); padding: 0 0 8px;
            border-bottom: 2px solid var(--ink); margin-top: 22px; }
.imp-row { padding: 18px 0; border-bottom: 1px solid var(--line); line-height: 1.55; }
.imp-row .now { color: var(--muted); }
.imp-row .up { color: var(--ink); font-weight: 500; border-left: 3px solid var(--ok); padding-left: 14px; }
.imp-row .why { color: var(--ink-2); }
.imp-row [data-l]::before { display: none; }

.tl { list-style: none; margin: 22px 0 0 8px; padding: 0; }
.tl li { position: relative; padding: 0 0 28px 30px; border-left: 2px solid var(--line); }
.tl li::before { content: ""; position: absolute; left: -9px; top: 2px; width: 16px; height: 16px;
                 border-radius: 50%; background: var(--gold); border: 2px solid var(--ink); }
.tl li:last-child { border-left-color: transparent; padding-bottom: 0; }
.tl .ph { font-weight: 600; font-size: 17.5px; color: var(--ink); }
.tl p { margin: 4px 0 0; color: var(--ink-2); line-height: 1.65; max-width: 72ch; }

/* ---------- Generated art, icons and dark panels (mixed theme) ---------- */
.ico { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px;
       border-radius: 12px; background: var(--panel); flex: none; }
.trio .ico { margin-bottom: 14px; }
.h2i { display: flex; align-items: center; gap: 12px; }
.h2i .ico { width: 38px; height: 38px; border-radius: 10px; }

.hero { display: grid; grid-template-columns: 1.2fr 1fr; gap: 28px; align-items: center;
        background: radial-gradient(900px 420px at 88% 0%, rgba(242,169,0,.18), transparent 60%), var(--panel);
        border-radius: 28px; padding: 52px 48px; color: #fff; overflow: hidden; }
.hero .hero-title { color: #fff; font-size: clamp(34px, 4.6vw, 56px); }
.hero .hero-sub { color: rgba(255,255,255,.78); }
.hero .pulse { margin: 28px 0 0; height: 48px; }
.hero .pulse path { stroke: var(--gold); }
.hero-art { width: 100%; height: auto; display: block; }
.hero-art text { font-family: var(--body); font-weight: 600; }

.band { background: var(--panel); color: #fff; border-radius: 28px; padding: 44px 44px 48px; margin-top: 68px; }
.band .h2 { color: #fff; }
.band .lede { color: rgba(255,255,255,.75); }

.tips-dark { background: var(--panel); color: #fff; border-radius: 22px; padding: 26px 26px 24px; }
.tips-dark svg { display: block; margin: 0 auto 14px; width: 150px; height: auto; }
.tips-dark .tt { font-weight: 600; font-size: 17px; margin-bottom: 10px; color: #fff; }
.tips-dark ul { margin: 0; padding-left: 18px; color: rgba(255,255,255,.84); line-height: 1.8; font-size: 15px; }
.tips-dark .foot { margin-top: 12px; color: rgba(255,255,255,.6); font-size: 14px; }

.cover { position: relative; overflow: hidden; border-radius: 24px; background: var(--panel); color: #fff;
         padding: 34px 36px; display: flex; align-items: center; gap: 22px; min-height: 150px; margin-bottom: 30px; }
.cover .bg { position: absolute; inset: 0; width: 100%; height: 100%; }
.cover .logo, .cover .copy { position: relative; z-index: 1; }
.cover .logo { flex: none; line-height: 0; filter: drop-shadow(0 6px 18px rgba(0,0,0,.35)); }
.cover .ct { font-family: var(--display); font-weight: 700; font-size: clamp(28px, 4vw, 42px);
             letter-spacing: -0.02em; line-height: 1.08; margin: 0 0 6px; }
.cover .cs { color: rgba(255,255,255,.8); font-size: 17px; line-height: 1.55; max-width: 60ch; margin: 0; }

.brandkit { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-top: 22px; }
.bk { background: var(--surface); border: 1px solid var(--line); border-radius: 18px; padding: 26px 20px 22px;
      display: flex; flex-direction: column; align-items: center; gap: 12px; text-align: center; }
.bk .wm { font-family: var(--display); font-weight: 700; font-size: 20px; color: var(--ink); word-break: break-word; }
.bk .tag { font-size: 13px; color: var(--muted); }
.bk.dark { background: var(--panel); border-color: var(--panel); }
.bk.dark .wm { color: #fff; }
.bk.dark .tag { color: rgba(255,255,255,.62); }
.bk.gold { background: var(--gold); border-color: var(--gold); }
.bk.gold .tag { color: rgba(20,38,43,.72); }

ul.plain li.member { display: flex; gap: 14px; align-items: flex-start; }
.member .av { flex: none; line-height: 0; }
.member .ico { width: 36px; height: 36px; border-radius: 10px; }

.flowpanel { background: radial-gradient(700px 300px at 90% 0%, rgba(242,169,0,.15), transparent 65%), var(--panel);
             border: 1px solid #2B4A52; border-radius: 22px; padding: 28px 20px; margin: 4px 0 34px; }
.flowpanel svg { display: block; margin: 0 auto; max-width: 100%; height: auto; }
.flowpanel text { font-family: var(--body); font-size: 14px; font-weight: 500; }

@media (max-width: 860px) {
    .hero { grid-template-columns: 1fr; padding: 36px 26px; }
    .hero-art { max-width: 420px; margin: 0 auto; }
    .brandkit { grid-template-columns: 1fr; }
    .band { padding: 32px 26px 36px; }
}
@media (max-width: 640px) {
    .cover { flex-direction: column; align-items: flex-start; padding: 28px 24px; }
}

/* ---------- Streamlit widget overrides ---------- */
[data-testid="stWidgetLabel"] p { font-weight: 600 !important; font-size: 15px !important; color: var(--ink) !important; }
[data-baseweb="input"], [data-baseweb="textarea"] {
    background: var(--surface) !important; border: 1.5px solid #B9C4BE !important; border-radius: 8px !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: var(--ink) !important; box-shadow: 0 0 0 3px rgba(242,169,0,.38) !important; }
[data-baseweb="base-input"] { background: transparent !important; }
.stTextInput input, .stTextArea textarea { color: var(--ink) !important; background: transparent !important;
    font-size: 16px !important; line-height: 1.6 !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #8A9A9E !important; }

.stButton button, .stDownloadButton button { border-radius: 8px !important; font-weight: 600 !important;
    font-size: 16px !important; padding: 11px 24px !important; min-height: 48px;
    transition: background .15s ease, border-color .15s ease !important; box-shadow: none !important; }
.stButton button p, .stDownloadButton button p { color: inherit !important; font-weight: 600 !important; }

.stButton button[kind="primary"], .stButton button[data-testid="stBaseButton-primary"],
.stDownloadButton button[kind="primary"], .stDownloadButton button[data-testid="stBaseButton-primary"] {
    background: var(--gold) !important; color: var(--ink) !important; border: 1.5px solid var(--gold) !important; }
.stButton button[kind="primary"]:hover, .stButton button[data-testid="stBaseButton-primary"]:hover,
.stDownloadButton button[kind="primary"]:hover, .stDownloadButton button[data-testid="stBaseButton-primary"]:hover {
    background: #FFC21F !important; border-color: var(--ink) !important; color: var(--ink) !important; }

.stButton button[kind="secondary"], .stButton button[data-testid="stBaseButton-secondary"] {
    background: transparent !important; color: var(--ink) !important; border: 1.5px solid var(--ink) !important; }
.stButton button[kind="secondary"]:hover, .stButton button[data-testid="stBaseButton-secondary"]:hover {
    background: var(--ink) !important; color: #fff !important; }

button:focus-visible { outline: 3px solid var(--ink) !important; outline-offset: 2px !important; }
[data-testid="stCaptionContainer"] { color: var(--muted) !important; }
[data-testid="stSpinner"] * { color: var(--ink-2) !important; }

/* ---------- Responsive ---------- */
@media (max-width: 860px) {
    .overview-grid, .cols2 { grid-template-columns: 1fr; }
    .trio { grid-template-columns: 1fr; gap: 26px; }
    .flow { grid-template-columns: 1fr; gap: 22px; }
    .flow::before { display: none; }
}
@media (max-width: 720px) {
    .imp-head { display: none; }
    .imp-row { grid-template-columns: 1fr; gap: 10px; }
    .imp-row [data-l]::before { display: block; content: attr(data-l); font-size: 12.5px;
        font-weight: 600; color: var(--muted); margin-bottom: 2px; }
}
@media (max-width: 640px) {
    .step span { display: none; }
    .step.on span { display: inline; }
    .step-sep { width: 10px; }
}
@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "home",
    "startup_name": "",
    "startup_description": "",
    "failure_results": [],
    "indian_startups": [],
    "prediction_result": {},
    "concept_data": {},
    "plan_data": {},
    "logo_seed": 0,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = copy.deepcopy(v)


def reset_and_go_to_input():
    for key, value in defaults.items():
        st.session_state[key] = copy.deepcopy(value)
    st.session_state.page = "input"


# =========================================================
# CACHED ANALYSIS
# Local retrieval runs concurrently. Completed API-backed results are cached
# for one hour, which makes a repeated idea or a browser refresh instant.
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def run_initial_analysis(startup_description: str):
    with ThreadPoolExecutor(max_workers=2) as executor:
        failures_future = executor.submit(
            retrieve_similar_failures, startup_description, top_k=5
        )
        indian_future = executor.submit(
            retrieve_similar_indian_startups, startup_description, top_k=5
        )
        failure_results = failures_future.result()
        indian_startups = indian_future.result()

    prediction_result = predict_startup_success(
        startup_description,
        failure_results=failure_results,
        indian_startups=indian_startups,
    )
    concept_data = generate_concept_and_risks(
        startup_description,
        prediction_result,
        failure_results,
        indian_startups,
    )
    return failure_results, indian_startups, prediction_result, concept_data


@st.cache_data(ttl=3600, show_spinner=False)
def build_detailed_plan(
    startup_description: str,
    prediction_result: dict,
    failure_results: list,
    indian_startups: list,
):
    return generate_detailed_plan(
        startup_description,
        prediction_result,
        failure_results,
        indian_startups,
    )


# =========================================================
# SMALL HELPERS
# =========================================================

def esc(x) -> str:
    """HTML-escape any value (and neutralise $ so it is never read as math)."""
    return escape("" if x is None else str(x), quote=True).replace("$", "&#36;")


def rich(x) -> str:
    """Escape, then allow **bold** and line breaks from model output."""
    t = esc(x)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t.replace("\n", "<br>")


def md(html: str):
    """Render an HTML snippet (collapsed to one line so Markdown never treats it as code)."""
    st.markdown(" ".join(line.strip() for line in html.strip().splitlines()), unsafe_allow_html=True)


def num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def pct_str(v) -> str:
    v = num(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def plain_list(items) -> str:
    rows = "".join(f"<li>{rich(i)}</li>" for i in (items or []))
    return f'<ul class="plain">{rows}</ul>'


STEP_LABELS = ["Describe idea", "Read verdict", "Build plan"]


def top_bar(active: int | None = None):
    """Brand on the left; progress through the three real stages on the right."""
    steps_html = ""
    if active is not None:
        parts = []
        for i, label in enumerate(STEP_LABELS):
            cls = "done" if i < active else ("on" if i == active else "")
            mark = "✓" if i < active else str(i + 1)
            parts.append(f'<div class="step {cls}"><i>{mark}</i><span>{label}</span></div>')
        steps_html = '<div class="steps">' + '<div class="step-sep"></div>'.join(parts) + "</div>"

    md(
        f"""<div class="nav">
<div class="brand">
{brand_mark(32)}
AI Startup Validator
</div>
{steps_html}
</div>"""
    )


# =========================================================
# GENERATED ART
# Every logo, banner, icon and illustration is built as inline SVG
# from the idea name, so it needs no image files and no network calls.
# =========================================================

LOGO_PALETTES = [
    ("#14262B", "#F2A900", "#FFF3D1"),
    ("#1D7A57", "#FFFFFF", "#C9F2E0"),
    ("#2B3A8F", "#FFD166", "#DDE3FF"),
    ("#B4382C", "#FFF3D1", "#FFD9D2"),
    ("#4B2E83", "#6EE0B2", "#E7DDFB"),
    ("#0F5E73", "#F2A900", "#D5F1F8"),
]
DISPLAY_FONT = "font-family:'Bricolage Grotesque','IBM Plex Sans',system-ui,sans-serif"


def _hash(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)


def initials_of(text: str) -> str:
    """'QuickTutor' -> QT, 'Nova Pay' -> NP, 'agrilog' -> AG."""
    words = re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+", text or "")
    if not words:
        return "AI"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def session_brand_name() -> str:
    """Name used for logos: the idea name, else the first two words of the pitch."""
    if st.session_state.startup_name:
        return st.session_state.startup_name
    words = st.session_state.startup_description.split()[:2]
    return " ".join(words) or "Idea"


def brand_mark(size: int = 32) -> str:
    """The AI Startup Validator logo: a shield with a check."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 30 30" role="img" aria-label="AI Startup Validator logo">'
        '<rect width="30" height="30" rx="8" fill="#14262B"/>'
        '<path d="M15 4.5 L24 8 V15 C24 20 20.2 23.6 15 25.5 C9.8 23.6 6 20 6 15 V8 Z" fill="none" '
        'stroke="#F2A900" stroke-width="1.8" stroke-linejoin="round"/>'
        '<path d="M10.6 15.2 L13.7 18.2 L19.6 11.8" fill="none" stroke="#6EE0B2" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        "</svg>"
    )


def logo_svg(name: str, seed: int = 0, style: int | None = None, size: int = 72) -> str:
    """A generated logo for the idea. Same name + seed always gives the same logo."""
    h = _hash(f"{(name or 'idea').lower()}|{seed}")
    bg, fg, soft = LOGO_PALETTES[h % len(LOGO_PALETTES)]
    kind = (h // 7) % 4 if style is None else style % 4
    ini = esc(initials_of(name))
    uid = f"lg{h % 10**7}{kind}"

    def label(y, fs, fill, x=60):
        return (
            f'<text x="{x}" y="{y}" text-anchor="middle" fill="{fill}" '
            f'style="{DISPLAY_FONT};font-weight:800;font-size:{fs}px;letter-spacing:-1px">{ini}</text>'
        )

    clip = f'<clipPath id="{uid}c"><rect width="120" height="120" rx="32"/></clipPath>'

    if kind == 0:  # soft square with a spark
        body = (
            f"<defs>{clip}</defs>"
            f'<g clip-path="url(#{uid}c)"><rect width="120" height="120" fill="{bg}"/>'
            f'<circle cx="18" cy="112" r="46" fill="{fg}" opacity=".18"/>'
            f'<circle cx="96" cy="26" r="12" fill="{fg}"/></g>'
            + label(76, 46, soft)
        )
    elif kind == 1:  # ring
        body = (
            f'<circle cx="60" cy="60" r="58" fill="{bg}"/>'
            f'<circle cx="60" cy="60" r="47" fill="none" stroke="{fg}" stroke-width="3"/>'
            f'<circle cx="60" cy="13" r="5" fill="{fg}"/>'
            + label(74, 42, soft)
        )
    elif kind == 2:  # hexagon with a pulse line
        body = (
            f'<polygon points="60,4 110,32 110,88 60,116 10,88 10,32" fill="{bg}"/>'
            f'<path d="M26 84 H44 L52 70 L64 98 L72 84 H94" fill="none" stroke="{fg}" stroke-width="4" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            + label(62, 34, soft)
        )
    else:  # split corner
        body = (
            f"<defs>{clip}</defs>"
            f'<g clip-path="url(#{uid}c)"><rect width="120" height="120" fill="{bg}"/>'
            f'<path d="M120 40 V120 H30 Z" fill="{fg}" opacity=".92"/></g>'
            + label(66, 44, soft, x=52)
        )

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" role="img" '
        f'aria-label="Generated logo concept for {esc(name)}">{body}</svg>'
    )


def avatar_svg(label: str, size: int = 40) -> str:
    """Round generated avatar for a team role."""
    h = _hash((label or "role").lower())
    bg, fg, soft = LOGO_PALETTES[h % len(LOGO_PALETTES)]
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" aria-hidden="true">'
        f'<circle cx="20" cy="20" r="20" fill="{bg}"/>'
        f'<circle cx="20" cy="20" r="18" fill="none" stroke="{fg}" stroke-width="1.5"/>'
        f'<text x="20" y="25" text-anchor="middle" fill="{soft}" '
        f'style="{DISPLAY_FONT};font-weight:700;font-size:14px">{esc(initials_of(label))}</text>'
        "</svg>"
    )


def cover_svg(name: str, seed: int = 0) -> str:
    """Generated banner artwork that sits behind the page title."""
    h = _hash(f"{(name or 'idea').lower()}|{seed}")
    bg, fg, soft = LOGO_PALETTES[h % len(LOGO_PALETTES)]
    uid = f"cv{h % 10**7}"
    shift = (h // 11) % 80
    heights = [38, 60, 52, 84, 76, 112, 138]
    bars = "".join(
        f'<rect x="{640 + shift + i * 40}" y="{220 - v}" width="24" height="{v}" rx="6" fill="{soft}" opacity=".14"/>'
        for i, v in enumerate(heights)
    )
    pts = " ".join(f"{652 + shift + i * 40},{206 - v}" for i, v in enumerate(heights))
    end_x, end_y = 652 + shift + 6 * 40, 206 - heights[-1]
    return (
        '<svg class="bg" viewBox="0 0 1000 220" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#14262B"/><stop offset="1" stop-color="{bg}"/></linearGradient>'
        f'<pattern id="{uid}p" width="24" height="24" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1.4" fill="#fff" opacity=".16"/></pattern></defs>'
        f'<rect width="1000" height="220" fill="url(#{uid})"/>'
        f'<rect width="1000" height="220" fill="url(#{uid}p)"/>'
        f'<circle cx="{560 + shift}" cy="30" r="130" fill="{fg}" opacity=".14"/>'
        f'<circle cx="{900 - shift}" cy="210" r="96" fill="{soft}" opacity=".10"/>'
        + bars
        + f'<polyline points="{pts}" fill="none" stroke="{fg}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{end_x}" cy="{end_y}" r="7" fill="{fg}"/>'
        "</svg>"
    )


def cover_html(title: str, sub: str, brand: str, seed: int = 0) -> str:
    return (
        f'<div class="cover">{cover_svg(brand, seed)}'
        f'<div class="logo">{logo_svg(brand, seed, size=84)}</div>'
        f'<div class="copy"><div class="ct">{esc(title)}</div><p class="cs">{esc(sub)}</p></div></div>'
    )


ICON_PATHS = {
    "doc": '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><path d="M10 12h5M10 16h5"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="M16 16l5 5"/><path d="M11 8.5v3l2 1"/>',
    "gauge": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/><circle cx="12" cy="17" r="1.2"/>',
    "map": '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "bulb": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "skill": '<path d="M12 3l2.6 5.6 6 .8-4.4 4.2 1.1 6L12 16.7 6.7 19.6l1.1-6L3.4 9.4l6-.8z"/>',
}


def icon(kind: str) -> str:
    return (
        '<span class="ico"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#F2A900" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        + ICON_PATHS[kind]
        + "</svg></span>"
    )


HERO_ART_SVG = """<svg class="hero-art" viewBox="0 0 480 360" role="img" aria-label="Illustration of a startup dashboard with a survival score, risk list and growth chart">
<defs>
<linearGradient id="ha-bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#2BB8A0"/><stop offset="1" stop-color="#6EE0B2"/></linearGradient>
<linearGradient id="ha-card" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22464F"/><stop offset="1" stop-color="#162E34"/></linearGradient>
</defs>
<circle cx="410" cy="64" r="92" fill="#F2A900" opacity=".12"/>
<circle cx="70" cy="320" r="72" fill="#6EE0B2" opacity=".10"/>
<rect x="24" y="44" width="420" height="270" rx="22" fill="url(#ha-card)" stroke="rgba(255,255,255,.18)"/>
<circle cx="52" cy="70" r="5" fill="#FF8F7E"/><circle cx="70" cy="70" r="5" fill="#F2A900"/><circle cx="88" cy="70" r="5" fill="#6EE0B2"/>
<rect x="46" y="94" width="150" height="10" rx="5" fill="#fff" opacity=".2"/>
<rect x="46" y="112" width="100" height="8" rx="4" fill="#fff" opacity=".1"/>
<rect x="50" y="240" width="28" height="50" rx="6" fill="url(#ha-bar)" opacity=".75"/>
<rect x="94" y="206" width="28" height="84" rx="6" fill="url(#ha-bar)" opacity=".75"/>
<rect x="138" y="224" width="28" height="66" rx="6" fill="url(#ha-bar)" opacity=".75"/>
<rect x="182" y="174" width="28" height="116" rx="6" fill="url(#ha-bar)" opacity=".75"/>
<rect x="226" y="192" width="28" height="98" rx="6" fill="url(#ha-bar)" opacity=".75"/>
<rect x="270" y="138" width="28" height="152" rx="6" fill="url(#ha-bar)"/>
<polyline points="64,224 108,190 152,208 196,158 240,176 284,122" fill="none" stroke="#F2A900" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="284" cy="122" r="7" fill="#F2A900"/><circle cx="284" cy="122" r="12" fill="none" stroke="#F2A900" opacity=".4"/>
<path d="M 322 168 A 48 48 0 0 1 418 168" fill="none" stroke="rgba(255,255,255,.16)" stroke-width="12" stroke-linecap="round"/>
<path d="M 322 168 A 48 48 0 0 1 418 168" pathLength="100" fill="none" stroke="#6EE0B2" stroke-width="12" stroke-linecap="round" stroke-dasharray="72 100"/>
<text x="370" y="166" text-anchor="middle" fill="#fff" style="font-size:26px;font-weight:700">72%</text>
<text x="370" y="188" text-anchor="middle" fill="rgba(255,255,255,.66)" style="font-size:11px;font-weight:500">survival score</text>
<circle cx="330" cy="228" r="5" fill="#FF8F7E"/><rect x="342" y="223" width="86" height="10" rx="5" fill="#fff" opacity=".2"/>
<circle cx="330" cy="252" r="5" fill="#F2A900"/><rect x="342" y="247" width="66" height="10" rx="5" fill="#fff" opacity=".2"/>
<circle cx="330" cy="276" r="5" fill="#6EE0B2"/><rect x="342" y="271" width="78" height="10" rx="5" fill="#fff" opacity=".2"/>
<rect x="318" y="12" width="140" height="34" rx="17" fill="#F2A900"/>
<text x="388" y="34" text-anchor="middle" fill="#14262B" style="font-size:12.5px">Risk found: cash runway</text>
<rect x="6" y="302" width="130" height="34" rx="17" fill="#fff"/>
<text x="71" y="324" text-anchor="middle" fill="#14262B" style="font-size:12.5px">Plan ready ✓</text>
</svg>"""

TIPS_ART_SVG = """<svg viewBox="0 0 160 110" role="img" aria-label="Light bulb illustration">
<circle cx="80" cy="52" r="46" fill="#F2A900" opacity=".12"/>
<circle cx="80" cy="52" r="32" fill="#F2A900" opacity=".18"/>
<circle cx="80" cy="50" r="22" fill="#F2A900"/>
<path d="M70 66 H90 L88 78 H72 Z" fill="#F2A900"/>
<rect x="70" y="80" width="20" height="5" rx="2.5" fill="#FFF3D1"/>
<rect x="73" y="87" width="14" height="5" rx="2.5" fill="#FFF3D1"/>
<path d="M73 50 l7 7 l7 -7" fill="none" stroke="#14262B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M20 50 H30 M130 50 H140 M36 14 L43 21 M124 14 L117 21 M36 86 L43 79 M124 86 L117 79" fill="none" stroke="#6EE0B2" stroke-width="3" stroke-linecap="round"/>
</svg>"""


def hero_art_svg() -> str:
    return HERO_ART_SVG


def tips_art_svg() -> str:
    return TIPS_ART_SVG


# =========================================================
# FLOWCHART
# The Mermaid text is parsed and drawn as inline SVG. Its size is known
# in Python, so it sits in the normal page flow: nothing overflows,
# nothing scrolls and nothing can cover the text below it.
# If the text can't be parsed, a scaled-to-fit Mermaid frame is the fallback.
# =========================================================

_FC_SHAPES = [
    ("((", "))", "circle"),
    ("([", "])", "stadium"),
    ("[[", "]]", "rect"),
    ("{{", "}}", "hex"),
    ("[(", ")]", "rect"),
    ("[/", "/]", "rect"),
    ("[\\", "\\]", "rect"),
    ("[", "]", "rect"),
    ("(", ")", "round"),
    ("{", "}", "diamond"),
    (">", "]", "rect"),
]
_FC_ID = re.compile(r"[A-Za-z0-9_]+")
_FC_CLASS = re.compile(r":::[\w-]+")
_FC_ARROW = re.compile(r"(?:<)?(?:-{2,}>|-{3,}|={2,}>|={3,}|-\.+->|-\.+-)(?:\s*\|([^|]*)\|)?")
_FC_ARROW_TEXT = re.compile(r"(?:--|==|-\.)\s+(.+?)\s+(?:-->|---|==>|===|\.->|\.-)")
_FC_SKIP = re.compile(r"^(subgraph|direction|classDef|class|style|linkStyle|click|accTitle|accDescr)\b")


def _fc_clean(text: str) -> str:
    t = text.strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        t = t[1:-1]
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("#quot;", '"').replace("`", "")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _fc_split(code: str):
    """Split into statements on newlines and on ';' that is outside brackets and quotes."""
    out, buf, depth, quote = [], [], 0, False
    for ch in code:
        if ch == '"':
            quote = not quote
        if not quote:
            if ch in "[({":
                depth += 1
            elif ch in "])}":
                depth = max(0, depth - 1)
        if (ch == "\n" and not quote) or (ch == ";" and depth == 0 and not quote):
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return out


def _fc_read_node(s: str, pos: int):
    m = _FC_ID.match(s, pos)
    if not m:
        return None
    nid, pos = m.group(0), m.end()
    label, shape = None, None
    for op, cl, shp in _FC_SHAPES:
        if s.startswith(op, pos):
            start = pos + len(op)
            if start < len(s) and s[start] == '"':
                q = s.find('"', start + 1)
                end = s.find(cl, q + 1) if q != -1 else -1
            else:
                end = s.find(cl, start)
            if end == -1:
                break
            label, shape = _fc_clean(s[start:end]), shp
            pos = end + len(cl)
            break
    return nid, label, shape, pos


def _fc_parse_statement(s: str, nodes: dict, edges: list):
    def skip_ws(p):
        while p < len(s) and s[p] in " \t":
            p += 1
        return p

    def read_group(p):
        group = []
        while True:
            p = skip_ws(p)
            r = _fc_read_node(s, p)
            if not r:
                return group, p
            nid, label, shape, p = r
            mc = _FC_CLASS.match(s, p)
            if mc:
                p = mc.end()
            if nid not in nodes:
                nodes[nid] = {"label": label or nid, "shape": shape or "rect"}
            elif label is not None:
                nodes[nid] = {"label": label, "shape": shape or "rect"}
            group.append(nid)
            p = skip_ws(p)
            if p < len(s) and s[p] == "&":
                p += 1
                continue
            return group, p

    group, pos = read_group(0)
    while group and pos < len(s):
        pos = skip_ws(pos)
        m = _FC_ARROW.match(s, pos)
        if m:
            label = m.group(1) or ""
        else:
            m = _FC_ARROW_TEXT.match(s, pos)
            if not m:
                break
            label = m.group(1)
        dashed = "." in m.group(0)[:4]
        nxt, pos = read_group(m.end())
        if not nxt:
            break
        for a in group:
            for b in nxt:
                edges.append((a, b, _fc_clean(label), dashed))
        group = nxt


def _parse_flowchart(code: str):
    """Return (nodes, edges, horizontal) or None if the text isn't a flowchart we can draw."""
    nodes, edges, horizontal = {}, [], False
    for raw in _fc_split(code):
        line = raw.strip()
        if not line or line.startswith("%%") or line == "end":
            continue
        head = re.match(r"^(?:graph|flowchart)\b\s*(TD|TB|BT|LR|RL)?", line, re.I)
        if head:
            horizontal = (head.group(1) or "").upper() in ("LR", "RL")
            continue
        if _FC_SKIP.match(line):
            continue
        _fc_parse_statement(line, nodes, edges)
    if len(nodes) < 2 or not edges:
        return None
    return nodes, edges, horizontal


def _flowchart_svg(nodes: dict, edges: list, horizontal: bool) -> str:
    FS, LH, CW = 14, 18, 8.2
    PAD, GAP = 28, 34
    RANK_GAP = 96 if horizontal else 66
    f1 = lambda v: f"{v:.1f}"

    # ---- node sizes from their wrapped text
    size, lines_of = {}, {}
    for nid, nd in nodes.items():
        shape = nd["shape"]
        maxc = 20 if shape == "diamond" else 24
        lines = []
        for para in str(nd["label"]).split("\n"):
            lines += textwrap.wrap(para, width=maxc, break_long_words=True) or [""]
        if len(lines) > 4:
            lines = lines[:4]
            lines[3] = lines[3][: maxc - 3].rstrip() + "..."
        tw, th = max(len(l) for l in lines) * CW, len(lines) * LH
        if shape == "diamond":
            w, h = max(150, tw * 1.5 + 36), max(72, th * 1.7 + 30)
        elif shape == "circle":
            w, h = max(96, tw + 52), max(64, th + 38)
        elif shape == "hex":
            w, h = max(120, tw + 54), max(48, th + 26)
        else:
            w, h = max(112, tw + 36), max(46, th + 26)
        size[nid], lines_of[nid] = (w, h), lines

    # ---- clean edge list, find loop-back edges
    ids = list(nodes)
    seen, es = set(), []
    for a, b, lab, dashed in edges:
        if a == b or a not in nodes or b not in nodes or (a, b) in seen:
            continue
        seen.add((a, b))
        es.append((a, b, lab, dashed))

    out, indeg = {i: [] for i in ids}, {i: 0 for i in ids}
    for a, b, _, _ in es:
        out[a].append(b)
        indeg[b] += 1
    state, back = {}, set()

    def dfs(u):
        state[u] = 1
        for v in out[u]:
            if state.get(v) == 1:
                back.add((u, v))
            elif v not in state:
                dfs(v)
        state[u] = 2

    for i in [n for n in ids if indeg[n] == 0] + ids:
        if i not in state:
            dfs(i)

    # ---- layers (longest path)
    preds = {i: [] for i in ids}
    for a, b, _, _ in es:
        if (a, b) not in back:
            preds[b].append(a)
    layer = {}

    def lay(n):
        if n in layer:
            return layer[n]
        layer[n] = 0
        layer[n] = max((lay(p) + 1 for p in preds[n]), default=0)
        return layer[n]

    for i in ids:
        lay(i)

    # ---- cross/rank sizes + dummy nodes for edges that skip layers
    cross, rank, lay_of = {}, {}, {}
    for n in ids:
        w, h = size[n]
        cross[n], rank[n] = (h, w) if horizontal else (w, h)
        lay_of[n] = layer[n]
    chains, k = [], 0
    for a, b, lab, dashed in es:
        if (a, b) in back:
            continue
        path = [a]
        for L in range(layer[a] + 1, layer[b]):
            d = f"~{k}"
            k += 1
            cross[d], rank[d], lay_of[d] = 12, 0, L
            path.append(d)
        path.append(b)
        chains.append((a, b, lab, dashed, path))

    n_layers = max(lay_of.values()) + 1
    layers = [[] for _ in range(n_layers)]
    for n in lay_of:
        layers[lay_of[n]].append(n)

    up, down = {n: [] for n in lay_of}, {n: [] for n in lay_of}
    for *_, path in chains:
        for u, v in zip(path, path[1:]):
            down[u].append(v)
            up[v].append(u)

    # ---- order inside layers (barycenter sweeps)
    for _ in range(4):
        for li in range(1, n_layers):
            idx = {n: i for i, n in enumerate(layers[li - 1])}
            cur = {n: i for i, n in enumerate(layers[li])}
            layers[li].sort(key=lambda n: sum(idx[p] for p in up[n]) / len(up[n]) if up[n] else cur[n])
        for li in range(n_layers - 2, -1, -1):
            idx = {n: i for i, n in enumerate(layers[li + 1])}
            cur = {n: i for i, n in enumerate(layers[li])}
            layers[li].sort(key=lambda n: sum(idx[c] for c in down[n]) / len(down[n]) if down[n] else cur[n])

    # ---- positions across the layer
    def gap(p, n):
        return 22 if (p.startswith("~") or n.startswith("~")) else GAP

    pos = {}
    for L in layers:
        total = sum(cross[n] for n in L) + sum(gap(p, n) for p, n in zip(L, L[1:]))
        x = -total / 2.0
        for n in L:
            pos[n] = x + cross[n] / 2.0
            x += cross[n] + 0
            x += GAP if n is not L[-1] else 0

    def place(L, want):
        xs = []
        for i, n in enumerate(L):
            x = want[n]
            if i:
                p = L[i - 1]
                x = max(x, xs[-1] + (cross[p] + cross[n]) / 2.0 + gap(p, n))
            xs.append(x)
        shift = sum(want[n] - x for n, x in zip(L, xs)) / len(xs)
        for n, x in zip(L, xs):
            pos[n] = x + shift

    for _ in range(8):
        for li in range(1, n_layers):
            place(layers[li], {n: (sum(pos[p] for p in up[n]) / len(up[n]) if up[n] else pos[n]) for n in layers[li]})
        for li in range(n_layers - 2, -1, -1):
            place(layers[li], {n: (sum(pos[c] for c in down[n]) / len(down[n]) if down[n] else pos[n]) for n in layers[li]})

    # ---- positions along the flow
    lsize = [(max(rank[n] for n in L) or 10) for L in layers]
    rpos, cur_r = [], PAD
    for s in lsize:
        rpos.append(cur_r + s / 2.0)
        cur_r += s + RANK_GAP
    total_rank = cur_r - RANK_GAP + PAD

    lo = min(pos[n] - cross[n] / 2.0 for n in lay_of)
    hi = max(pos[n] + cross[n] / 2.0 for n in lay_of)
    offset = PAD - lo
    cross_total = hi - lo + 2 * PAD
    lanes = len(back)
    extra = (30 + 20 * lanes) if lanes else 0
    if horizontal:
        W, H = total_rank, cross_total + extra
    else:
        W, H = cross_total + extra, total_rank

    def xy(n):
        c, r = pos[n] + offset, rpos[lay_of[n]]
        return (r, c) if horizontal else (c, r)

    def port(n, side):
        x, y = xy(n)
        w, h = size[n]
        return (x + side * w / 2.0, y) if horizontal else (x, y + side * h / 2.0)

    def ctrl(p, q):
        if horizontal:
            kk = (q[0] - p[0]) / 2.0
            return (p[0] + kk, p[1]), (q[0] - kk, q[1])
        kk = (q[1] - p[1]) / 2.0
        return (p[0], p[1] + kk), (q[0], q[1] - kk)

    def bez(p0, p1, p2, p3, t):
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])

    EDGE = "#9FB4B0"
    edge_svg, label_svg = [], []

    def arrow(tip, frm):
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]
        ln = (dx * dx + dy * dy) ** 0.5 or 1.0
        dx, dy = dx / ln, dy / ln
        bx, by = tip[0] - dx * 11, tip[1] - dy * 11
        px, py = -dy * 5.5, dx * 5.5
        return (
            f'<polygon points="{f1(tip[0])},{f1(tip[1])} {f1(bx + px)},{f1(by + py)} {f1(bx - px)},{f1(by - py)}" fill="{EDGE}"/>'
        )

    def add_label(text, pt):
        if not text:
            return
        lw = len(text) * 7.6 + 16
        label_svg.append(
            f'<rect x="{f1(pt[0] - lw / 2)}" y="{f1(pt[1] - 11)}" width="{f1(lw)}" height="22" rx="7" fill="#14262B"/>'
            f'<text x="{f1(pt[0])}" y="{f1(pt[1] + 4.5)}" text-anchor="middle" fill="#E9F1EE" '
            f'style="font-size:12.5px;font-weight:600">{esc(text)}</text>'
        )

    for a, b, lab, dashed, path in chains:
        pts = [port(a, 1)] + [xy(d) for d in path[1:-1]] + [port(b, -1)]
        d_attr = f"M{f1(pts[0][0])},{f1(pts[0][1])}"
        last_c2 = None
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            c1, c2 = ctrl(p, q)
            d_attr += f" C{f1(c1[0])},{f1(c1[1])} {f1(c2[0])},{f1(c2[1])} {f1(q[0])},{f1(q[1])}"
            if i == 0:
                add_label(lab, bez(p, c1, c2, q, 0.5))
            last_c2 = c2
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        edge_svg.append(f'<path d="{d_attr}" fill="none" stroke="{EDGE}" stroke-width="1.8"{dash}/>')
        edge_svg.append(arrow(pts[-1], last_c2))

    base = (cross_total - PAD + 24) if lanes else 0
    lane_i = 0
    for a, b, lab, dashed in es:
        if (a, b) not in back:
            continue
        lane = base + 20 * lane_i
        lane_i += 1
        ax, ay = xy(a)
        bx_, by_ = xy(b)
        aw, ah = size[a]
        bw, bh = size[b]
        if horizontal:
            p0, p3 = (ax, ay + ah / 2.0), (bx_, by_ + bh / 2.0)
            c1, c2 = (p0[0], lane), (p3[0], lane)
        else:
            p0, p3 = (ax + aw / 2.0, ay), (bx_ + bw / 2.0, by_)
            c1, c2 = (lane, p0[1]), (lane, p3[1])
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        edge_svg.append(
            f'<path d="M{f1(p0[0])},{f1(p0[1])} C{f1(c1[0])},{f1(c1[1])} {f1(c2[0])},{f1(c2[1])} {f1(p3[0])},{f1(p3[1])}" '
            f'fill="none" stroke="{EDGE}" stroke-width="1.8"{dash}/>'
        )
        edge_svg.append(arrow(p3, c2))
        add_label(lab, bez(p0, c1, c2, p3, 0.5))

    # ---- nodes
    INK_ = "#14262B"
    node_svg = []
    for n in ids:
        x, y = xy(n)
        w, h = size[n]
        shape = nodes[n]["shape"]
        fill, stroke = "#FFF3D1", "#F2A900"
        if shape == "diamond":
            fill = "#FFE08A"
        elif shape in ("stadium", "circle"):
            fill, stroke = "#BFEFDC", "#6EE0B2"
        elif shape == "hex":
            fill, stroke = "#E3EFE9", "#9FB4B0"
        sty = f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"'
        if shape == "diamond":
            el = (f'<polygon points="{f1(x)},{f1(y - h / 2)} {f1(x + w / 2)},{f1(y)} '
                  f'{f1(x)},{f1(y + h / 2)} {f1(x - w / 2)},{f1(y)}" {sty}/>')
        elif shape == "hex":
            ins = min(24.0, w * 0.14)
            el = (f'<polygon points="{f1(x - w / 2 + ins)},{f1(y - h / 2)} {f1(x + w / 2 - ins)},{f1(y - h / 2)} '
                  f'{f1(x + w / 2)},{f1(y)} {f1(x + w / 2 - ins)},{f1(y + h / 2)} '
                  f'{f1(x - w / 2 + ins)},{f1(y + h / 2)} {f1(x - w / 2)},{f1(y)}" {sty}/>')
        elif shape == "circle":
            el = f'<ellipse cx="{f1(x)}" cy="{f1(y)}" rx="{f1(w / 2)}" ry="{f1(h / 2)}" {sty}/>'
        else:
            rx = h / 2.0 if shape == "stadium" else (18 if shape == "round" else 10)
            el = f'<rect x="{f1(x - w / 2)}" y="{f1(y - h / 2)}" width="{f1(w)}" height="{f1(h)}" rx="{f1(rx)}" {sty}/>'
        node_svg.append(el)
        lines = lines_of[n]
        ty = y - (len(lines) - 1) * LH / 2.0 + 5
        for ln in lines:
            node_svg.append(f'<text x="{f1(x)}" y="{f1(ty)}" text-anchor="middle" fill="{INK_}">{esc(ln)}</text>')
            ty += LH

    return (
        f'<svg viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" role="img" '
        f'aria-label="Roadmap flowchart">' + "".join(edge_svg) + "".join(node_svg) + "".join(label_svg) + "</svg>"
    )


# Fallback only: used when the Mermaid text can't be parsed. The frame has a fixed height and the
# chart is scaled to fit inside it, so it can never spill over the content below.
MERMAID_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
<style>
  html, body { margin: 0; height: 100%; background: transparent; overflow: hidden;
               font-family: 'IBM Plex Sans', system-ui, sans-serif; }
  .wrap { background: radial-gradient(700px 300px at 90% 0%, rgba(242,169,0,.15), transparent 65%), #14262B;
          border: 1px solid #2B4A52; border-radius: 22px; margin: 1px; padding: 20px;
          height: calc(100% - 2px); box-sizing: border-box; }
  .mermaid { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
  .mermaid svg { max-width: 100% !important; width: 100% !important; height: 100% !important; }
  .nodeLabel, .node .label { color: #14262B !important; font-weight: 500; }
  .edgeLabel, span.edgeLabel, .edgeLabel p { color: #E9F1EE !important; background-color: #14262B !important; }
  .cluster-label .nodeLabel { color: #E9F1EE !important; }
  .fallback { color: #D6E2DF; font-size: 14px; width: 100%; height: 100%; overflow: auto; }
  .fallback pre { white-space: pre-wrap; background: #1D3A41; padding: 12px; border-radius: 8px;
                  font-size: 12.5px; color: #E9F1EE; }
</style>
</head>
<body>
<div class="wrap"><pre class="mermaid" id="g">__GRAPH__</pre></div>
<script>
  var box = document.getElementById('g');
  var source = box.textContent;
  function showFallback() {
    var holder = document.createElement('div');
    holder.className = 'fallback';
    holder.textContent = "The flowchart couldn't be drawn. Here is its text version:";
    var pre = document.createElement('pre');
    pre.textContent = source;
    holder.appendChild(pre);
    box.parentNode.replaceChild(holder, box);
  }
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
        primaryColor: '#FFF3D1',
        primaryBorderColor: '#F2A900',
        primaryTextColor: '#14262B',
        lineColor: '#9FB4B0',
        textColor: '#E9F1EE',
        secondaryColor: '#E3EFE9',
        tertiaryColor: '#1D3A41',
        clusterBkg: '#1D3A41',
        clusterBorder: '#3B5961',
        edgeLabelBackground: '#14262B'
      },
      flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' }
    });
    mermaid.run({ nodes: [box] }).catch(showFallback);
  } catch (err) { showFallback(); }
</script>
</body>
</html>"""


def _chart_height(code: str) -> int:
    """Fixed frame height for the fallback; the chart is scaled to fit it."""
    if re.search(r"(graph|flowchart)\s+(LR|RL)", code, re.I):
        return 460
    edges = len(re.findall(r"-->|==>|-\.->|---", code))
    return int(min(1500, max(520, 170 + 95 * edges)))


def render_mermaid(code: str):
    """Draw the flowchart on a dark panel as part of the page (no iframe, no scroll box)."""
    clean = code.strip()
    if "```mermaid" in clean:
        clean = clean.split("```mermaid")[1].split("```")[0].strip()
    elif "```" in clean:
        clean = clean.replace("```", "").strip()

    svg = None
    try:
        parsed = _parse_flowchart(clean)
        if parsed:
            svg = _flowchart_svg(*parsed)
    except Exception:
        svg = None

    if svg:
        md(f'<div class="flowpanel">{svg}</div>')
        return

    html_code = MERMAID_TEMPLATE.replace("__GRAPH__", escape(clean, quote=False))
    components.html(html_code, height=_chart_height(clean), scrolling=False)


# =========================================================
# SCREEN 1: HOME
# =========================================================

if st.session_state.page == "home":

    top_bar()

    md(
        f"""<div class="hero">
<div>
<div class="hero-title">Learn why startups like yours failed, before you build yours.</div>
<p class="hero-sub">Describe your idea in a few sentences. We compare it with 250+ failed startups and 300+ Indian ones, then give you a survival score, the risks behind it, and a plan to work around them.</p>
<svg class="pulse" viewBox="0 0 1000 64" preserveAspectRatio="none" aria-hidden="true">
<path pathLength="1" d="M0 36 H230 L250 36 L266 8 L288 58 L304 22 L318 36 H600 L618 36 L634 12 L654 54 L668 26 L680 36 H1000"/>
</svg>
</div>
{hero_art_svg()}
</div>"""
    )

    st.write("")
    c1, _ = st.columns([1.1, 3])
    with c1:
        if st.button("Check my idea", use_container_width=True, type="primary"):
            st.session_state.page = "input"
            st.rerun()

    md(
        f"""<div class="section">
<div class="h2">What you get</div>
<p class="lede">One short report that tells you where your idea is strong, where it is likely to break, and what to do next.</p>
<div class="trio">
<div>
{icon("doc")}
<div class="t3">A sharper pitch</div>
<p>Your idea is rewritten as a clear value proposition, with the problems it solves and the users you may be overlooking.</p>
</div>
<div>
{icon("search")}
<div class="t3">The failures closest to yours</div>
<p>We match your idea against 250+ failed tech startups to surface the operating, money and competition risks they ran into.</p>
</div>
<div>
{icon("gauge")}
<div class="t3">A survival score</div>
<p>A Random Forest model scores 25 signals about your idea against past outcomes and returns a probability of success.</p>
</div>
</div>
</div>"""
    )

    md(
        """<div class="band">
<div class="h2">How it works</div>
<div class="flow">
<div><div class="n">1</div><div class="ft">Describe your idea</div><p>No financials or pitch deck needed.</p></div>
<div><div class="n">2</div><div class="ft">We find precedents</div><p>Past failures and Indian competitors that look like you.</p></div>
<div><div class="n">3</div><div class="ft">Get your score</div><p>Survival odds, plus the threats behind the number.</p></div>
<div><div class="n">4</div><div class="ft">Build the plan</div><p>Roadmap, skills, team, logo concepts and a PDF you can share.</p></div>
</div>
</div>"""
    )

    st.write("")
    st.write("")
    c1, _ = st.columns([1.1, 3])
    with c1:
        if st.button("Start with your idea", use_container_width=True, type="primary", key="home_cta_2"):
            st.session_state.page = "input"
            st.rerun()


# =========================================================
# SCREEN 2: PITCH INPUT
# =========================================================

elif st.session_state.page == "input":

    top_bar(active=0)

    md(
        """<div class="page-title">Describe your idea</div>
<p class="page-sub">A few sentences is enough. The more specific you are about who it is for and how it earns, the sharper the analysis.</p>"""
    )

    form_col, tips_col = st.columns([1.8, 1], gap="large")

    with form_col:
        startup_name = st.text_input(
            "Idea name (optional)",
            value=st.session_state.startup_name,
            placeholder="e.g. QuickTutor, NovaPay, AgriLog",
        )

        startup_description = st.text_area(
            "What are you building?",
            value=st.session_state.startup_description,
            placeholder="Who is it for, what problem does it solve, and how will it make money?",
            height=250,
        )

        st.write("")
        if st.button("Run the analysis", type="primary", use_container_width=True):
            if len(startup_description.strip()) < 30:
                st.warning("Add a little more detail, at least 30 characters, so there is enough to analyse.")
            else:
                st.session_state.startup_name = startup_name.strip()
                st.session_state.startup_description = startup_description.strip()
                # Clear previous outputs
                st.session_state.failure_results = []
                st.session_state.indian_startups = []
                st.session_state.prediction_result = {}
                st.session_state.concept_data = {}
                st.session_state.plan_data = {}
                st.session_state.page = "overview"
                st.rerun()

        if st.button("Back", type="secondary"):
            st.session_state.page = "home"
            st.rerun()

    with tips_col:
        md(
            f"""<div class="tips-dark">
{tips_art_svg()}
<div class="tt">Cover these four things</div>
<ul>
<li>The problem, and who has it</li>
<li>What you will build</li>
<li>How it makes money</li>
<li>How you will reach your first customers</li>
</ul>
<div class="foot">Two or three sentences each is plenty.</div>
</div>"""
        )


# =========================================================
# SCREEN 3: VERDICT + RISKS
# =========================================================

elif st.session_state.page == "overview":

    top_bar(active=1)

    desc = st.session_state.startup_description
    name = st.session_state.startup_name or "Your idea"

    if not st.session_state.concept_data or not st.session_state.prediction_result:
        with st.spinner("Matching your idea against past startups and scoring it..."):
            try:
                (
                    st.session_state.failure_results,
                    st.session_state.indian_startups,
                    st.session_state.prediction_result,
                    st.session_state.concept_data,
                ) = run_initial_analysis(desc)
            except Exception as e:
                st.error(f"The analysis stopped: {e}")
                st.stop()

    concept = st.session_state.concept_data
    pred = st.session_state.prediction_result

    succ_val = max(0.0, min(100.0, num(pred.get("success_probability", 0))))
    fail_val = max(0.0, min(100.0, num(pred.get("failure_probability", 0))))
    status_label = str(pred.get("status", "Unknown"))
    status_up = status_label.upper()

    if "SUCCESS" in status_up:
        is_success = True
    elif "FAIL" in status_up:
        is_success = False
    else:
        is_success = succ_val >= 50

    tone = "ok" if is_success else "risky"
    arc_color = "#6EE0B2" if is_success else "#FF8F7E"

    brand_name = session_brand_name()
    logo_seed = st.session_state.logo_seed

    md(
        cover_html(
            name,
            "Here is how your idea reads against past startups, and the risks that drive the score.",
            brand_name,
            logo_seed,
        )
    )

    md(
        f"""<div class="overview-grid">
<div class="verdict">
<svg class="dial" viewBox="0 0 220 140" role="img" aria-label="{pct_str(succ_val)} percent chance of success">
<path class="track" pathLength="100" d="M 20 120 A 90 90 0 0 1 200 120" fill="none" stroke-width="14" stroke-linecap="round"/>
<path class="val" pathLength="100" d="M 20 120 A 90 90 0 0 1 200 120" fill="none" stroke="{arc_color}" stroke-width="14" stroke-linecap="round" stroke-dasharray="{succ_val:.2f} 100"/>
<text class="pct" x="110" y="104" text-anchor="middle">{pct_str(succ_val)}%</text>
<text class="cap" x="110" y="126" text-anchor="middle">chance of success</text>
</svg>
<div class="verdict-status {tone}">{esc(status_label)}</div>
<div class="verdict-split">
<div><b>{pct_str(succ_val)}%</b><span>Success</span></div>
<div><b>{pct_str(fail_val)}%</b><span>Failure risk</span></div>
</div>
</div>
<div class="doc">
<div class="lab">Your pitch</div>
<p class="orig">{rich(desc)}</p>
<div class="lab">Sharper version</div>
<p class="sharp">{rich(concept.get("enhanced_description", ""))}</p>
</div>
</div>"""
    )

    # Generated logo concepts
    base_style = (_hash(f"{brand_name.lower()}|{logo_seed}") // 7) % 4
    themes = ["", "dark", "gold"]
    kit_cards = ""
    for i in range(3):
        kit_cards += (
            f'<div class="bk {themes[i]}">'
            f'{logo_svg(brand_name, logo_seed + i, style=(base_style + i) % 4, size=96)}'
            f'<div class="wm">{esc(brand_name)}</div>'
            f'<div class="tag">Concept {"ABC"[i]}</div></div>'
        )
    md(
        f"""<div class="section" style="margin-top:56px">
<div class="h2 h2i">{icon("bulb")}Logo concepts</div>
<p class="lede">Generated from your idea name. Shuffle to see new options.</p>
<div class="brandkit">{kit_cards}</div>
</div>"""
    )

    st.write("")
    sh1, _ = st.columns([1.3, 3])
    with sh1:
        if st.button("Shuffle logo concepts", use_container_width=True, type="secondary"):
            st.session_state.logo_seed += 1
            st.rerun()

    md(
        f"""<div class="cols2">
<div>
<div class="h2">Problems it solves</div>
{plain_list(concept.get("problems_identified", []))}
</div>
<div>
<div class="h2">Who it is for</div>
{plain_list(concept.get("target_users", []))}
</div>
</div>"""
    )

    st.caption(
        "The score comes from a Random Forest model that reads 25 signals inferred from your idea "
        "and compares them with patterns in past tech startups. Treat it as a guide, not a guarantee."
    )

    # Major risks
    risk_blocks = "".join(
        f'<div class="risk"><div class="rt">{esc(r.get("title", "Risk"))}</div><p>{rich(r.get("explanation", ""))}</p></div>'
        for r in concept.get("major_risks", [])
    )
    md(
        f"""<div class="section">
<div class="h2">Biggest risks</div>
<p class="lede" style="margin-bottom:26px">Drawn from 250+ failure cases and the Indian startup landscape.</p>
{risk_blocks}
</div>"""
    )

    # Decision gate
    md(
        """<div class="gate">
<div class="gt">Want a plan to get around these risks?</div>
<p class="lede" style="margin-bottom:22px">We'll build a phased roadmap, the skills and team you need, and upgrades to your concept that target each risk above.</p>
</div>"""
    )

    b1, b2, _ = st.columns([1.2, 1.2, 2])
    with b1:
        if st.button("Build my plan", use_container_width=True, type="primary"):
            st.session_state.page = "detailed_plan"
            st.rerun()
    with b2:
        if st.button("Start over", use_container_width=True, type="secondary"):
            reset_and_go_to_input()
            st.rerun()


# =========================================================
# SCREEN 4: PLAYBOOK
# =========================================================

elif st.session_state.page == "detailed_plan":

    top_bar(active=2)

    name = st.session_state.startup_name or "Your idea"

    if not st.session_state.plan_data:
        with st.spinner("Building your roadmap, skills list and team plan..."):
            try:
                st.session_state.plan_data = build_detailed_plan(
                    st.session_state.startup_description,
                    st.session_state.prediction_result,
                    st.session_state.failure_results,
                    st.session_state.indian_startups,
                )
            except Exception as e:
                st.error(f"The plan couldn't be built: {e}")
                st.stop()

    plan = st.session_state.plan_data

    md(
        cover_html(
            f"Your plan for {name}",
            "What to change in the concept, the order to build and test it in, and who you need on the team.",
            session_brand_name(),
            st.session_state.logo_seed,
        )
    )

    # Concept improvements
    imp_list = plan.get("improvements", [])
    if imp_list:
        rows = "".join(
            f"""<div class="imp-row">
<div class="now" data-l="Your idea now">{rich(i.get("current", ""))}</div>
<div class="up" data-l="Upgrade">{rich(i.get("suggested", ""))}</div>
<div class="why" data-l="Why it helps">{rich(i.get("rationale", ""))}</div>
</div>"""
            for i in imp_list
        )
        md(
            f"""<div>
<div class="h2 h2i">{icon("bulb")}Upgrades to the concept</div>
<p class="lede">Each change targets a failure pattern found in your analysis.</p>
<div class="imp-head"><div>Your idea now</div><div>Upgrade</div><div>Why it helps</div></div>
{rows}
</div>"""
        )

    # Roadmap
    md(
        f"""<div class="section">
<div class="h2 h2i">{icon("map")}Roadmap</div>
<p class="lede" style="margin-bottom:18px">The path from first test to a validated product.</p>
</div>"""
    )

    if plan.get("flowchart"):
        render_mermaid(plan.get("flowchart"))

    stages = plan.get("roadmap_stages", [])
    if stages:
        items = "".join(
            f'<li><div class="ph">{esc(s.get("phase", ""))}</div><p>{rich(s.get("details", ""))}</p></li>'
            for s in stages
        )
        md(f'<ol class="tl">{items}</ol>')

    # Skills and team
    skills_rows = "".join(
        f'<li class="member"><div class="av">{icon("skill")}</div><div>'
        f'<b>{esc(s.get("skill", ""))}</b><div class="sub">{rich(s.get("purpose", ""))}</div></div></li>'
        for s in plan.get("required_skills", [])
    )
    team_rows = "".join(
        f'<li class="member"><div class="av">{avatar_svg(t.get("role", "Role"))}</div><div>'
        f'<b>{esc(t.get("role", ""))}</b><span class="pill">×{esc(t.get("count", 1))}</span>'
        f'<div class="sub">{rich(t.get("description", ""))}</div></div></li>'
        for t in plan.get("recommended_team", [])
    )
    md(
        f"""<div class="cols2" style="margin-top:64px">
<div>
<div class="h2">Skills you need</div>
<ul class="plain">{skills_rows}</ul>
</div>
<div>
<div class="h2">Who to bring in</div>
<ul class="plain">{team_rows}</ul>
</div>
</div>"""
    )

    # PDF export
    md(
        """<div class="gate">
<div class="gt">Take it with you</div>
<p class="lede" style="margin-bottom:22px">Download the full report as a PDF: the analysis, your score, and this plan, ready to share with co-founders or advisors.</p>
</div>"""
    )

    pdf_buffer = generate_pdf_report(
        startup_name=st.session_state.startup_name,
        original_desc=st.session_state.startup_description,
        concept_data=st.session_state.concept_data,
        prediction_result=st.session_state.prediction_result,
        plan_data=st.session_state.plan_data,
        logo_seed=st.session_state.logo_seed,
    )

    d1, _ = st.columns([1.6, 2])
    with d1:
        st.download_button(
            label="Download PDF report",
            data=pdf_buffer,
            file_name=f"AI_Startup_Validator_Report_{st.session_state.startup_name or 'Idea'}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    st.write("")
    n1, n2, _ = st.columns([1.2, 1.4, 2])
    with n1:
        if st.button("Back to verdict", use_container_width=True, type="secondary"):
            st.session_state.page = "overview"
            st.rerun()
    with n2:
        if st.button("Check another idea", use_container_width=True, type="secondary"):
            reset_and_go_to_input()
            st.rerun()
