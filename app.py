import streamlit as st
import pdfplumber
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
import time
from groq import Groq
from datetime import datetime

# ─── PAGE CONFIG ───────────────────────────────────────
st.set_page_config(
    page_title="FactChecker AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── LOAD API KEYS ─────────────────────────────────────
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── SESSION STATE ─────────────────────────────────────
for key, default in [
    ("history", []),
    ("results", None),
    ("page", "Home"),
    ("uploaded_file", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {
    /* Core palette — dark SaaS */
    --bg:          #090d14;
    --bg2:         #0d1420;
    --surface:     #111827;
    --surface2:    #1a2235;
    --border:      #1e2d45;
    --border-mid:  #243450;
    --border-hi:   #2e4268;

    /* Text */
    --text:        #f0f4ff;
    --text-2:      #8a9bbf;
    --text-3:      #4d5f80;

    /* Blue accent */
    --blue:        #2563eb;
    --blue-mid:    #1d4ed8;
    --blue-glow:   rgba(37,99,235,0.18);
    --blue-light:  rgba(37,99,235,0.10);
    --blue-border: rgba(37,99,235,0.35);

    /* Status */
    --green:       #22c55e;
    --green-bg:    rgba(34,197,94,0.08);
    --green-brd:   rgba(34,197,94,0.25);
    --amber:       #f59e0b;
    --amber-bg:    rgba(245,158,11,0.08);
    --amber-brd:   rgba(245,158,11,0.25);
    --red:         #ef4444;
    --red-bg:      rgba(239,68,68,0.08);
    --red-brd:     rgba(239,68,68,0.25);
    --slate-text:  #6b7fa3;
    --slate-bg:    rgba(107,127,163,0.08);
    --slate-brd:   rgba(107,127,163,0.25);

    --radius:      14px;
    --radius-sm:   9px;
    --radius-lg:   20px;
    --shadow:      0 4px 24px rgba(0,0,0,0.4);
    --shadow-sm:   0 2px 10px rgba(0,0,0,0.3);
    --shadow-glow: 0 0 30px rgba(37,99,235,0.15);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
    font-size: 15px;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.block-container {
    padding: 2rem 2.5rem 5rem 2.5rem !important;
    max-width: 1100px !important;
}

/* ══ SIDEBAR ══════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1.5rem 1rem !important;
}

.sidebar-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 0.25rem 0.25rem 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.brand-icon {
    width: 36px; height: 36px; border-radius: 9px;
    background: var(--blue); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
    box-shadow: 0 0 16px var(--blue-glow);
}
.brand-name {
    font-family: 'Syne', sans-serif;
    font-size: 1rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.01em;
}
.brand-sub { font-size: 0.68rem; color: var(--text-3); margin-top: 2px; }

.sidebar-label {
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-3);
    padding: 0 0.25rem; margin: 0 0 0.6rem;
}

/* ══ BUTTONS ══════════════════════════════════════════ */
.stButton > button {
    background: var(--surface2) !important;
    color: var(--text-2) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border: 1px solid var(--border-mid) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.6rem 1.25rem !important;
    font-size: 0.85rem !important;
    width: 100% !important;
    transition: all 0.18s ease !important;
    box-shadow: var(--shadow-sm) !important;
    letter-spacing: -0.01em !important;
    text-align: left !important;
}
.stButton > button:hover {
    background: var(--blue-light) !important;
    border-color: var(--blue-border) !important;
    color: var(--text) !important;
    box-shadow: var(--shadow-glow) !important;
}
.stButton > button:active {
    transform: translateY(1px) !important;
}

/* ══ PAGE HEADER ══════════════════════════════════════ */
.page-header { margin-bottom: 2rem; }
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.1rem; font-weight: 700;
    color: var(--text); margin-bottom: 0.4rem;
    letter-spacing: -0.03em; line-height: 1.15;
}
.page-subtitle { color: var(--text-2); font-size: 0.9rem; line-height: 1.65; }

/* ══ HERO ══════════════════════════════════════════════ */
.hero {
    background: linear-gradient(135deg, var(--surface) 0%, var(--bg2) 100%);
    border: 1px solid var(--border-mid);
    border-radius: var(--radius-lg);
    padding: 4rem 3.5rem 3.5rem;
    margin-bottom: 2rem;
    position: relative; overflow: hidden;
    box-shadow: var(--shadow), var(--shadow-glow);
}
.hero::before {
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 320px; height: 320px; border-radius: 50%;
    background: radial-gradient(circle, rgba(37,99,235,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute; bottom: -80px; left: 30%;
    width: 200px; height: 200px; border-radius: 50%;
    background: radial-gradient(circle, rgba(37,99,235,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero-tag {
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--blue);
    background: var(--blue-light);
    border: 1px solid var(--blue-border);
    padding: 0.35em 1em; border-radius: 100px;
    margin-bottom: 1.5rem;
}
.hero-dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--blue);
    animation: pulse 2s ease infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.75); }
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.6rem; font-weight: 800;
    line-height: 1.05; letter-spacing: -0.04em;
    color: var(--text); margin-bottom: 1.25rem;
}
.hero-title .accent { color: var(--blue); }
.hero-sub {
    font-size: 1.05rem; color: var(--text-2); line-height: 1.75;
    max-width: 520px; margin-bottom: 2.25rem; font-weight: 300;
}
.hero-cta-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.cta-primary {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--blue); color: #fff !important;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600; font-size: 0.9rem;
    padding: 0.75rem 1.75rem; border-radius: var(--radius-sm);
    text-decoration: none; border: none; cursor: pointer;
    box-shadow: 0 4px 20px var(--blue-glow);
    transition: all 0.18s ease;
    letter-spacing: -0.01em;
}
.cta-primary:hover {
    background: var(--blue-mid);
    box-shadow: 0 6px 28px rgba(37,99,235,0.4);
    transform: translateY(-1px);
}
.cta-secondary {
    display: inline-flex; align-items: center; gap: 8px;
    background: transparent; color: var(--text-2) !important;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500; font-size: 0.88rem;
    padding: 0.75rem 1.5rem; border-radius: var(--radius-sm);
    text-decoration: none; border: 1px solid var(--border-mid); cursor: pointer;
    transition: all 0.18s ease;
}
.cta-secondary:hover { border-color: var(--blue-border); color: var(--text) !important; background: var(--blue-light); }

/* ══ SECTION HEADING ══════════════════════════════════ */
.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--text); letter-spacing: -0.025em;
    margin-bottom: 0.4rem;
}
.section-sub {
    font-size: 0.875rem; color: var(--text-2); margin-bottom: 1.5rem; line-height: 1.6;
}

/* ══ FEATURE CARDS ════════════════════════════════════ */
.features-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 2.5rem;
}
.feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.5rem;
    transition: all 0.2s ease;
    position: relative; overflow: hidden;
}
.feature-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--blue-border), transparent);
    opacity: 0; transition: opacity 0.2s;
}
.feature-card:hover { border-color: var(--border-hi); box-shadow: var(--shadow), var(--shadow-glow); transform: translateY(-2px); }
.feature-card:hover::before { opacity: 1; }
.feature-ico {
    width: 42px; height: 42px; border-radius: 10px; flex-shrink: 0;
    background: var(--blue-light); border: 1px solid var(--blue-border);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; margin-bottom: 1rem;
}
.feature-title { font-family: 'Syne', sans-serif; font-weight: 600; color: var(--text); font-size: 0.95rem; margin-bottom: 0.4rem; letter-spacing: -0.01em; }
.feature-desc { font-size: 0.8rem; color: var(--text-2); line-height: 1.7; font-weight: 300; }

/* ══ HOW IT WORKS ════════════════════════════════════ */
.steps-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 2.5rem;
}
.step-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.4rem 1.2rem;
    position: relative; transition: all 0.2s ease;
}
.step-card:hover { border-color: var(--border-hi); transform: translateY(-2px); box-shadow: var(--shadow); }
.step-num {
    font-family: 'Syne', sans-serif;
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.12em;
    color: var(--blue); text-transform: uppercase; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 6px;
}
.step-num-badge {
    width: 22px; height: 22px; border-radius: 50%;
    background: var(--blue-light); border: 1px solid var(--blue-border);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700; color: var(--blue);
}
.step-ico { font-size: 1.5rem; margin-bottom: 0.6rem; display: block; }
.step-title { font-family: 'Syne', sans-serif; font-weight: 600; color: var(--text); font-size: 0.9rem; margin-bottom: 0.35rem; }
.step-desc { font-size: 0.77rem; color: var(--text-2); line-height: 1.65; font-weight: 300; }

/* ══ ABOUT SECTION ════════════════════════════════════ */
.about-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 2.5rem;
    margin-bottom: 2.5rem;
    position: relative; overflow: hidden;
}
.about-card::before {
    content: ''; position: absolute; top: 0; right: 0;
    width: 250px; height: 250px; border-radius: 50%;
    background: radial-gradient(circle, rgba(37,99,235,0.07) 0%, transparent 70%);
}
.tech-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1rem; }
.tech-chip {
    background: var(--bg2); border: 1px solid var(--border-mid);
    color: var(--text-2); border-radius: 100px; padding: 0.3em 0.9em;
    font-size: 0.74rem; font-weight: 500;
}

/* ══ FOOTER ══════════════════════════════════════════ */
.footer {
    border-top: 1px solid var(--border); padding: 2rem 0 0.5rem;
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 1rem; margin-top: 3rem;
}
.footer-brand { font-family: 'Syne', sans-serif; font-weight: 700; color: var(--text); font-size: 0.9rem; }
.footer-links { display: flex; gap: 1.5rem; align-items: center; }
.footer-link {
    font-size: 0.78rem; color: var(--text-3); text-decoration: none;
    transition: color 0.15s;
}
.footer-link:hover { color: var(--blue); }
.footer-badge {
    font-size: 0.72rem; color: var(--text-3);
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 100px; padding: 0.25em 0.85em;
}

/* ══ UPLOAD ZONE ═════════════════════════════════════ */
.upload-zone {
    border: 2px dashed var(--border-hi);
    border-radius: var(--radius-lg); padding: 4rem 2rem;
    text-align: center;
    background: var(--surface);
    transition: all 0.18s; margin-bottom: 1.5rem;
}
.upload-zone:hover { border-color: var(--blue); background: var(--blue-light); }
.upload-icon { font-size: 2.75rem; margin-bottom: 1rem; display: block; }
.upload-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.2rem; font-weight: 700; color: var(--text);
    margin-bottom: 0.5rem;
}
.upload-sub { font-size: 0.82rem; color: var(--text-2); font-weight: 300; }

/* ══ METRICS ═════════════════════════════════════════ */
.metrics-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.5rem;
}
.metric-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.4rem;
    box-shadow: var(--shadow-sm);
}
.metric-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem; font-weight: 700; line-height: 1; letter-spacing: -0.04em;
    margin-bottom: 0.3rem;
}
.metric-label { font-size: 0.74rem; color: var(--text-2); font-weight: 400; }
.m-total .metric-num { color: var(--text); }
.m-verified .metric-num { color: var(--green); }
.m-inaccurate .metric-num { color: var(--amber); }
.m-false .metric-num { color: var(--red); }

/* ══ TRUST CARD ══════════════════════════════════════ */
.trust-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.5rem;
    text-align: center; height: 100%;
    display: flex; flex-direction: column; justify-content: center; gap: 0.4rem;
    box-shadow: var(--shadow-sm);
}
.trust-label { font-size: 0.62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-3); }
.trust-num {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem; font-weight: 800; line-height: 1; letter-spacing: -0.05em;
}
.trust-sub { font-size: 0.74rem; color: var(--text-3); }

/* ══ RISK BADGE ══════════════════════════════════════ */
.risk-tag {
    display: inline-block; padding: 0.28em 0.9em; border-radius: 100px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.04em;
}
.risk-low  { background: var(--green-bg);  color: var(--green);  border: 1px solid var(--green-brd); }
.risk-med  { background: var(--amber-bg);  color: var(--amber);  border: 1px solid var(--amber-brd); }
.risk-high { background: var(--red-bg);    color: var(--red);    border: 1px solid var(--red-brd); }

/* ══ AI SUMMARY ══════════════════════════════════════ */
.ai-summary {
    background: var(--blue-light);
    border: 1px solid var(--blue-border);
    border-left: 3px solid var(--blue);
    border-radius: var(--radius); padding: 1.2rem 1.5rem;
    margin-bottom: 1.75rem;
}
.ai-label { font-size: 0.63rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: var(--blue); margin-bottom: 0.45rem; }
.ai-text { font-size: 0.9rem; color: var(--text-2); line-height: 1.8; font-weight: 300; }

/* ══ CLAIM CARDS ══════════════════════════════════════ */
.claim-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.3rem 1.5rem;
    margin-bottom: 0.75rem; border-left: 3px solid var(--border-mid);
    box-shadow: var(--shadow-sm); transition: all 0.18s;
}
.claim-card:hover { box-shadow: var(--shadow); border-color: var(--border-hi); }
.claim-card.verified   { border-left-color: var(--green); }
.claim-card.inaccurate { border-left-color: var(--amber); }
.claim-card.false      { border-left-color: var(--red); }
.claim-card.noevidence { border-left-color: var(--border-mid); }

.claim-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 1rem; margin-bottom: 0.5rem; flex-wrap: wrap;
}
.claim-text { font-size: 0.92rem; font-weight: 500; color: var(--text); line-height: 1.55; flex: 1; min-width: 200px; }
.claim-exp  { font-size: 0.83rem; color: var(--text-2); line-height: 1.7; font-weight: 300; }

.before-after {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 0.85rem;
}
.before-box { background: var(--red-bg);   border: 1px solid var(--red-brd);   border-radius: var(--radius-sm); padding: 0.85rem; }
.after-box  { background: var(--green-bg); border: 1px solid var(--green-brd); border-radius: var(--radius-sm); padding: 0.85rem; }
.ba-label   { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 600; margin-bottom: 0.35rem; }
.before-box .ba-label { color: var(--red); }
.after-box  .ba-label { color: var(--green); }
.ba-text    { font-size: 0.82rem; color: var(--text-2); line-height: 1.6; font-weight: 300; }

.ai-reasoning {
    background: var(--blue-light); border: 1px solid var(--blue-border);
    border-radius: var(--radius-sm); padding: 0.8rem 1rem; margin-top: 0.65rem;
}
.reasoning-label { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 600; color: var(--blue); margin-bottom: 0.2rem; }
.reasoning-text  { font-size: 0.81rem; color: var(--text-2); line-height: 1.7; font-weight: 300; }

.sources-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.65rem; }
.source-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: var(--surface2); border: 1px solid var(--border-mid);
    border-radius: var(--radius-sm); padding: 0.24rem 0.7rem;
    font-size: 0.74rem; color: var(--blue); text-decoration: none;
    transition: all 0.12s;
}
.source-chip:hover { background: var(--blue-light); border-color: var(--blue-border); }

/* ══ BADGES ══════════════════════════════════════════ */
.badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em;
    text-transform: uppercase; padding: 0.28em 0.85em; border-radius: 100px; white-space: nowrap;
    border: 1px solid;
}
.badge-verified   { background: var(--green-bg);  color: var(--green);  border-color: var(--green-brd); }
.badge-inaccurate { background: var(--amber-bg);  color: var(--amber);  border-color: var(--amber-brd); }
.badge-false      { background: var(--red-bg);    color: var(--red);    border-color: var(--red-brd); }
.badge-noevidence { background: var(--slate-bg);  color: var(--slate-text); border-color: var(--slate-brd); }

/* ══ CONFIDENCE BAR ══════════════════════════════════ */
.conf-wrap { margin-top: 0.6rem; display: flex; align-items: center; gap: 0.75rem; }
.conf-track { flex: 1; background: var(--bg2); border-radius: 100px; height: 5px; }
.conf-fill  { height: 5px; border-radius: 100px; transition: width 0.5s ease; }
.conf-high { background: var(--green); }
.conf-med  { background: var(--amber); }
.conf-low  { background: var(--red); }
.conf-label { font-size: 0.7rem; color: var(--text-3); white-space: nowrap; min-width: 72px; }
.conf-pct   { font-size: 0.74rem; font-weight: 600; min-width: 34px; }

/* ══ SUSPICIOUS ══════════════════════════════════════ */
.suspicious-wrap {
    background: rgba(245,158,11,0.06); border: 1px solid var(--amber-brd);
    border-radius: var(--radius); padding: 1.1rem 1.35rem; margin-bottom: 1.5rem;
}
.suspicious-header { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--amber); margin-bottom: 0.5rem; }
.suspicious-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.suspicious-chip {
    background: var(--amber-bg); border: 1px solid var(--amber-brd);
    color: var(--amber); border-radius: var(--radius-sm); padding: 0.22rem 0.7rem;
    font-size: 0.72rem; font-weight: 500;
}

/* ══ STEPPER ══════════════════════════════════════════ */
.stepper {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.5rem; margin: 1rem 0;
    box-shadow: var(--shadow-sm);
}
.s-step {
    display: flex; align-items: center; gap: 1rem;
    padding: 0.65rem 0; border-bottom: 1px solid var(--border);
}
.s-step:last-child { border-bottom: none; padding-bottom: 0; }
.s-indicator {
    width: 33px; height: 33px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; flex-shrink: 0;
}
.s-indicator.done    { background: var(--green-bg);  color: var(--green);  border: 1px solid var(--green-brd); }
.s-indicator.active  { background: var(--blue-light); color: var(--blue);  border: 1px solid var(--blue-border); }
.s-indicator.pending { background: var(--surface2);   color: var(--text-3); border: 1px solid var(--border); }
.s-title { font-weight: 500; font-size: 0.88rem; color: var(--text); }
.s-sub   { font-size: 0.73rem; color: var(--text-3); margin-top: 1px; font-weight: 300; }

/* ══ CHARTS ══════════════════════════════════════════ */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 1.5rem 0; }
.chart-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.4rem; box-shadow: var(--shadow-sm);
}
.chart-title {
    font-family: 'Syne', sans-serif;
    font-weight: 600; color: var(--text); font-size: 0.95rem; margin-bottom: 1.1rem;
}
.donut-svg { width: 100%; max-width: 140px; display: block; margin: 0 auto 0.85rem; }
.legend-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.76rem; color: var(--text-2); margin-bottom: 0.35rem; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.6rem; }
.bar-label { font-size: 0.73rem; color: var(--text-2); min-width: 95px; }
.bar-track { flex: 1; background: var(--bg2); border-radius: 100px; height: 7px; }
.bar-fill  { height: 7px; border-radius: 100px; transition: width 0.5s ease; }
.bar-pct   { font-size: 0.73rem; font-weight: 600; color: var(--text); min-width: 30px; text-align: right; }

/* ══ HISTORY ══════════════════════════════════════════ */
.history-row {
    display: grid; grid-template-columns: 2fr 0.6fr 0.6fr 0.6fr 0.6fr 1fr;
    gap: 1rem; padding: 0.9rem 1.35rem;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); margin-bottom: 8px;
    align-items: center; transition: all 0.18s;
    box-shadow: var(--shadow-sm);
}
.history-row:hover { box-shadow: var(--shadow); border-color: var(--border-hi); }

/* ══ FILE CARD ════════════════════════════════════════ */
.file-card {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.2rem 1.5rem;
    margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;
    box-shadow: var(--shadow-sm);
}

/* ══ DIVIDER ══════════════════════════════════════════ */
.soft-divider { height: 1px; background: var(--border); margin: 2.25rem 0; }

/* ══ NATIVE WIDGETS ══════════════════════════════════ */
.stProgress > div > div {
    background: var(--blue) !important;
    border-radius: 100px !important;
}
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 2px dashed var(--border-hi) !important;
    border-radius: var(--radius) !important;
}
div[data-testid="stRadio"] { display: none !important; }
hr { border-color: var(--border) !important; margin: 2rem 0 !important; }

[data-testid="stDownloadButton"] > button {
    background: var(--green-bg) !important;
    color: var(--green) !important;
    border: 1px solid var(--green-brd) !important;
    box-shadow: none !important;
}
.stSuccess {
    background: var(--green-bg) !important;
    border-color: var(--green-brd) !important;
    color: var(--green) !important;
    border-radius: var(--radius-sm) !important;
}
.stWarning {
    background: var(--amber-bg) !important;
    border-color: var(--amber-brd) !important;
    color: var(--amber) !important;
    border-radius: var(--radius-sm) !important;
}
.stInfo {
    background: var(--blue-light) !important;
    border-color: var(--blue-border) !important;
    color: var(--text-2) !important;
    border-radius: var(--radius-sm) !important;
}

/* ══ RESPONSIVE ═══════════════════════════════════════ */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 2rem !important; }
    .hero { padding: 2.5rem 1.5rem; }
    .hero-title { font-size: 2.2rem !important; }
    .steps-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .features-grid { grid-template-columns: 1fr !important; }
    .metrics-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .before-after { grid-template-columns: 1fr !important; }
    .charts-grid { grid-template-columns: 1fr !important; }
    .hero-cta-row { flex-direction: column; }
    .footer { flex-direction: column; gap: 0.75rem; }
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-icon">🛡️</div>
        <div>
            <div class="brand-name">FactChecker AI</div>
            <div class="brand-sub">Truth layer for your content</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Navigation</div>', unsafe_allow_html=True)
    for icon, label in [("🏠","Home"),("📤","Upload PDF"),("✅","Fact Check"),("📊","Dashboard"),("🕐","History")]:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:1rem;font-size:0.74rem;color:var(--text-3);line-height:1.9;">
        <div style="color:var(--blue);font-weight:600;margin-bottom:0.4rem;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;">Pipeline</div>
        PDF → Extract Claims<br>→ Web Search<br>→ AI Verification<br>→ Trust Report
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.results:
        r = st.session_state.results
        trust = r.get("trust_score", 70)
        color  = "#22c55e" if trust >= 70 else "#f59e0b" if trust >= 45 else "#ef4444"
        bg     = "rgba(34,197,94,0.08)"  if trust >= 70 else "rgba(245,158,11,0.08)"  if trust >= 45 else "rgba(239,68,68,0.08)"
        border = "rgba(34,197,94,0.25)"  if trust >= 70 else "rgba(245,158,11,0.25)"  if trust >= 45 else "rgba(239,68,68,0.25)"
        risk   = "Low Risk" if trust >= 70 else "Medium Risk" if trust >= 45 else "High Risk"
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:12px;padding:1.1rem;margin-top:0.75rem;text-align:center;">
            <div style="font-size:0.6rem;color:var(--text-3);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;font-weight:600;">Trust Score</div>
            <div style="font-family:'Syne',sans-serif;font-size:2.1rem;font-weight:800;color:{color};letter-spacing:-0.04em;">{trust}<span style="font-size:0.85rem;opacity:0.5">/100</span></div>
            <div style="font-size:0.72rem;color:var(--text-3);margin-top:3px;">{risk}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── HELPERS ───────────────────────────────────────────
SUSPICIOUS_PHRASES = [
    "world's best","most trusted","#1","number one","best in class",
    "revolutionary","game-changing","unprecedented","unmatched","guaranteed",
    "100% proven","scientifically proven","doctors recommend","clinically proven",
    "fastest growing","market leader","industry leading","world-class",
]

def extract_text(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

def find_suspicious(text):
    return [p for p in SUSPICIOUS_PHRASES if p in text.lower()]

def extract_claims(text):
    prompt = f"""You are a fact-checking AI. Extract all specific verifiable factual claims from the text.
Focus ONLY on: statistics, percentages, revenue/market figures, user counts, dates tied to events, technical specs, scientific statistics.
Return ONLY a valid JSON array of claim strings. No markdown, no preamble.
Example: ["India has 950M internet users", "OpenAI reached 100M users in 2023"]
Text: {text[:4000]}"""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    return json.loads(clean)

def verify_claim(claim):
    results = tavily.search(claim, max_results=4)
    sources = [{"title":r.get("title",""),"url":r.get("url",""),"date":r.get("published_date","")} for r in results.get("results",[])]
    source_texts = "\n".join([f"- {r.get('title','')} ({r.get('url','')}): {r.get('content','')[:300]}" for r in results.get("results",[])])
    prompt = f"""You are a fact-checking AI. Analyze this claim against web evidence.
Claim: "{claim}"
Web Evidence:
{source_texts}

Classify as: VERIFIED, INACCURATE, FALSE, or NO_EVIDENCE.
Reply ONLY with this exact JSON (no markdown):
{{"verdict":"VERIFIED","explanation":"One clear sentence.","correct_fact":"Updated fact if wrong, else empty string.","ai_reasoning":"Brief note on which sources were checked and why confidence is high or low.","confidence":85}}
confidence is 0-100 integer."""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    data = json.loads(clean)
    data["sources"] = sources
    return data

def generate_ai_summary(results_list, verified, inaccurate, false_count, noev, total):
    bad = [c for c,r in results_list if r.get("verdict") in ["FALSE","INACCURATE"]][:3]
    prompt = f"""Write a 2-3 sentence professional AI fact-check summary.
Stats: {total} claims, {verified} verified, {inaccurate} inaccurate, {false_count} false, {noev} no evidence.
Sample problematic claims: {bad}
Write like: "This document contains X claims. Y appear verified, while Z contain outdated or unsupported data. Overall reliability is [assessment]."
Return ONLY the summary text."""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    return r.choices[0].message.content.strip()

def compute_trust(verified, inaccurate, false_count, noev, total):
    if total == 0: return 50
    return max(0, min(100, int((verified*100 + inaccurate*50 + noev*40 + false_count*0) / total)))

def verdict_badge(verdict):
    return {
        "VERIFIED":    '<span class="badge badge-verified">✅ Verified</span>',
        "INACCURATE":  '<span class="badge badge-inaccurate">⚠️ Outdated</span>',
        "FALSE":       '<span class="badge badge-false">❌ False</span>',
        "NO_EVIDENCE": '<span class="badge badge-noevidence">❓ No Evidence</span>',
    }.get(verdict, '<span class="badge badge-noevidence">❓ No Evidence</span>')

def css_class(verdict):
    return {"VERIFIED":"verified","INACCURATE":"inaccurate","FALSE":"false","NO_EVIDENCE":"noevidence"}.get(verdict,"noevidence")

def confidence_html(score):
    score = int(score) if score else 50
    cls   = "conf-high" if score >= 70 else "conf-med" if score >= 45 else "conf-low"
    color = "#22c55e"   if score >= 70 else "#f59e0b"  if score >= 45 else "#ef4444"
    return f"""<div class="conf-wrap">
        <div class="conf-label" style="color:{color};font-weight:500;font-size:0.71rem;">Confidence</div>
        <div class="conf-track"><div class="conf-fill {cls}" style="width:{score}%"></div></div>
        <div class="conf-pct" style="color:{color}">{score}%</div>
    </div>"""

def donut_chart(verified, inaccurate, false_count, noev, total):
    if total == 0: return ""
    cx, cy, r, circ = 70, 70, 52, 2*3.14159*52
    segments = [(verified/total,"#22c55e"),(inaccurate/total,"#f59e0b"),(false_count/total,"#ef4444"),(noev/total,"#4d5f80")]
    offset, paths = 0, []
    for ratio, color in segments:
        if ratio == 0: continue
        dash = ratio * circ
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="13" stroke-dasharray="{dash:.1f} {circ-dash:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash
    return f"""<svg viewBox="0 0 140 140" class="donut-svg">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1a2235" stroke-width="13"/>
        {"".join(paths)}
        <text x="{cx}" y="{cy-4}" text-anchor="middle" fill="#f0f4ff" font-size="20" font-weight="700" font-family="Syne,sans-serif">{total}</text>
        <text x="{cx}" y="{cy+12}" text-anchor="middle" fill="#4d5f80" font-size="9" font-family="DM Sans,sans-serif">claims</text>
    </svg>"""

# ═══════════════════════════════════════════════════════
# 🏠  HOME
# ═══════════════════════════════════════════════════════
if st.session_state.page == "Home":

    # ── HERO ────────────────────────────────────────────
    st.markdown("""
    <div class="hero">
        <div class="hero-tag"><div class="hero-dot"></div> AI-Powered Fact Verification</div>
        <div class="hero-title">Turn Information<br>into<span class="accent"> Verified Insight</span></div>
        <p class="hero-sub">Upload any PDF — FactChecker AI extracts every factual claim, searches the live web, and returns a verdict with confidence scores and corrected facts in under 60 seconds.</p>
        <div class="hero-cta-row">
            <button class="cta-primary" onclick="window.location.href='?nav=upload'">📤 Upload PDF — It's Free</button>
            <span class="cta-secondary">↓ See how it works</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA button (Streamlit native for nav)
    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        if st.button("📤  Upload Your PDF", key="hero_cta"):
            st.session_state.page = "Upload PDF"; st.rerun()
    with col_b:
        if st.button("✅  View Results", key="hero_results"):
            st.session_state.page = "Fact Check"; st.rerun()

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

    # ── HOW IT WORKS ────────────────────────────────────
    st.markdown('<div class="section-heading">How It Works</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Four steps from document to verified truth.</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="steps-grid">
        <div class="step-card">
            <div class="step-num"><div class="step-num-badge">1</div></div>
            <span class="step-ico">📤</span>
            <div class="step-title">Upload PDF</div>
            <div class="step-desc">Drop any report, article, or marketing document. Supports up to 50 MB.</div>
        </div>
        <div class="step-card">
            <div class="step-num"><div class="step-num-badge">2</div></div>
            <span class="step-ico">🧠</span>
            <div class="step-title">AI Extracts Claims</div>
            <div class="step-desc">LLaMA 3.3 70B identifies every verifiable statistic, percentage, and factual statement.</div>
        </div>
        <div class="step-card">
            <div class="step-num"><div class="step-num-badge">3</div></div>
            <span class="step-ico">🌐</span>
            <div class="step-title">Live Web Verification</div>
            <div class="step-desc">Each claim is searched against real-time web sources via Tavily — no cached data.</div>
        </div>
        <div class="step-card">
            <div class="step-num"><div class="step-num-badge">4</div></div>
            <span class="step-ico">📊</span>
            <div class="step-title">Results Generated</div>
            <div class="step-desc">Get a full report: ✅ Verified, ⚠️ Outdated, ❌ False — with sources and corrected facts.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

    # ── FEATURE CARDS ────────────────────────────────────
    st.markdown('<div class="section-heading">What FactChecker AI Does</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Every tool you need to audit a document for misinformation.</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-ico">🎯</div>
            <div class="feature-title">Claim Extraction</div>
            <div class="feature-desc">Automatically pulls out every verifiable factual statement — statistics, market figures, user counts, dates, and technical specs — from any PDF document.</div>
        </div>
        <div class="feature-card">
            <div class="feature-ico">🌐</div>
            <div class="feature-title">Live Web Verification</div>
            <div class="feature-desc">Each extracted claim is matched against four live web sources in real time. No static databases — just current, trustworthy evidence from across the internet.</div>
        </div>
        <div class="feature-card">
            <div class="feature-ico">🤖</div>
            <div class="feature-title">AI Analysis</div>
            <div class="feature-desc">LLaMA 3.3 70B cross-references web evidence with the original claim to return a verdict with a 0–100 confidence score and detailed AI reasoning.</div>
        </div>
        <div class="feature-card">
            <div class="feature-ico">📥</div>
            <div class="feature-title">Verification Reports</div>
            <div class="feature-desc">Download a complete structured report containing all verdicts, corrected facts, AI reasoning, source links, and a document trust score.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

    # ── ABOUT PROJECT ────────────────────────────────────
    st.markdown("""
    <div class="about-card">
        <div class="section-heading" style="margin-bottom:0.35rem;">About This Project</div>
        <div class="section-sub" style="margin-bottom:1.25rem;">Built to fight misinformation at the source — the document.</div>
        <div style="font-size:0.88rem;color:var(--text-2);line-height:1.85;font-weight:300;max-width:680px;">
            FactChecker AI was built to address a growing problem: PDFs — reports, whitepapers, marketing decks, and articles — are one of the primary ways misinformation spreads in professional contexts. Traditional fact-checking is slow and manual. This tool automates the entire pipeline.<br><br>
            Upload a document, and our AI extracts every falsifiable claim, runs a live web search for each one, and uses a large language model to reason about whether the claim is <strong style="color:var(--green)">verified</strong>, <strong style="color:var(--amber)">outdated</strong>, or <strong style="color:var(--red)">false</strong> — returning corrected facts and source links. The entire process takes under 60 seconds.
        </div>
        <div class="tech-chips">
            <span class="tech-chip">🦙 LLaMA 3.3 70B</span>
            <span class="tech-chip">⚡ Groq Inference</span>
            <span class="tech-chip">🌐 Tavily Web Search</span>
            <span class="tech-chip">📄 pdfplumber</span>
            <span class="tech-chip">🎈 Streamlit</span>
            <span class="tech-chip">🐍 Python</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FOOTER ───────────────────────────────────────────
    st.markdown("""
    <div class="footer">
        <div>
            <div class="footer-brand">🛡️ FactChecker AI</div>
            <div style="font-size:0.72rem;color:var(--text-3);margin-top:4px;">Built with AI + Live Web Verification</div>
        </div>
        <div class="footer-links">
            <a class="footer-link" href="https://github.com/ishamishra0421-gif/fact-checker" target="_blank">⬡ GitHub</a>
            <a class="footer-link" href="#" target="_blank">🚀 Deployed on Streamlit Cloud</a>
            <span class="footer-badge">v1.0.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 📤  UPLOAD PDF
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Upload PDF":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Upload your PDF</div>
        <div class="page-subtitle">Drop any document to begin AI-powered fact-checking. PDF only · Max 50 MB.</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF (Max 50MB)", type="pdf", label_visibility="visible")

    if not uploaded_file:
        st.markdown("""
        <div class="upload-zone">
            <span class="upload-icon">☁️</span>
            <div class="upload-title">Drag & drop your PDF here</div>
            <div class="upload-sub">or use the uploader above · PDF only · Max 50 MB</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-weight:600;font-size:0.95rem;color:var(--text);margin-bottom:1rem;">Try a Sample PDF</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-ico">📋</div>
                <div class="feature-title">Demo PDF — Real Facts</div>
                <div class="feature-desc">Contains accurate, verifiable claims and up-to-date statistics to see how verified results look.</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-ico">⚠️</div>
                <div class="feature-title">Trap PDF — Fake & Outdated</div>
                <div class="feature-desc">Contains intentionally false statistics to test the full detection and correction pipeline.</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("🔒 Your PDF is processed in memory only. No data is stored or shared.")
    else:
        st.success(f"✅  **{uploaded_file.name}** is ready to fact-check!")
        st.session_state.uploaded_file = uploaded_file
        st.session_state.results = None
        file_size = len(uploaded_file.getvalue()) / 1024
        st.markdown(f"""
        <div class="file-card">
            <div>
                <div style="font-weight:600;color:var(--text);font-size:0.92rem;">📄 {uploaded_file.name}</div>
                <div style="font-size:0.75rem;color:var(--text-3);margin-top:4px;">{file_size:.1f} KB · PDF Document</div>
            </div>
            <span class="badge badge-verified">Ready</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀  Start Fact Checking →"):
            st.session_state.page = "Fact Check"; st.rerun()

# ═══════════════════════════════════════════════════════
# ✅  FACT CHECK
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Fact Check":
    uploaded_file = st.session_state.get("uploaded_file")

    if uploaded_file is None:
        st.markdown('<div class="page-header"><div class="page-title">Fact Check</div></div>', unsafe_allow_html=True)
        st.warning("⚠️ No PDF uploaded. Please go to Upload PDF first.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()

    elif st.session_state.results is None:
        st.markdown("""
        <div class="page-header">
            <div class="page-title">Fact Check in progress…</div>
            <div class="page-subtitle">Extracting and verifying claims from your document. Please wait.</div>
        </div>
        """, unsafe_allow_html=True)

        stepper = st.empty()
        def render_stepper(active):
            steps = [
                ("📄","Reading PDF","Extracting text from document"),
                ("🧠","Extracting Claims","AI identifying verifiable facts"),
                ("🌐","Searching Web","Live web search per claim"),
                ("🔍","Verifying Facts","Cross-referencing with AI"),
                ("📊","Generating Report","Compiling your fact-check report"),
            ]
            html = '<div class="stepper">'
            for i,(icon,title,sub) in enumerate(steps):
                if i < active:    state, show = "done", "✓"
                elif i == active: state, show = "active", icon
                else:             state, show = "pending", icon
                tc = "var(--text)" if state in ["done","active"] else "var(--text-3)"
                html += f'<div class="s-step"><div class="s-indicator {state}"><span>{show}</span></div><div><div class="s-title" style="color:{tc}">{title}</div><div class="s-sub">{sub}</div></div></div>'
            stepper.markdown(html + "</div>", unsafe_allow_html=True)

        progress_bar = st.progress(0)
        status_txt   = st.empty()

        render_stepper(0)
        try:
            text = extract_text(uploaded_file)
            suspicious_phrases = find_suspicious(text)
        except Exception as e:
            st.error(f"❌ Could not read PDF: {e}"); st.stop()

        render_stepper(1)
        try:
            claims = extract_claims(text)
        except Exception as e:
            st.error(f"❌ Claim extraction failed: {e}"); claims = []

        if not claims:
            st.warning("⚠️ No verifiable claims found. Try a PDF with statistics or factual data."); st.stop()

        render_stepper(2)
        verified_count = inaccurate_count = false_count = noev_count = 0
        results_list = []

        for i, claim in enumerate(claims):
            render_stepper(3)
            status_txt.markdown(
                f'<div style="font-size:0.8rem;color:var(--text-2);padding:0.35rem 0;">'
                f'Verifying <b style="color:var(--blue)">{i+1}</b> of <b>{len(claims)}</b> — '
                f'<span style="font-style:italic;color:var(--text-3)">{claim[:70]}…</span></div>',
                unsafe_allow_html=True
            )
            try:
                result = verify_claim(claim)
            except:
                result = {"verdict":"NO_EVIDENCE","explanation":"Could not verify.","correct_fact":"","ai_reasoning":"Verification failed.","confidence":0,"sources":[]}
            results_list.append((claim, result))
            v = result.get("verdict","NO_EVIDENCE")
            if v=="VERIFIED":    verified_count+=1
            elif v=="INACCURATE": inaccurate_count+=1
            elif v=="FALSE":      false_count+=1
            else:                noev_count+=1
            progress_bar.progress((i+1)/len(claims))

        render_stepper(4)
        status_txt.empty()

        try:
            ai_summary = generate_ai_summary(results_list, verified_count, inaccurate_count, false_count, noev_count, len(claims))
        except:
            ai_summary = f"This document contains {len(claims)} factual claims. {verified_count} verified, {inaccurate_count} inaccurate, {false_count} false."

        trust_score = compute_trust(verified_count, inaccurate_count, false_count, noev_count, len(claims))

        st.session_state.results = {
            "filename": uploaded_file.name,
            "date": datetime.now().strftime("%b %d, %Y · %H:%M"),
            "claims": results_list,
            "verified": verified_count, "inaccurate": inaccurate_count,
            "false": false_count, "noevidence": noev_count,
            "total": len(claims), "trust_score": trust_score,
            "ai_summary": ai_summary, "suspicious": suspicious_phrases,
        }
        st.session_state.history.append({**st.session_state.results, "claims": None})
        st.rerun()

    else:
        r = st.session_state.results
        trust       = r.get("trust_score", 70)
        risk_label  = "Low Risk"    if trust >= 70 else "Medium Risk"  if trust >= 45 else "High Risk"
        risk_cls    = "risk-low"    if trust >= 70 else "risk-med"     if trust >= 45 else "risk-high"
        trust_color = "#22c55e"     if trust >= 70 else "#f59e0b"      if trust >= 45 else "#ef4444"

        st.markdown(f"""
        <div class="page-header">
            <div class="page-title">Fact check complete ✓</div>
            <div class="page-subtitle">📄 {r["filename"]} · {r["date"]}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="ai-summary"><div class="ai-label">🤖 AI Summary</div><div class="ai-text">{r.get("ai_summary","")}</div></div>', unsafe_allow_html=True)

        col_trust, col_metrics = st.columns([1, 3])
        with col_trust:
            st.markdown(f"""<div class="trust-card">
                <div class="trust-label">Trust Score</div>
                <div class="trust-num" style="color:{trust_color}">{trust}</div>
                <div class="trust-sub">/100</div>
                <span class="risk-tag {risk_cls}">{risk_label}</span>
            </div>""", unsafe_allow_html=True)
        with col_metrics:
            st.markdown(f"""<div class="metrics-grid">
                <div class="metric-card m-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
                <div class="metric-card m-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
                <div class="metric-card m-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Outdated</div></div>
                <div class="metric-card m-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
            </div>""", unsafe_allow_html=True)

        if r.get("suspicious"):
            chips = "".join([f'<span class="suspicious-chip">"{p}"</span>' for p in r["suspicious"]])
            st.markdown(f'<div class="suspicious-wrap"><div class="suspicious-header">🚨 Suspicious Marketing Language Detected</div><div class="suspicious-chips">{chips}</div></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊  View Dashboard"):
                st.session_state.page = "Dashboard"; st.rerun()
        with c2:
            if st.button("🔄  Check Another PDF"):
                st.session_state.results = None; st.session_state.uploaded_file = None
                st.session_state.page = "Upload PDF"; st.rerun()
        with c3:
            lines = [
                f"FactChecker AI — {r['filename']}",
                f"Date: {r['date']}",
                f"Trust Score: {trust}/100 ({risk_label})",
                f"Total: {r['total']} | Verified: {r['verified']} | Outdated: {r['inaccurate']} | False: {r['false']}",
                "", f"AI Summary: {r.get('ai_summary','')}", "", "="*60, ""
            ]
            for i,(claim,res) in enumerate(r["claims"],1):
                lines += [
                    f"{i}. [{res.get('verdict','?')}] {claim}",
                    f"   Explanation: {res.get('explanation','')}",
                    f"   Confidence: {res.get('confidence',0)}%"
                ]
                if res.get("correct_fact"):  lines.append(f"   Correct Fact: {res['correct_fact']}")
                if res.get("ai_reasoning"):  lines.append(f"   AI Reasoning: {res['ai_reasoning']}")
                for s in res.get("sources",[])[:2]:
                    if s.get("url"): lines.append(f"   Source: {s['url']}")
                lines.append("")
            st.download_button("📥  Download Report", data="\n".join(lines),
                               file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")

        st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.15rem;font-weight:700;color:var(--text);margin-bottom:1.1rem;letter-spacing:-0.02em;">Detailed Results</div>', unsafe_allow_html=True)

        for claim, result in r["claims"]:
            verdict    = result.get("verdict","NO_EVIDENCE")
            c_class    = css_class(verdict)
            correct    = result.get("correct_fact","")
            sources    = result.get("sources",[])
            confidence = result.get("confidence",50)
            ai_reason  = result.get("ai_reasoning","")

            if correct and verdict in ["FALSE","INACCURATE"]:
                extra = f'<div class="before-after"><div class="before-box"><div class="ba-label">❌ Uploaded Claim</div><div class="ba-text">{claim}</div></div><div class="after-box"><div class="ba-label">✅ Correct Fact</div><div class="ba-text">{correct}</div></div></div>'
            elif correct:
                extra = f'<div class="ai-reasoning"><div class="reasoning-label">📌 Correct Fact</div><div class="reasoning-text">{correct}</div></div>'
            else:
                extra = ""

            reasoning  = f'<div class="ai-reasoning"><div class="reasoning-label">🤖 AI Reasoning</div><div class="reasoning-text">{ai_reason}</div></div>' if ai_reason else ""
            src_links  = "".join([f'<a class="source-chip" href="{s["url"]}" target="_blank">🔗 {(s["title"] or s["url"])[:36]}…</a>' for s in sources[:3] if s.get("url")])
            sources_html = f'<div class="sources-list">{src_links}</div>' if src_links else ""

            st.markdown(f"""<div class="claim-card {c_class}">
                <div class="claim-header">
                    <div class="claim-text">{claim}</div>
                    <div>{verdict_badge(verdict)}</div>
                </div>
                <div class="claim-exp">{result.get('explanation','')}</div>
                {confidence_html(confidence)}
                {extra}{reasoning}{sources_html}
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 📊  DASHBOARD
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Dashboard":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Dashboard</div>
        <div class="page-subtitle">Analytics overview of your last fact-check session.</div>
    </div>
    """, unsafe_allow_html=True)

    r = st.session_state.results
    if r is None:
        st.info("No results yet. Upload a PDF to get started.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()
    else:
        total = r["total"] or 1
        trust = r.get("trust_score", 70)
        trust_color = "#22c55e" if trust >= 70 else "#f59e0b" if trust >= 45 else "#ef4444"

        st.markdown(f"""<div class="metrics-grid">
            <div class="metric-card m-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
            <div class="metric-card m-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
            <div class="metric-card m-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Outdated</div></div>
            <div class="metric-card m-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
        </div>""", unsafe_allow_html=True)

        donut = donut_chart(r["verified"],r["inaccurate"],r["false"],r["noevidence"],r["total"])
        st.markdown(f"""<div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Claim Distribution</div>
                {donut}
                <div class="legend-row"><div class="legend-dot" style="background:#22c55e"></div>Verified ({r['verified']})</div>
                <div class="legend-row"><div class="legend-dot" style="background:#f59e0b"></div>Outdated ({r['inaccurate']})</div>
                <div class="legend-row"><div class="legend-dot" style="background:#ef4444"></div>False ({r['false']})</div>
                <div class="legend-row"><div class="legend-dot" style="background:#4d5f80"></div>No Evidence ({r['noevidence']})</div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Verification Breakdown</div>
                <div class="bar-row"><div class="bar-label">✅ Verified</div><div class="bar-track"><div class="bar-fill" style="width:{r['verified']/total*100:.0f}%;background:#22c55e;"></div></div><div class="bar-pct">{r['verified']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">⚠️ Outdated</div><div class="bar-track"><div class="bar-fill" style="width:{r['inaccurate']/total*100:.0f}%;background:#f59e0b;"></div></div><div class="bar-pct">{r['inaccurate']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❌ False</div><div class="bar-track"><div class="bar-fill" style="width:{r['false']/total*100:.0f}%;background:#ef4444;"></div></div><div class="bar-pct">{r['false']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❓ No Evidence</div><div class="bar-track"><div class="bar-fill" style="width:{r['noevidence']/total*100:.0f}%;background:#4d5f80;"></div></div><div class="bar-pct">{r['noevidence']/total*100:.0f}%</div></div>
                <div style="margin-top:1.2rem;padding-top:1.1rem;border-top:1px solid var(--border);">
                    <div style="font-size:0.65rem;color:var(--text-3);margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Trust Score</div>
                    <div style="font-family:'Syne',sans-serif;font-size:2.1rem;font-weight:800;color:{trust_color};letter-spacing:-0.04em;">{trust}<span style="font-size:0.9rem;opacity:0.4">/100</span></div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if r.get("ai_summary"):
            st.markdown(f'<div class="ai-summary"><div class="ai-label">🤖 AI Summary</div><div class="ai-text">{r["ai_summary"]}</div></div>', unsafe_allow_html=True)

        if st.button("📋  View Detailed Results"):
            st.session_state.page = "Fact Check"; st.rerun()

# ═══════════════════════════════════════════════════════
# 🕐  HISTORY
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "History":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">History</div>
        <div class="page-subtitle">All previously fact-checked documents this session.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow-sm);">
            <div style="font-size:2.75rem;margin-bottom:0.75rem;">🕐</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:var(--text);font-size:1.2rem;margin-bottom:0.4rem;">No history yet</div>
            <div style="font-size:0.82rem;color:var(--text-3);font-weight:300;">Your fact-check results will appear here after analyzing a PDF.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;'
            'padding:.4rem 1.35rem;font-size:.63rem;font-weight:600;color:var(--text-3);'
            'text-transform:uppercase;letter-spacing:.09em;">'
            '<div>Document</div><div>Total</div><div>✅</div><div>⚠️</div><div>❌</div><div>Date</div></div>',
            unsafe_allow_html=True
        )
        for h in reversed(st.session_state.history):
            trust = h.get("trust_score", 70)
            tc = "#22c55e" if trust >= 70 else "#f59e0b" if trust >= 45 else "#ef4444"
            st.markdown(f"""<div class="history-row">
                <div>
                    <div style="font-weight:600;color:var(--text);font-size:0.88rem;">📄 {h["filename"]}</div>
                    <div style="font-size:0.71rem;color:var(--text-3);margin-top:3px;">Trust: <span style="color:{tc};font-weight:700;">{trust}/100</span></div>
                </div>
                <div style="font-weight:700;color:var(--text);">{h["total"]}</div>
                <div style="color:#22c55e;font-weight:700;">{h["verified"]}</div>
                <div style="color:#f59e0b;font-weight:700;">{h["inaccurate"]}</div>
                <div style="color:#ef4444;font-weight:700;">{h["false"]}</div>
                <div style="font-size:0.75rem;color:var(--text-3);">{h["date"]}</div>
            </div>""", unsafe_allow_html=True)
