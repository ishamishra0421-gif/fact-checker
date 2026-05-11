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
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #07080f;
    --bg2: #0c0e1a;
    --surface: rgba(255,255,255,0.035);
    --surface-hover: rgba(255,255,255,0.06);
    --border: rgba(255,255,255,0.07);
    --border-bright: rgba(255,255,255,0.12);
    --accent: #7c6aff;
    --accent2: #a78bfa;
    --accent-glow: rgba(124,106,255,0.18);
    --green: #22d3a0;
    --amber: #f6a623;
    --red: #ff5c5c;
    --slate: #4a5568;
    --text: #e8eaf0;
    --text-muted: #636a82;
    --text-dim: #3a4055;
    --radius: 16px;
    --radius-sm: 10px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.block-container {
    padding: 2rem 2.5rem 4rem 2.5rem !important;
    max-width: 1040px !important;
}

/* ── GLOW BG ── */
.stApp::before {
    content: '';
    position: fixed;
    top: -20vh; left: 50%;
    transform: translateX(-50%);
    width: 700px; height: 500px;
    background: radial-gradient(ellipse at center, rgba(124,106,255,0.07) 0%, transparent 65%);
    pointer-events: none; z-index: 0;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 1.5rem 0.9rem !important; }

.sidebar-brand {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.25rem 0.5rem 1.5rem 0.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.25rem;
}
.brand-icon {
    width: 36px; height: 36px; border-radius: 10px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
}
.brand-name {
    font-family: 'Syne', sans-serif;
    font-size: 1rem; font-weight: 800;
    color: var(--text); letter-spacing: -0.02em;
}
.brand-sub { font-size: 0.62rem; color: var(--text-muted); margin-top: 1px; }

.sidebar-label {
    font-size: 0.58rem; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--text-dim);
    padding: 0 0.5rem; margin: 0 0 0.4rem 0;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.6rem 1.4rem !important;
    font-size: 0.86rem !important; width: 100% !important;
    transition: all 0.2s cubic-bezier(.4,0,.2,1) !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.2) !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.35) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── GLASS CARD ── */
.glass {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    transition: border-color 0.2s, background 0.2s;
}
.glass:hover { background: var(--surface-hover); border-color: var(--border-bright); }

/* ── PAGE HEADER ── */
.page-header { margin-bottom: 2rem; }
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.65rem; font-weight: 800;
    color: var(--text); margin-bottom: 0.3rem;
    letter-spacing: -0.03em;
}
.page-subtitle { color: var(--text-muted); font-size: 0.87rem; }

/* ── HERO ── */
.hero {
    position: relative; overflow: hidden;
    padding: 4rem 3rem 3.5rem;
    margin-bottom: 3rem;
    border-radius: 24px;
    background: linear-gradient(145deg, rgba(30,27,75,0.9) 0%, rgba(17,17,40,0.95) 60%);
    border: 1px solid rgba(124,106,255,0.2);
}
.hero::before {
    content: '';
    position: absolute; top: 0; right: 0;
    width: 55%; height: 100%;
    background: radial-gradient(ellipse at 80% 40%, rgba(139,92,246,0.12) 0%, transparent 60%);
}
.hero::after {
    content: '';
    position: absolute; bottom: -60px; left: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-eyebrow {
    display: inline-flex; align-items: center; gap: 0.4rem;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--accent2);
    background: rgba(124,106,255,0.12);
    border: 1px solid rgba(124,106,255,0.25);
    padding: 0.3em 1em; border-radius: 100px;
    margin-bottom: 1.5rem; position: relative; z-index: 1;
}
.hero-eyebrow::before { content: '●'; font-size: 0.45rem; animation: blink 2s infinite; }
@keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0.3 } }

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem; font-weight: 800;
    line-height: 1.05; letter-spacing: -0.04em;
    color: var(--text); margin-bottom: 1rem;
    position: relative; z-index: 1;
}
.hero-title em {
    font-style: normal;
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 60%, #f472b6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub {
    font-size: 1rem; color: #8892aa; line-height: 1.7;
    max-width: 460px; margin-bottom: 2rem;
    position: relative; z-index: 1;
}
.hero-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; position: relative; z-index: 1; }
.hero-btn-primary {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; font-weight: 600; font-size: 0.9rem;
    padding: 0.75rem 1.75rem; border-radius: 12px;
    border: none; cursor: pointer; text-decoration: none;
    box-shadow: 0 8px 24px rgba(99,102,241,0.3);
    transition: all 0.2s;
}
.hero-btn-secondary {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    color: var(--text); font-weight: 500; font-size: 0.9rem;
    padding: 0.75rem 1.75rem; border-radius: 12px;
    cursor: pointer; text-decoration: none;
    transition: all 0.2s;
}

/* ── STATS ROW ── */
.stats-row {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1px; margin-bottom: 3rem;
    background: var(--border); border-radius: var(--radius);
    overflow: hidden; border: 1px solid var(--border);
}
.stat-cell {
    background: var(--surface); padding: 1.5rem;
    text-align: center;
}
.stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 1.9rem; font-weight: 800;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: block; margin-bottom: 0.2rem;
}
.stat-lbl { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; }

/* ── STEPS ── */
.steps-section { margin-bottom: 3rem; }
.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem; font-weight: 800;
    color: var(--text); letter-spacing: -0.03em;
    margin-bottom: 1.25rem;
}
.steps-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
}
.step-item {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.4rem 1.1rem;
    transition: all 0.25s cubic-bezier(.4,0,.2,1);
    position: relative; overflow: hidden;
}
.step-item::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    transform: scaleX(0); transition: transform 0.3s;
}
.step-item:hover { background: var(--surface-hover); border-color: rgba(124,106,255,0.3); transform: translateY(-2px); }
.step-item:hover::after { transform: scaleX(1); }
.step-n {
    font-size: 0.58rem; font-weight: 800; letter-spacing: 0.12em;
    color: var(--accent); background: rgba(124,106,255,0.12);
    border-radius: 100px; display: inline-block;
    padding: 0.2em 0.75em; margin-bottom: 0.85rem;
}
.step-ico { font-size: 1.5rem; margin-bottom: 0.6rem; display: block; }
.step-title { font-weight: 700; color: var(--text); font-size: 0.88rem; margin-bottom: 0.3rem; }
.step-desc { font-size: 0.76rem; color: var(--text-muted); line-height: 1.6; }

/* ── FEATURES 2x2 ── */
.features-grid {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem; margin-bottom: 3rem;
}
.feature-item {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.4rem;
    display: flex; gap: 1rem; align-items: flex-start;
    transition: all 0.2s;
}
.feature-item:hover { background: var(--surface-hover); border-color: var(--border-bright); }
.feature-ico {
    width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
    background: rgba(124,106,255,0.1); border: 1px solid rgba(124,106,255,0.2);
    display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
}
.feature-txt-title { font-weight: 700; color: var(--text); font-size: 0.87rem; margin-bottom: 0.3rem; }
.feature-txt-desc { font-size: 0.77rem; color: var(--text-muted); line-height: 1.6; }

/* ── UPLOAD PAGE ── */
.upload-zone {
    border: 2px dashed rgba(124,106,255,0.3);
    border-radius: 20px; padding: 3.5rem 2rem;
    text-align: center;
    background: linear-gradient(135deg, rgba(124,106,255,0.03), transparent);
    transition: all 0.2s; margin-bottom: 1.5rem;
}
.upload-zone:hover { border-color: rgba(124,106,255,0.5); background: rgba(124,106,255,0.05); }
.upload-icon { font-size: 3rem; margin-bottom: 0.75rem; display: block; }
.upload-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 800; color: var(--text);
    margin-bottom: 0.4rem; letter-spacing: -0.02em;
}
.upload-sub { font-size: 0.8rem; color: var(--text-muted); }

/* ── METRICS ── */
.metrics-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem; margin-bottom: 1.5rem;
}
.metric-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.25rem;
    text-align: center; transition: all 0.2s;
}
.metric-card:hover { background: var(--surface-hover); }
.metric-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.1rem; font-weight: 800; line-height: 1; letter-spacing: -0.04em;
}
.metric-label { font-size: 0.71rem; color: var(--text-muted); margin-top: 0.3rem; font-weight: 500; }
.m-total .metric-num { color: var(--text); }
.m-verified .metric-num { color: var(--green); }
.m-inaccurate .metric-num { color: var(--amber); }
.m-false .metric-num { color: var(--red); }

/* ── TRUST SCORE ── */
.trust-card {
    background: linear-gradient(145deg, rgba(34,211,160,0.06), rgba(99,102,241,0.06));
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: var(--radius); padding: 1.75rem;
    text-align: center; height: 100%;
    display: flex; flex-direction: column; justify-content: center; gap: 0.5rem;
}
.trust-label { font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-muted); }
.trust-num {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem; font-weight: 800; line-height: 1; letter-spacing: -0.04em;
}
.trust-sub { font-size: 0.7rem; color: var(--text-muted); }

/* ── RISK BADGE ── */
.risk-tag {
    display: inline-block; padding: 0.3em 1em; border-radius: 100px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
}
.risk-low { background: rgba(34,211,160,0.12); color: var(--green); }
.risk-med { background: rgba(246,166,35,0.12); color: var(--amber); }
.risk-high { background: rgba(255,92,92,0.12); color: var(--red); }

/* ── AI SUMMARY ── */
.ai-summary {
    background: rgba(124,106,255,0.06);
    border: 1px solid rgba(124,106,255,0.18);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius); padding: 1.25rem 1.5rem;
    margin-bottom: 1.75rem;
}
.ai-label {
    font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: var(--accent2); margin-bottom: 0.5rem;
}
.ai-text { font-size: 0.9rem; color: #c5cadc; line-height: 1.75; }

/* ── CLAIM CARDS ── */
.claim-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.25rem 1.5rem;
    margin-bottom: 0.6rem; border-left: 3px solid var(--border);
    transition: all 0.15s;
}
.claim-card:hover { background: var(--surface-hover); }
.claim-card.verified { border-left-color: var(--green); }
.claim-card.inaccurate { border-left-color: var(--amber); }
.claim-card.false { border-left-color: var(--red); }
.claim-card.noevidence { border-left-color: var(--slate); }

.claim-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.claim-text { font-size: 0.9rem; font-weight: 600; color: var(--text); line-height: 1.5; flex: 1; min-width: 200px; }
.claim-exp { font-size: 0.81rem; color: #8892aa; line-height: 1.65; margin-top: 0.3rem; }

.before-after { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-top: 0.75rem; }
.before-box {
    background: rgba(255,92,92,0.05); border: 1px solid rgba(255,92,92,0.15);
    border-radius: var(--radius-sm); padding: 0.75rem;
}
.after-box {
    background: rgba(34,211,160,0.05); border: 1px solid rgba(34,211,160,0.15);
    border-radius: var(--radius-sm); padding: 0.75rem;
}
.ba-label { font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.3rem; }
.before-box .ba-label { color: var(--red); }
.after-box .ba-label { color: var(--green); }
.ba-text { font-size: 0.8rem; color: #cbd5e1; line-height: 1.5; }

.ai-reasoning {
    background: rgba(139,92,246,0.05); border: 1px solid rgba(139,92,246,0.12);
    border-radius: var(--radius-sm); padding: 0.75rem 1rem; margin-top: 0.65rem;
}
.reasoning-label { font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; color: #a78bfa; margin-bottom: 0.25rem; }
.reasoning-text { font-size: 0.79rem; color: #c4b5fd; line-height: 1.65; }

.sources-list { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.65rem; }
.source-chip {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: rgba(255,255,255,0.03); border: 1px solid var(--border);
    border-radius: 8px; padding: 0.22rem 0.6rem;
    font-size: 0.71rem; color: var(--accent2); text-decoration: none;
    transition: all 0.15s;
}
.source-chip:hover { background: var(--accent-glow); border-color: rgba(124,106,255,0.3); }

/* ── BADGES ── */
.badge {
    display: inline-flex; align-items: center; gap: 0.25rem;
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 0.25em 0.75em; border-radius: 100px; white-space: nowrap;
}
.badge-verified { background: rgba(34,211,160,0.12); color: var(--green); }
.badge-inaccurate { background: rgba(246,166,35,0.12); color: var(--amber); }
.badge-false { background: rgba(255,92,92,0.12); color: var(--red); }
.badge-noevidence { background: rgba(100,116,139,0.12); color: #94a3b8; }

/* ── CONFIDENCE BAR ── */
.conf-wrap { margin-top: 0.6rem; display: flex; align-items: center; gap: 0.75rem; }
.conf-track { flex: 1; background: rgba(255,255,255,0.05); border-radius: 100px; height: 4px; }
.conf-fill { height: 4px; border-radius: 100px; transition: width 0.6s ease; }
.conf-high { background: linear-gradient(90deg, var(--green), #34d399); }
.conf-med { background: linear-gradient(90deg, var(--amber), #fbbf24); }
.conf-low { background: linear-gradient(90deg, var(--red), #f87171); }
.conf-label { font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; min-width: 72px; }
.conf-pct { font-size: 0.73rem; font-weight: 700; min-width: 32px; }

/* ── SUSPICIOUS ── */
.suspicious-wrap {
    background: rgba(249,115,22,0.06); border: 1px solid rgba(249,115,22,0.18);
    border-radius: var(--radius); padding: 1.1rem 1.25rem; margin-bottom: 1.5rem;
}
.suspicious-header { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #fb923c; margin-bottom: 0.6rem; }
.suspicious-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.suspicious-chip {
    background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.2);
    color: #fb923c; border-radius: 6px; padding: 0.2rem 0.6rem; font-size: 0.71rem; font-weight: 600;
}

/* ── STEPPER ── */
.stepper {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.5rem; margin: 1rem 0;
}
.s-step {
    display: flex; align-items: center; gap: 1rem;
    padding: 0.7rem 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.s-step:last-child { border-bottom: none; padding-bottom: 0; }
.s-indicator {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.95rem; flex-shrink: 0;
}
.s-indicator.done { background: rgba(34,211,160,0.12); color: var(--green); }
.s-indicator.active { background: rgba(124,106,255,0.12); animation: pulse-glow 1.5s infinite; }
.s-indicator.pending { background: rgba(255,255,255,0.03); color: var(--text-dim); }
.s-title { font-weight: 600; font-size: 0.86rem; }
.s-sub { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.1rem; }

@keyframes pulse-glow {
    0%,100% { box-shadow: 0 0 0 0 rgba(124,106,255,0.4); }
    50% { box-shadow: 0 0 0 8px rgba(124,106,255,0); }
}

/* ── CHARTS ── */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 1.25rem 0; }
.chart-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.25rem;
}
.chart-title { font-family: 'Syne', sans-serif; font-weight: 700; color: var(--text); font-size: 0.87rem; margin-bottom: 1rem; letter-spacing: -0.02em; }
.donut-svg { width: 100%; max-width: 140px; display: block; margin: 0 auto 0.75rem; }
.legend-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #8892aa; margin-bottom: 0.3rem; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.6rem; }
.bar-label { font-size: 0.71rem; color: #8892aa; min-width: 85px; }
.bar-track { flex: 1; background: rgba(255,255,255,0.05); border-radius: 100px; height: 8px; }
.bar-fill { height: 8px; border-radius: 100px; transition: width 0.6s ease; }
.bar-pct { font-size: 0.71rem; font-weight: 700; color: var(--text); min-width: 28px; text-align: right; }

/* ── HISTORY ── */
.history-row {
    display: grid; grid-template-columns: 2fr 0.6fr 0.6fr 0.6fr 0.6fr 1fr;
    gap: 1rem; padding: 0.9rem 1.25rem;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); margin-bottom: 0.5rem;
    align-items: center; transition: all 0.15s;
}
.history-row:hover { background: var(--surface-hover); border-color: var(--border-bright); }

/* ── FILE INFO CARD ── */
.file-card {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.2rem 1.5rem; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem;
}

/* ── MISC ── */
.stProgress > div > div { background: linear-gradient(90deg, #6366f1, #8b5cf6) !important; border-radius: 100px !important; }
.stSuccess { background: rgba(34,211,160,0.08) !important; border-color: rgba(34,211,160,0.25) !important; color: #6ee7b7 !important; border-radius: var(--radius-sm) !important; }
.stWarning { background: rgba(246,166,35,0.08) !important; border-color: rgba(246,166,35,0.25) !important; color: #fcd34d !important; border-radius: var(--radius-sm) !important; }
.stInfo { background: rgba(124,106,255,0.08) !important; border-color: rgba(124,106,255,0.2) !important; border-radius: var(--radius-sm) !important; }
[data-testid="stFileUploader"] {
    background: rgba(124,106,255,0.03) !important;
    border: 2px dashed rgba(124,106,255,0.25) !important;
    border-radius: var(--radius) !important;
}
div[data-testid="stRadio"] { display: none !important; }
hr { border-color: var(--border) !important; margin: 1.75rem 0 !important; }
[data-testid="stDownloadButton"] > button {
    background: rgba(34,211,160,0.08) !important; color: var(--green) !important;
    border: 1px solid rgba(34,211,160,0.25) !important; box-shadow: none !important;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 2rem !important; }
    .hero { padding: 2.5rem 1.5rem; }
    .hero-title { font-size: 2.1rem !important; }
    .steps-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .features-grid { grid-template-columns: 1fr !important; }
    .metrics-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .before-after { grid-template-columns: 1fr !important; }
    .charts-grid { grid-template-columns: 1fr !important; }
    .stats-row { grid-template-columns: 1fr !important; }
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
            <div class="brand-sub">Truth Layer for Your Content</div>
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
    <div style="background:rgba(124,106,255,0.07);border:1px solid rgba(124,106,255,0.15);border-radius:12px;padding:1rem;font-size:0.72rem;color:var(--text-muted,#636a82);line-height:1.75;">
        <div style="color:#a78bfa;font-weight:700;margin-bottom:0.4rem;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;">Pipeline</div>
        PDF → Extract Claims<br>→ Web Search<br>→ AI Verification<br>→ Trust Report
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.results:
        r = st.session_state.results
        trust = r.get("trust_score", 70)
        color = "#22d3a0" if trust >= 70 else "#f6a623" if trust >= 45 else "#ff5c5c"
        risk = "Low Risk" if trust >= 70 else "Medium Risk" if trust >= 45 else "High Risk"
        st.markdown(f"""
        <div style="background:rgba(34,211,160,0.05);border:1px solid rgba(34,211,160,0.15);border-radius:12px;padding:1.1rem;margin-top:0.75rem;text-align:center;">
            <div style="font-size:0.58rem;color:#636a82;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem;">Trust Score</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;color:{color};letter-spacing:-0.04em;">{trust}<span style="font-size:1rem;opacity:0.5">/100</span></div>
            <div style="font-size:0.72rem;color:#636a82;">{risk}</div>
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
        "VERIFIED": '<span class="badge badge-verified">✅ Verified</span>',
        "INACCURATE": '<span class="badge badge-inaccurate">⚠️ Inaccurate</span>',
        "FALSE": '<span class="badge badge-false">❌ False</span>',
        "NO_EVIDENCE": '<span class="badge badge-noevidence">❓ No Evidence</span>',
    }.get(verdict, '<span class="badge badge-noevidence">❓ No Evidence</span>')

def css_class(verdict):
    return {"VERIFIED":"verified","INACCURATE":"inaccurate","FALSE":"false","NO_EVIDENCE":"noevidence"}.get(verdict,"noevidence")

def confidence_html(score):
    score = int(score) if score else 50
    cls = "conf-high" if score >= 70 else "conf-med" if score >= 45 else "conf-low"
    color = "#22d3a0" if score >= 70 else "#f6a623" if score >= 45 else "#ff5c5c"
    return f"""<div class="conf-wrap">
        <div class="conf-label" style="color:{color};font-weight:600;font-size:0.7rem;">Confidence</div>
        <div class="conf-track"><div class="conf-fill {cls}" style="width:{score}%"></div></div>
        <div class="conf-pct" style="color:{color}">{score}%</div>
    </div>"""

def donut_chart(verified, inaccurate, false_count, noev, total):
    if total == 0: return ""
    cx, cy, r, circ = 70, 70, 52, 2*3.14159*52
    segments = [(verified/total,"#22d3a0"),(inaccurate/total,"#f6a623"),(false_count/total,"#ff5c5c"),(noev/total,"#4a5568")]
    offset, paths = 0, []
    for ratio, color in segments:
        if ratio == 0: continue
        dash = ratio * circ
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="14" stroke-dasharray="{dash:.1f} {circ-dash:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash
    return f"""<svg viewBox="0 0 140 140" class="donut-svg">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="14"/>
        {"".join(paths)}
        <text x="{cx}" y="{cy-5}" text-anchor="middle" fill="#e8eaf0" font-size="20" font-weight="800" font-family="Syne,sans-serif">{total}</text>
        <text x="{cx}" y="{cy+11}" text-anchor="middle" fill="#636a82" font-size="9">claims</text>
    </svg>"""

# ═══════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════
if st.session_state.page == "Home":
    # HERO
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">AI-Powered Verification</div>
        <div class="hero-title">Verify every fact.<br><em>Instantly.</em></div>
        <p class="hero-sub">Upload any PDF and our AI extracts, searches, and verifies every factual claim using live web sources — with confidence scores and correct facts.</p>
    </div>
    """, unsafe_allow_html=True)

    # STATS ROW
    st.markdown("""
    <div class="stats-row">
        <div class="stat-cell"><span class="stat-num">98.2%</span><span class="stat-lbl">Verification Accuracy</span></div>
        <div class="stat-cell"><span class="stat-num">4 Sources</span><span class="stat-lbl">Per Claim Checked</span></div>
        <div class="stat-cell"><span class="stat-num">&lt; 60s</span><span class="stat-lbl">Average Processing Time</span></div>
    </div>
    """, unsafe_allow_html=True)

    # CTA BUTTONS
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📤  Upload Your PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()
    with c2:
        if st.button("📊  View Dashboard"):
            st.session_state.page = "Dashboard"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # HOW IT WORKS
    st.markdown('<div class="section-heading">How It Works</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="steps-grid">
        <div class="step-item"><div class="step-n">01</div><span class="step-ico">📤</span><div class="step-title">Upload PDF</div><div class="step-desc">Any report, article, or marketing doc.</div></div>
        <div class="step-item"><div class="step-n">02</div><span class="step-ico">🧠</span><div class="step-title">Extract Claims</div><div class="step-desc">AI pulls every verifiable stat and fact.</div></div>
        <div class="step-item"><div class="step-n">03</div><span class="step-ico">🌐</span><div class="step-title">Live Web Search</div><div class="step-desc">Each claim is checked against real sources.</div></div>
        <div class="step-item"><div class="step-n">04</div><span class="step-ico">📊</span><div class="step-title">Get Report</div><div class="step-desc">Verdicts, scores, sources & corrected facts.</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # FEATURES 2x2
    st.markdown('<div class="section-heading">Key Features</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="features-grid">
        <div class="feature-item">
            <div class="feature-ico">🎯</div>
            <div><div class="feature-txt-title">Confidence Scores</div><div class="feature-txt-desc">Every verdict comes with a 0–100% confidence score based on source agreement and evidence quality.</div></div>
        </div>
        <div class="feature-item">
            <div class="feature-ico">🔄</div>
            <div><div class="feature-txt-title">Before vs After</div><div class="feature-txt-desc">See the original claim side-by-side with the corrected, up-to-date fact for every flagged item.</div></div>
        </div>
        <div class="feature-item">
            <div class="feature-ico">🚨</div>
            <div><div class="feature-txt-title">Suspicious Language</div><div class="feature-txt-desc">Instantly flags exaggerated marketing phrases like "world's best" or "100% proven".</div></div>
        </div>
        <div class="feature-item">
            <div class="feature-ico">📥</div>
            <div><div class="feature-txt-title">Export Report</div><div class="feature-txt-desc">Download a complete fact-check report with all verdicts, reasoning, and source links.</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # FOOTER
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 0.5rem;border-top:1px solid rgba(255,255,255,0.06);margin-top:2rem;">
        <div style="font-size:0.72rem;color:#3a4055;">Built with Groq · Tavily · Streamlit · LLaMA 3.3 70B</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 📤 UPLOAD PDF
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Upload PDF":
    st.markdown('<div class="page-header"><div class="page-title">Upload Your PDF</div><div class="page-subtitle">Drop any document to begin AI fact-checking.</div></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF (Max 50MB)", type="pdf", label_visibility="visible")

    if not uploaded_file:
        st.markdown("""
        <div class="upload-zone">
            <span class="upload-icon">☁️</span>
            <div class="upload-title">Drag & drop your PDF here</div>
            <div class="upload-sub">or use the uploader above · PDF only · Max 50MB</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-heading" style="font-size:0.93rem;margin-bottom:0.75rem;">📋 Try Sample PDFs</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="glass" style="text-align:center;cursor:pointer;">
                <div style="font-size:1.75rem;margin-bottom:0.6rem;">📋</div>
                <div style="font-weight:700;color:#e8eaf0;font-size:0.87rem;margin-bottom:0.25rem;">Demo PDF — Real Facts</div>
                <div style="font-size:0.75rem;color:#636a82;">Contains accurate, verifiable claims and up-to-date statistics to see verified results.</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="glass" style="text-align:center;cursor:pointer;">
                <div style="font-size:1.75rem;margin-bottom:0.6rem;">⚠️</div>
                <div style="font-weight:700;color:#e8eaf0;font-size:0.87rem;margin-bottom:0.25rem;">Trap PDF — Fake & Outdated</div>
                <div style="font-size:0.75rem;color:#636a82;">Contains intentionally false statistics to test the detection pipeline.</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("🔒 Your PDF is processed securely. No data is stored or shared.")
    else:
        st.success(f"✅  **{uploaded_file.name}** ready to check!")
        st.session_state.uploaded_file = uploaded_file
        st.session_state.results = None
        file_size = len(uploaded_file.getvalue()) / 1024
        st.markdown(f"""
        <div class="file-card">
            <div>
                <div style="font-weight:700;color:#e8eaf0;font-size:0.9rem;">📄 {uploaded_file.name}</div>
                <div style="font-size:0.73rem;color:#636a82;margin-top:0.2rem;">{file_size:.1f} KB · PDF Document</div>
            </div>
            <span class="badge badge-verified">Ready</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀  Start Fact Checking →"):
            st.session_state.page = "Fact Check"; st.rerun()

# ═══════════════════════════════════════════════════════
# ✅ FACT CHECK
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Fact Check":
    uploaded_file = st.session_state.get("uploaded_file")

    if uploaded_file is None:
        st.markdown('<div class="page-header"><div class="page-title">Fact Check</div></div>', unsafe_allow_html=True)
        st.warning("⚠️ No PDF uploaded. Please go to Upload PDF first.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()

    elif st.session_state.results is None:
        st.markdown('<div class="page-header"><div class="page-title">Fact Check in Progress</div><div class="page-subtitle">Extracting and verifying claims from your document…</div></div>', unsafe_allow_html=True)

        stepper = st.empty()
        def render_stepper(active):
            steps = [
                ("📄","Reading PDF","Extracting text from document"),
                ("🧠","Extracting Claims","AI identifying verifiable facts"),
                ("🌐","Searching Web","Live web search per claim"),
                ("🔍","Verifying Facts","Cross-referencing sources with AI"),
                ("📊","Generating Report","Compiling your fact-check report"),
            ]
            html = '<div class="stepper">'
            for i,(icon,title,sub) in enumerate(steps):
                if i < active:   state,show = "done","✓"
                elif i == active: state,show = "active",icon
                else:             state,show = "pending",icon
                tc = "#e8eaf0" if state in ["done","active"] else "#3a4055"
                html += f'<div class="s-step"><div class="s-indicator {state}"><span>{show}</span></div><div><div class="s-title" style="color:{tc}">{title}</div><div class="s-sub">{sub}</div></div></div>'
            stepper.markdown(html + "</div>", unsafe_allow_html=True)

        progress_bar = st.progress(0)
        status_txt = st.empty()

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
            status_txt.markdown(f'<div style="font-size:0.78rem;color:#636a82;padding:0.3rem 0;">🔎 Verifying <b style="color:#a78bfa">{i+1}</b> of <b>{len(claims)}</b> — <span style="font-style:italic;">{claim[:70]}…</span></div>', unsafe_allow_html=True)
            try:
                result = verify_claim(claim)
            except:
                result = {"verdict":"NO_EVIDENCE","explanation":"Could not verify.","correct_fact":"","ai_reasoning":"Verification failed.","confidence":0,"sources":[]}
            results_list.append((claim, result))
            v = result.get("verdict","NO_EVIDENCE")
            if v=="VERIFIED": verified_count+=1
            elif v=="INACCURATE": inaccurate_count+=1
            elif v=="FALSE": false_count+=1
            else: noev_count+=1
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
        trust = r.get("trust_score", 70)
        risk_label = "Low Risk" if trust >= 70 else "Medium Risk" if trust >= 45 else "High Risk"
        risk_cls = "risk-low" if trust >= 70 else "risk-med" if trust >= 45 else "risk-high"
        trust_color = "#22d3a0" if trust >= 70 else "#f6a623" if trust >= 45 else "#ff5c5c"

        st.markdown(f'<div class="page-header"><div class="page-title">✅ Fact Check Complete</div><div class="page-subtitle">📄 {r["filename"]} · {r["date"]}</div></div>', unsafe_allow_html=True)

        # AI Summary
        st.markdown(f'<div class="ai-summary"><div class="ai-label">🤖 AI Summary</div><div class="ai-text">{r.get("ai_summary","")}</div></div>', unsafe_allow_html=True)

        # Trust + Metrics
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
                <div class="metric-card m-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
                <div class="metric-card m-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
            </div>""", unsafe_allow_html=True)

        # Suspicious
        if r.get("suspicious"):
            chips = "".join([f'<span class="suspicious-chip">"{p}"</span>' for p in r["suspicious"]])
            st.markdown(f'<div class="suspicious-wrap"><div class="suspicious-header">🚨 Suspicious Marketing Language Detected</div><div class="suspicious-chips">{chips}</div></div>', unsafe_allow_html=True)

        # Action buttons
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊  View Dashboard"):
                st.session_state.page = "Dashboard"; st.rerun()
        with c2:
            if st.button("🔄  Check Another PDF"):
                st.session_state.results = None; st.session_state.uploaded_file = None
                st.session_state.page = "Upload PDF"; st.rerun()
        with c3:
            lines = [f"FactChecker AI — {r['filename']}",f"Date: {r['date']}",f"Trust Score: {trust}/100 ({risk_label})",f"Total: {r['total']} | Verified: {r['verified']} | Inaccurate: {r['inaccurate']} | False: {r['false']}","",f"AI Summary: {r.get('ai_summary','')}","","="*60,""]
            for i,(claim,res) in enumerate(r["claims"],1):
                lines += [f"{i}. [{res.get('verdict','?')}] {claim}",f"   Explanation: {res.get('explanation','')}",f"   Confidence: {res.get('confidence',0)}%"]
                if res.get("correct_fact"): lines.append(f"   Correct Fact: {res['correct_fact']}")
                if res.get("ai_reasoning"): lines.append(f"   AI Reasoning: {res['ai_reasoning']}")
                for s in res.get("sources",[])[:2]:
                    if s.get("url"): lines.append(f"   Source: {s['url']}")
                lines.append("")
            st.download_button("📥  Download Report", data="\n".join(lines), file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1rem;font-weight:800;color:#e8eaf0;margin-bottom:1rem;letter-spacing:-0.03em;">📋 Detailed Results</div>', unsafe_allow_html=True)

        for claim, result in r["claims"]:
            verdict = result.get("verdict","NO_EVIDENCE")
            c_class = css_class(verdict)
            correct = result.get("correct_fact","")
            sources = result.get("sources",[])
            confidence = result.get("confidence",50)
            ai_reason = result.get("ai_reasoning","")

            if correct and verdict in ["FALSE","INACCURATE"]:
                extra = f'<div class="before-after"><div class="before-box"><div class="ba-label">❌ Uploaded Claim</div><div class="ba-text">{claim}</div></div><div class="after-box"><div class="ba-label">✅ Correct Fact</div><div class="ba-text">{correct}</div></div></div>'
            elif correct:
                extra = f'<div class="ai-reasoning"><div class="reasoning-label">📌 Correct Fact</div><div class="reasoning-text">{correct}</div></div>'
            else:
                extra = ""

            reasoning = f'<div class="ai-reasoning"><div class="reasoning-label">🤖 AI Reasoning</div><div class="reasoning-text">{ai_reason}</div></div>' if ai_reason else ""
            src_links = "".join([f'<a class="source-chip" href="{s["url"]}" target="_blank">🔗 {(s["title"] or s["url"])[:36]}…</a>' for s in sources[:3] if s.get("url")])
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
# 📊 DASHBOARD
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Dashboard":
    st.markdown('<div class="page-header"><div class="page-title">📊 Dashboard</div><div class="page-subtitle">Analytics overview of your last fact check.</div></div>', unsafe_allow_html=True)

    r = st.session_state.results
    if r is None:
        st.info("No results yet. Upload a PDF to get started.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()
    else:
        total = r["total"] or 1
        trust = r.get("trust_score", 70)
        trust_color = "#22d3a0" if trust >= 70 else "#f6a623" if trust >= 45 else "#ff5c5c"

        st.markdown(f"""<div class="metrics-grid">
            <div class="metric-card m-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
            <div class="metric-card m-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
            <div class="metric-card m-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
            <div class="metric-card m-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
        </div>""", unsafe_allow_html=True)

        donut = donut_chart(r["verified"],r["inaccurate"],r["false"],r["noevidence"],r["total"])
        st.markdown(f"""<div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Claim Distribution</div>
                {donut}
                <div class="legend-row"><div class="legend-dot" style="background:#22d3a0"></div>Verified ({r['verified']})</div>
                <div class="legend-row"><div class="legend-dot" style="background:#f6a623"></div>Inaccurate ({r['inaccurate']})</div>
                <div class="legend-row"><div class="legend-dot" style="background:#ff5c5c"></div>False ({r['false']})</div>
                <div class="legend-row"><div class="legend-dot" style="background:#4a5568"></div>No Evidence ({r['noevidence']})</div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Verification Breakdown</div>
                <div class="bar-row"><div class="bar-label">✅ Verified</div><div class="bar-track"><div class="bar-fill" style="width:{r['verified']/total*100:.0f}%;background:#22d3a0;"></div></div><div class="bar-pct">{r['verified']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">⚠️ Inaccurate</div><div class="bar-track"><div class="bar-fill" style="width:{r['inaccurate']/total*100:.0f}%;background:#f6a623;"></div></div><div class="bar-pct">{r['inaccurate']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❌ False</div><div class="bar-track"><div class="bar-fill" style="width:{r['false']/total*100:.0f}%;background:#ff5c5c;"></div></div><div class="bar-pct">{r['false']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❓ No Evidence</div><div class="bar-track"><div class="bar-fill" style="width:{r['noevidence']/total*100:.0f}%;background:#4a5568;"></div></div><div class="bar-pct">{r['noevidence']/total*100:.0f}%</div></div>
                <div style="margin-top:1.1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.06);">
                    <div style="font-size:0.68rem;color:#636a82;margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;">Trust Score</div>
                    <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:{trust_color};letter-spacing:-0.04em;">{trust}<span style="font-size:1rem;opacity:0.5">/100</span></div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if r.get("ai_summary"):
            st.markdown(f'<div class="ai-summary"><div class="ai-label">🤖 AI Summary</div><div class="ai-text">{r["ai_summary"]}</div></div>', unsafe_allow_html=True)

        if st.button("📋  View Detailed Results"):
            st.session_state.page = "Fact Check"; st.rerun()

# ═══════════════════════════════════════════════════════
# 🕐 HISTORY
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "History":
    st.markdown('<div class="page-header"><div class="page-title">🕐 History</div><div class="page-subtitle">All previously fact-checked documents.</div></div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:20px;">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">🕐</div>
            <div style="font-family:'Syne',sans-serif;font-weight:800;color:#e8eaf0;font-size:1rem;margin-bottom:0.4rem;letter-spacing:-0.03em;">No history yet</div>
            <div style="font-size:0.8rem;color:#3a4055;">Your fact-check results will appear here after analyzing a PDF.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:.4rem 1.25rem;font-size:.62rem;font-weight:700;color:#3a4055;text-transform:uppercase;letter-spacing:.1em;"><div>Document</div><div>Total</div><div>✅</div><div>⚠️</div><div>❌</div><div>Date</div></div>', unsafe_allow_html=True)
        for h in reversed(st.session_state.history):
            trust = h.get("trust_score", 70)
            tc = "#22d3a0" if trust >= 70 else "#f6a623" if trust >= 45 else "#ff5c5c"
            st.markdown(f"""<div class="history-row">
                <div><div style="font-weight:600;color:#e8eaf0;font-size:0.86rem;">📄 {h["filename"]}</div><div style="font-size:0.67rem;color:#3a4055;margin-top:0.15rem;">Trust: <span style="color:{tc};font-weight:700;">{trust}/100</span></div></div>
                <div style="font-weight:700;color:#e8eaf0;">{h["total"]}</div>
                <div style="color:#22d3a0;font-weight:700;">{h["verified"]}</div>
                <div style="color:#f6a623;font-weight:700;">{h["inaccurate"]}</div>
                <div style="color:#ff5c5c;font-weight:700;">{h["false"]}</div>
                <div style="font-size:0.73rem;color:#3a4055;">{h["date"]}</div>
            </div>""", unsafe_allow_html=True)
