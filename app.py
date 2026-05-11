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
    page_title="FactChecker AI — Truth Verification for Documents",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── LOAD API KEYS ─────────────────────────────────────
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── SESSION STATE ─────────────────────────────────────
for key, default in [
    ("history", []),
    ("results", None),
    ("page", "home"),
    ("uploaded_file", None),
    ("nav_section", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── MASTER CSS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── RESET & TOKENS ─────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    /* Background stack */
    --bg-deep:    #03070f;
    --bg-base:    #060c18;
    --bg-raised:  #0b1525;
    --bg-float:   #101e30;
    --bg-hover:   #152438;

    /* Borders */
    --brd-dim:    #162035;
    --brd-mid:    #1e2f4a;
    --brd-hi:     #27405e;
    --brd-blue:   rgba(59,130,246,0.38);

    /* Text */
    --txt-1:      #eef2ff;
    --txt-2:      #94a3c4;
    --txt-3:      #4d6080;
    --txt-4:      #2a3a55;

    /* Blue system */
    --blue-50:    #eff6ff;
    --blue-400:   #60a5fa;
    --blue-500:   #3b82f6;
    --blue-600:   #2563eb;
    --blue-700:   #1d4ed8;
    --blue-900:   #1e3a8a;
    --blue-glow:  rgba(59,130,246,0.22);
    --blue-mist:  rgba(59,130,246,0.06);
    --blue-haze:  rgba(59,130,246,0.12);

    /* Status */
    --green:      #22c55e;
    --green-bg:   rgba(34,197,94,0.07);
    --green-brd:  rgba(34,197,94,0.22);
    --amber:      #f59e0b;
    --amber-bg:   rgba(245,158,11,0.07);
    --amber-brd:  rgba(245,158,11,0.22);
    --red:        #ef4444;
    --red-bg:     rgba(239,68,68,0.07);
    --red-brd:    rgba(239,68,68,0.22);
    --slate:      #64748b;
    --slate-bg:   rgba(100,116,139,0.07);
    --slate-brd:  rgba(100,116,139,0.22);

    /* Shape */
    --r-xs:  6px;
    --r-sm:  10px;
    --r-md:  14px;
    --r-lg:  20px;
    --r-xl:  28px;

    /* Shadow */
    --shadow-sm: 0 2px 12px rgba(0,0,0,0.35);
    --shadow-md: 0 4px 28px rgba(0,0,0,0.45);
    --shadow-xl: 0 8px 56px rgba(0,0,0,0.55);
    --glow-blue: 0 0 40px rgba(59,130,246,0.18);
    --glow-blue-lg: 0 0 80px rgba(59,130,246,0.14);
}

/* ── GLOBAL ─────────────────────────────────────────── */
html, body, .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg-base) !important;
    color: var(--txt-1) !important;
    font-size: 15px;
    line-height: 1.6;
}

#MainMenu, footer, header, .stDeployButton { visibility: hidden !important; display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

/* ── TOPNAV ─────────────────────────────────────────── */
.topnav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(6,12,24,0.85);
    backdrop-filter: blur(18px) saturate(180%);
    border-bottom: 1px solid var(--brd-dim);
    padding: 0 3rem;
    display: flex; align-items: center; justify-content: space-between;
    height: 64px;
    box-shadow: 0 1px 0 var(--brd-dim), 0 4px 20px rgba(0,0,0,0.3);
}
.nav-brand {
    display: flex; align-items: center; gap: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 700; font-size: 1rem;
    color: var(--txt-1); text-decoration: none;
    cursor: pointer;
}
.nav-logo {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--blue-600), var(--blue-400));
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    box-shadow: 0 0 16px var(--blue-glow);
    flex-shrink: 0;
}
.nav-links {
    display: flex; align-items: center; gap: 0.25rem;
}
.nav-link {
    font-size: 0.84rem; font-weight: 500;
    color: var(--txt-2); padding: 0.45rem 0.9rem;
    border-radius: var(--r-sm);
    cursor: pointer; transition: all 0.16s;
    border: 1px solid transparent;
    text-decoration: none;
}
.nav-link:hover { color: var(--txt-1); background: var(--bg-raised); border-color: var(--brd-dim); }
.nav-cta {
    background: var(--blue-600); color: #fff !important;
    font-size: 0.84rem; font-weight: 600;
    padding: 0.48rem 1.15rem;
    border-radius: var(--r-sm);
    cursor: pointer; transition: all 0.16s;
    text-decoration: none; border: 1px solid transparent;
    box-shadow: 0 4px 16px var(--blue-glow);
}
.nav-cta:hover {
    background: var(--blue-700);
    box-shadow: 0 6px 24px rgba(59,130,246,0.35);
    transform: translateY(-1px);
}

/* ── PAGE SHELL ─────────────────────────────────────── */
.page-shell {
    max-width: 1160px;
    margin: 0 auto;
    padding: 4rem 2.5rem 6rem;
}
.page-shell-wide {
    max-width: 1360px;
    margin: 0 auto;
    padding: 4rem 2.5rem 6rem;
}

/* ── HERO ────────────────────────────────────────────── */
.hero-wrap {
    padding: 6rem 2.5rem 5rem;
    max-width: 1160px;
    margin: 0 auto;
    position: relative;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--blue-mist); border: 1px solid var(--brd-blue);
    border-radius: 100px; padding: 0.35em 1.1em;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.07em;
    text-transform: uppercase; color: var(--blue-400);
    margin-bottom: 2rem;
}
.badge-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--blue-500);
    box-shadow: 0 0 8px var(--blue-500);
    animation: ping 2.4s ease infinite;
}
@keyframes ping {
    0%,100%{ opacity:1; transform:scale(1); }
    50%     { opacity:0.4; transform:scale(0.7); }
}

.hero-headline {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: clamp(3rem, 6vw, 5.2rem);
    font-weight: 400; line-height: 1.06;
    letter-spacing: -0.02em;
    color: var(--txt-1);
    margin-bottom: 1.75rem;
    max-width: 820px;
}
.hero-headline .ital { font-style: italic; color: var(--blue-400); }

.hero-tagline {
    font-size: 1.1rem; font-weight: 300;
    color: var(--txt-2); line-height: 1.8;
    max-width: 580px; margin-bottom: 2.75rem;
}

.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 4rem; }

.btn-primary {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--blue-600); color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600; font-size: 0.92rem;
    padding: 0.82rem 1.9rem;
    border-radius: var(--r-sm); border: none; cursor: pointer;
    box-shadow: 0 4px 20px var(--blue-glow), 0 1px 0 rgba(255,255,255,0.08) inset;
    transition: all 0.18s ease;
    letter-spacing: -0.01em;
    text-decoration: none;
}
.btn-primary:hover {
    background: var(--blue-700);
    box-shadow: 0 8px 32px rgba(59,130,246,0.4);
    transform: translateY(-2px);
}
.btn-primary:active { transform: translateY(0); }

.btn-ghost {
    display: inline-flex; align-items: center; gap: 8px;
    background: transparent; color: var(--txt-2);
    font-family: 'DM Sans', sans-serif;
    font-weight: 500; font-size: 0.9rem;
    padding: 0.82rem 1.6rem;
    border-radius: var(--r-sm); border: 1px solid var(--brd-mid); cursor: pointer;
    transition: all 0.18s ease; text-decoration: none;
}
.btn-ghost:hover {
    border-color: var(--brd-blue);
    color: var(--txt-1);
    background: var(--blue-mist);
}

/* ── HERO STATS STRIP ─────────────────────────────────*/
.hero-stats {
    display: flex; gap: 3rem; flex-wrap: wrap;
    padding-top: 2rem;
    border-top: 1px solid var(--brd-dim);
}
.hero-stat-num {
    font-family: 'DM Sans', sans-serif;
    font-size: 2rem; font-weight: 700; color: var(--txt-1);
    letter-spacing: -0.04em; line-height: 1;
    margin-bottom: 0.25rem;
}
.hero-stat-label { font-size: 0.78rem; color: var(--txt-3); font-weight: 400; }

/* ── SECTION WRAPPER ─────────────────────────────────*/
.section {
    padding: 5.5rem 2.5rem;
    max-width: 1160px; margin: 0 auto;
}
.section-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--blue-500);
    margin-bottom: 0.9rem; display: block;
}
.section-title {
    font-family: 'Instrument Serif', serif;
    font-size: clamp(1.8rem, 3.5vw, 3rem);
    font-weight: 400; line-height: 1.15; letter-spacing: -0.02em;
    color: var(--txt-1); margin-bottom: 1rem; max-width: 580px;
}
.section-sub {
    font-size: 0.95rem; color: var(--txt-2); line-height: 1.75;
    max-width: 520px; font-weight: 300;
}

/* ── DIVIDER ──────────────────────────────────────────*/
.section-divider {
    height: 1px; background: var(--brd-dim);
    max-width: 1160px; margin: 0 auto;
}

/* ── FEATURE CARDS ───────────────────────────────────*/
.features-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;
    margin-top: 3.5rem;
}
.feat-card {
    background: var(--bg-raised);
    border: 1px solid var(--brd-dim);
    border-radius: var(--r-lg); padding: 2rem;
    transition: all 0.22s ease;
    position: relative; overflow: hidden;
}
.feat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent 0%, var(--brd-blue) 50%, transparent 100%);
    opacity: 0; transition: opacity 0.22s;
}
.feat-card:hover { border-color: var(--brd-hi); transform: translateY(-3px); box-shadow: var(--shadow-md), var(--glow-blue); }
.feat-card:hover::before { opacity: 1; }
.feat-icon {
    width: 46px; height: 46px; border-radius: var(--r-sm);
    background: var(--blue-haze); border: 1px solid var(--brd-blue);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem; margin-bottom: 1.25rem;
    box-shadow: 0 0 20px var(--blue-mist);
}
.feat-title {
    font-size: 1rem; font-weight: 600; color: var(--txt-1);
    margin-bottom: 0.5rem; letter-spacing: -0.01em;
}
.feat-desc { font-size: 0.83rem; color: var(--txt-2); line-height: 1.75; font-weight: 300; }

/* ── HOW IT WORKS ─────────────────────────────────────*/
.steps-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
    margin-top: 3.5rem;
}
.step-card {
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-radius: var(--r-md); padding: 1.75rem 1.4rem;
    transition: all 0.22s ease; position: relative;
}
.step-card:hover { border-color: var(--brd-hi); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.step-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem; font-weight: 500; color: var(--blue-500);
    letter-spacing: 0.08em; margin-bottom: 1.1rem;
    display: flex; align-items: center; gap: 8px;
}
.step-num-pill {
    background: var(--blue-haze); border: 1px solid var(--brd-blue);
    border-radius: 100px; padding: 0.18em 0.65em;
    font-size: 0.65rem;
}
.step-icon { font-size: 1.6rem; display: block; margin-bottom: 0.75rem; }
.step-title { font-weight: 600; font-size: 0.92rem; color: var(--txt-1); margin-bottom: 0.4rem; }
.step-desc  { font-size: 0.78rem; color: var(--txt-2); line-height: 1.7; font-weight: 300; }

/* ── ABOUT SECTION ───────────────────────────────────*/
.about-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 4rem;
    margin-top: 3.5rem; align-items: start;
}
.about-body {
    font-size: 0.9rem; color: var(--txt-2); line-height: 1.85; font-weight: 300;
}
.about-body p { margin-bottom: 1.2rem; }
.about-body strong { color: var(--txt-1); font-weight: 600; }
.about-right { display: flex; flex-direction: column; gap: 14px; }
.tech-stack-card {
    background: var(--bg-raised); border: 1px solid var(--brd-mid);
    border-radius: var(--r-md); padding: 1.5rem;
}
.tech-stack-label {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--blue-500); margin-bottom: 1rem;
}
.tech-chips { display: flex; flex-wrap: wrap; gap: 7px; }
.tech-chip {
    background: var(--bg-float); border: 1px solid var(--brd-mid);
    color: var(--txt-2); border-radius: var(--r-sm);
    padding: 0.3em 0.85em; font-size: 0.75rem; font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
}
.problem-card {
    background: var(--amber-bg); border: 1px solid var(--amber-brd);
    border-radius: var(--r-md); padding: 1.3rem 1.5rem;
}
.problem-label { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--amber); margin-bottom: 0.5rem; }
.problem-text  { font-size: 0.82rem; color: var(--txt-2); line-height: 1.7; font-weight: 300; }

/* ── UPLOAD PAGE ──────────────────────────────────────*/
.upload-page-header {
    text-align: center; max-width: 620px;
    margin: 0 auto 3.5rem; padding-top: 1rem;
}
.upload-page-title {
    font-family: 'Instrument Serif', serif;
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 400; color: var(--txt-1);
    letter-spacing: -0.02em; line-height: 1.15;
    margin-bottom: 0.75rem;
}
.upload-page-sub { font-size: 0.92rem; color: var(--txt-2); font-weight: 300; line-height: 1.7; }

.upload-dropzone {
    background: var(--bg-raised);
    border: 2px dashed var(--brd-hi);
    border-radius: var(--r-xl); padding: 5rem 3rem;
    text-align: center; margin-bottom: 1.5rem;
    transition: all 0.22s ease; position: relative; overflow: hidden;
    cursor: pointer;
}
.upload-dropzone::before {
    content: ''; position: absolute;
    top: -80px; right: -80px; width: 280px; height: 280px; border-radius: 50%;
    background: radial-gradient(circle, var(--blue-mist) 0%, transparent 70%);
    pointer-events: none;
}
.upload-dropzone:hover { border-color: var(--blue-500); background: var(--blue-mist); }
.upload-icon-wrap {
    width: 72px; height: 72px; border-radius: var(--r-lg);
    background: var(--blue-haze); border: 1px solid var(--brd-blue);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.85rem; margin: 0 auto 1.5rem;
    box-shadow: 0 0 40px var(--blue-mist);
}
.upload-dz-title {
    font-family: 'Instrument Serif', serif;
    font-size: 1.4rem; font-weight: 400; color: var(--txt-1);
    margin-bottom: 0.5rem;
}
.upload-dz-sub { font-size: 0.82rem; color: var(--txt-3); font-weight: 300; }
.upload-dz-hint {
    margin-top: 1.5rem; display: inline-flex; align-items: center; gap: 6px;
    background: var(--bg-float); border: 1px solid var(--brd-mid);
    border-radius: var(--r-sm); padding: 0.35rem 0.9rem;
    font-size: 0.72rem; color: var(--txt-3);
    font-family: 'JetBrains Mono', monospace;
}

.file-card-ready {
    background: var(--green-bg); border: 1px solid var(--green-brd);
    border-radius: var(--r-md); padding: 1.3rem 1.6rem;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1.5rem;
}
.file-card-name { font-weight: 600; color: var(--txt-1); font-size: 0.92rem; }
.file-card-meta { font-size: 0.73rem; color: var(--txt-3); margin-top: 3px; }

/* ── TRUST SCORE SIDEBAR ──────────────────────────────*/
.trust-display {
    background: var(--bg-raised); border: 1px solid var(--brd-mid);
    border-radius: var(--r-md); padding: 1.75rem 1.5rem;
    text-align: center; position: sticky; top: 84px;
}
.trust-score-num {
    font-family: 'Instrument Serif', serif;
    font-size: 4.5rem; font-weight: 400; line-height: 1;
    letter-spacing: -0.04em; margin: 0.75rem 0 0.25rem;
}
.trust-score-label {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--txt-3); margin-bottom: 0.5rem;
}
.trust-score-sub {
    font-size: 0.75rem; color: var(--txt-3); margin-bottom: 1.25rem;
}
.trust-ring {
    width: 110px; height: 110px; margin: 0 auto 0.5rem;
    position: relative; display: flex; align-items: center; justify-content: center;
}

/* ── METRICS GRID ─────────────────────────────────────*/
.metrics-row {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin-bottom: 2rem;
}
.metric-tile {
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-radius: var(--r-md); padding: 1.4rem;
    box-shadow: var(--shadow-sm);
}
.metric-tile-num {
    font-family: 'DM Sans', sans-serif;
    font-size: 2.5rem; font-weight: 700; line-height: 1;
    letter-spacing: -0.05em; margin-bottom: 0.3rem;
}
.metric-tile-label { font-size: 0.73rem; color: var(--txt-2); }

/* ── AI SUMMARY BOX ───────────────────────────────────*/
.ai-summary-box {
    background: var(--blue-mist); border: 1px solid var(--brd-blue);
    border-left: 3px solid var(--blue-500);
    border-radius: var(--r-md); padding: 1.35rem 1.6rem;
    margin-bottom: 2rem;
}
.ai-summary-label {
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--blue-400); margin-bottom: 0.5rem;
}
.ai-summary-text { font-size: 0.9rem; color: var(--txt-2); line-height: 1.8; font-weight: 300; }

/* ── CLAIM CARDS ──────────────────────────────────────*/
.claim-card {
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-left: 3px solid var(--brd-hi);
    border-radius: var(--r-md); padding: 1.4rem 1.6rem;
    margin-bottom: 0.85rem; transition: all 0.18s; box-shadow: var(--shadow-sm);
}
.claim-card:hover { box-shadow: var(--shadow-md); border-color: var(--brd-hi); }
.claim-card.v-verified    { border-left-color: var(--green); }
.claim-card.v-inaccurate  { border-left-color: var(--amber); }
.claim-card.v-false       { border-left-color: var(--red);   }
.claim-card.v-noevidence  { border-left-color: var(--slate); }

.claim-top {
    display: flex; justify-content: space-between;
    align-items: flex-start; gap: 1rem; margin-bottom: 0.6rem; flex-wrap: wrap;
}
.claim-text { font-size: 0.93rem; font-weight: 500; color: var(--txt-1); line-height: 1.55; flex: 1; min-width: 200px; }
.claim-explanation { font-size: 0.84rem; color: var(--txt-2); line-height: 1.75; font-weight: 300; margin-bottom: 0.6rem; }

.conf-row { display: flex; align-items: center; gap: 0.75rem; margin-top: 0.5rem; }
.conf-track { flex: 1; background: var(--bg-deep); border-radius: 100px; height: 4px; }
.conf-fill  { height: 4px; border-radius: 100px; }
.conf-pct   { font-size: 0.72rem; font-weight: 600; min-width: 32px; }
.conf-tag   { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600; color: var(--txt-3); }

.before-after {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 1rem;
}
.ba-box { border-radius: var(--r-sm); padding: 1rem 1.1rem; }
.ba-before { background: var(--red-bg);   border: 1px solid var(--red-brd); }
.ba-after  { background: var(--green-bg); border: 1px solid var(--green-brd); }
.ba-label  { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 700; margin-bottom: 0.35rem; }
.ba-before .ba-label { color: var(--red); }
.ba-after  .ba-label { color: var(--green); }
.ba-text   { font-size: 0.82rem; color: var(--txt-2); line-height: 1.65; font-weight: 300; }

.ai-reason {
    background: var(--blue-mist); border: 1px solid var(--brd-blue);
    border-radius: var(--r-sm); padding: 0.85rem 1rem; margin-top: 0.75rem;
}
.ai-reason-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 700; color: var(--blue-400); margin-bottom: 0.25rem; }
.ai-reason-text  { font-size: 0.81rem; color: var(--txt-2); line-height: 1.7; font-weight: 300; }

.source-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.75rem; }
.source-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: var(--bg-float); border: 1px solid var(--brd-mid);
    border-radius: var(--r-xs); padding: 0.25rem 0.7rem;
    font-size: 0.72rem; color: var(--blue-400); text-decoration: none;
    transition: all 0.14s;
}
.source-chip:hover { background: var(--blue-haze); border-color: var(--brd-blue); }

/* ── VERDICT BADGE ────────────────────────────────────*/
.vbadge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.67rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase; padding: 0.3em 0.9em;
    border-radius: 100px; white-space: nowrap; border: 1px solid;
}
.vbadge-v { background: var(--green-bg);  color: var(--green);  border-color: var(--green-brd); }
.vbadge-i { background: var(--amber-bg);  color: var(--amber);  border-color: var(--amber-brd); }
.vbadge-f { background: var(--red-bg);    color: var(--red);    border-color: var(--red-brd); }
.vbadge-n { background: var(--slate-bg);  color: var(--slate);  border-color: var(--slate-brd); }

/* ── SUSPICIOUS ───────────────────────────────────────*/
.suspicious-box {
    background: var(--amber-bg); border: 1px solid var(--amber-brd);
    border-radius: var(--r-md); padding: 1.2rem 1.5rem; margin-bottom: 2rem;
}
.suspicious-label { font-size: 0.63rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--amber); margin-bottom: 0.6rem; }
.suspicious-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.susp-chip {
    background: var(--amber-bg); border: 1px solid var(--amber-brd);
    color: var(--amber); border-radius: var(--r-xs); padding: 0.22rem 0.7rem;
    font-size: 0.72rem; font-weight: 500;
}

/* ── PROGRESS STEPPER ─────────────────────────────────*/
.stepper-card {
    background: var(--bg-raised); border: 1px solid var(--brd-mid);
    border-radius: var(--r-lg); padding: 2rem 2rem; margin: 2rem 0;
    box-shadow: var(--shadow-sm);
}
.stepper-title {
    font-family: 'Instrument Serif', serif;
    font-size: 1.4rem; font-weight: 400; color: var(--txt-1);
    margin-bottom: 0.35rem;
}
.stepper-sub { font-size: 0.82rem; color: var(--txt-2); margin-bottom: 1.75rem; font-weight: 300; }
.s-row { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid var(--brd-dim); }
.s-row:last-child { border-bottom: none; padding-bottom: 0; }
.s-orb {
    width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 0.85rem;
}
.s-done    { background: var(--green-bg);  border: 1px solid var(--green-brd); color: var(--green);  }
.s-active  { background: var(--blue-haze); border: 1px solid var(--brd-blue);  color: var(--blue-400); }
.s-pending { background: var(--bg-float);  border: 1px solid var(--brd-dim);   color: var(--txt-3);  }
.s-text-title { font-weight: 500; font-size: 0.88rem; }
.s-text-sub   { font-size: 0.72rem; color: var(--txt-3); margin-top: 2px; font-weight: 300; }

/* ── CHARTS / DASHBOARD ───────────────────────────────*/
.charts-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 2rem; }
.chart-card {
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-radius: var(--r-md); padding: 1.6rem; box-shadow: var(--shadow-sm);
}
.chart-heading { font-weight: 600; color: var(--txt-1); font-size: 0.95rem; margin-bottom: 1.3rem; letter-spacing: -0.01em; }

.bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.65rem; }
.bar-label { font-size: 0.73rem; color: var(--txt-2); min-width: 100px; }
.bar-track { flex: 1; background: var(--bg-deep); border-radius: 100px; height: 6px; }
.bar-fill  { height: 6px; border-radius: 100px; transition: width 0.6s ease; }
.bar-pct   { font-size: 0.73rem; font-weight: 600; color: var(--txt-1); min-width: 32px; text-align: right; }

.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.77rem; color: var(--txt-2); margin-bottom: 0.4rem; }
.legend-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* ── HISTORY ──────────────────────────────────────────*/
.hist-header {
    display: grid; grid-template-columns: 2fr 0.55fr 0.55fr 0.55fr 0.55fr 1fr;
    gap: 1rem; padding: 0.4rem 1.25rem;
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.09em; color: var(--txt-3); margin-bottom: 0.5rem;
}
.hist-row {
    display: grid; grid-template-columns: 2fr 0.55fr 0.55fr 0.55fr 0.55fr 1fr;
    gap: 1rem; padding: 1rem 1.25rem;
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-radius: var(--r-sm); margin-bottom: 8px;
    align-items: center; transition: all 0.18s; box-shadow: var(--shadow-sm);
}
.hist-row:hover { border-color: var(--brd-hi); box-shadow: var(--shadow-md); }
.hist-empty {
    text-align: center; padding: 5rem 2rem;
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-radius: var(--r-xl); box-shadow: var(--shadow-sm);
}
.hist-empty-icon { font-size: 2.75rem; margin-bottom: 0.85rem; display: block; }
.hist-empty-title { font-family: 'Instrument Serif', serif; font-size: 1.4rem; font-weight: 400; color: var(--txt-1); margin-bottom: 0.35rem; }
.hist-empty-sub { font-size: 0.82rem; color: var(--txt-3); font-weight: 300; }

/* ── FOOTER ───────────────────────────────────────────*/
.site-footer {
    border-top: 1px solid var(--brd-dim); padding: 2.5rem 3rem;
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 1rem;
    background: var(--bg-deep);
}
.footer-brand { font-weight: 700; color: var(--txt-1); font-size: 0.9rem; }
.footer-sub   { font-size: 0.73rem; color: var(--txt-3); margin-top: 3px; }
.footer-links { display: flex; gap: 1.5rem; align-items: center; flex-wrap: wrap; }
.footer-link  { font-size: 0.78rem; color: var(--txt-3); text-decoration: none; transition: color 0.15s; }
.footer-link:hover { color: var(--blue-400); }
.footer-tag {
    font-size: 0.71rem; color: var(--txt-3);
    background: var(--bg-raised); border: 1px solid var(--brd-dim);
    border-radius: 100px; padding: 0.25em 0.85em;
}

/* ── NATIVE STREAMLIT OVERRIDES ───────────────────────*/
.stProgress > div > div { background: var(--blue-600) !important; border-radius: 100px !important; }
[data-testid="stFileUploader"] { background: transparent !important; border: none !important; }
div[data-testid="stRadio"] { display: none !important; }
hr { border-color: var(--brd-dim) !important; margin: 2rem 0 !important; }
.stSuccess { background: var(--green-bg) !important; border-color: var(--green-brd) !important; color: var(--green) !important; border-radius: var(--r-sm) !important; }
.stWarning { background: var(--amber-bg) !important; border-color: var(--amber-brd) !important; color: var(--amber) !important; border-radius: var(--r-sm) !important; }
.stInfo    { background: var(--blue-mist) !important; border-color: var(--brd-blue) !important; color: var(--txt-2) !important; border-radius: var(--r-sm) !important; }
.stButton > button {
    background: var(--bg-float) !important; color: var(--txt-2) !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    border: 1px solid var(--brd-mid) !important; border-radius: var(--r-sm) !important;
    font-size: 0.85rem !important; transition: all 0.16s !important;
    box-shadow: var(--shadow-sm) !important; letter-spacing: -0.01em !important;
}
.stButton > button:hover {
    background: var(--blue-haze) !important; border-color: var(--brd-blue) !important;
    color: var(--txt-1) !important; box-shadow: var(--glow-blue) !important;
}
[data-testid="stDownloadButton"] > button {
    background: var(--green-bg) !important; color: var(--green) !important;
    border: 1px solid var(--green-brd) !important; box-shadow: none !important;
}

/* ── SECTION ANCHOR PADDING ───────────────────────────*/
.anchor { padding-top: 64px; margin-top: -64px; }

/* ── RESPONSIVE ───────────────────────────────────────*/
@media (max-width: 900px) {
    .hero-wrap { padding: 4rem 1.5rem 3rem; }
    .hero-headline { font-size: 2.5rem; }
    .features-grid { grid-template-columns: 1fr; }
    .steps-grid { grid-template-columns: repeat(2, 1fr); }
    .metrics-row { grid-template-columns: repeat(2, 1fr); }
    .before-after { grid-template-columns: 1fr; }
    .charts-pair { grid-template-columns: 1fr; }
    .about-grid { grid-template-columns: 1fr; gap: 2rem; }
    .topnav { padding: 0 1.25rem; }
    .section { padding: 3.5rem 1.5rem; }
    .hero-stats { gap: 2rem; }
    .site-footer { flex-direction: column; gap: 0.75rem; padding: 2rem 1.5rem; }
}
</style>
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
    m = {
        "VERIFIED":    ('<span class="vbadge vbadge-v">✓ Verified</span>'),
        "INACCURATE":  ('<span class="vbadge vbadge-i">⚠ Outdated</span>'),
        "FALSE":       ('<span class="vbadge vbadge-f">✕ False</span>'),
        "NO_EVIDENCE": ('<span class="vbadge vbadge-n">? No Evidence</span>'),
    }
    return m.get(verdict, m["NO_EVIDENCE"])

def css_class(verdict):
    return {"VERIFIED":"v-verified","INACCURATE":"v-inaccurate","FALSE":"v-false","NO_EVIDENCE":"v-noevidence"}.get(verdict,"v-noevidence")

def confidence_html(score):
    score = int(score) if score else 50
    if score >= 70:   color, cls = "#22c55e", "#22c55e"
    elif score >= 45: color, cls = "#f59e0b", "#f59e0b"
    else:             color, cls = "#ef4444", "#ef4444"
    return f"""<div class="conf-row">
        <span class="conf-tag">Confidence</span>
        <div class="conf-track"><div class="conf-fill" style="width:{score}%;background:{cls};"></div></div>
        <div class="conf-pct" style="color:{color}">{score}%</div>
    </div>"""

def trust_color(trust):
    if trust >= 70: return "#22c55e"
    if trust >= 45: return "#f59e0b"
    return "#ef4444"

def trust_label(trust):
    if trust >= 70: return "Low Risk"
    if trust >= 45: return "Medium Risk"
    return "High Risk"

def donut_svg(verified, inaccurate, false_count, noev, total):
    if total == 0: return ""
    cx, cy, r, circ = 70, 70, 52, 2*3.14159*52
    segs = [(verified/total,"#22c55e"),(inaccurate/total,"#f59e0b"),(false_count/total,"#ef4444"),(noev/total,"#4d6080")]
    offset, paths = 0, []
    for ratio, color in segs:
        if ratio == 0: continue
        dash = ratio * circ
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="12" stroke-dasharray="{dash:.1f} {circ-dash:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash
    tc = trust_color(compute_trust(verified, inaccurate, false_count, noev, total))
    score = compute_trust(verified, inaccurate, false_count, noev, total)
    return f"""<svg viewBox="0 0 140 140" style="width:100%;max-width:140px;display:block;margin:0 auto 1rem;">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#0b1525" stroke-width="12"/>
        {"".join(paths)}
        <text x="{cx}" y="{cy-5}" text-anchor="middle" fill="{tc}" font-size="22" font-weight="700" font-family="DM Sans,sans-serif">{score}</text>
        <text x="{cx}" y="{cy+11}" text-anchor="middle" fill="#4d6080" font-size="9" font-family="DM Sans,sans-serif">/100</text>
    </svg>"""


# ─── TOPNAV ─────────────────────────────────────────────
def render_nav():
    st.markdown("""
    <div class="topnav">
        <div class="nav-brand">
            <div class="nav-logo">🛡️</div>
            FactChecker AI
        </div>
        <div class="nav-links">
            <span class="nav-link">Features</span>
            <span class="nav-link">How It Works</span>
            <span class="nav-link">About</span>
            <a class="nav-link" href="https://github.com/ishamishra0421-gif/fact-checker" target="_blank">GitHub ↗</a>
        </div>
        <span class="nav-cta">Analyze Document →</span>
    </div>
    """, unsafe_allow_html=True)

    # Real Streamlit nav buttons (hidden-style via columns to keep layout)
    col_home, col_upload, col_check, col_dash, col_hist, col_spacer = st.columns([1,1,1,1,1,3])
    with col_home:
        if st.button("Home", key="rnav_home"):
            st.session_state.page = "home"; st.rerun()
    with col_upload:
        if st.button("Upload", key="rnav_upload"):
            st.session_state.page = "upload"; st.rerun()
    with col_check:
        if st.button("Results", key="rnav_check"):
            st.session_state.page = "check"; st.rerun()
    with col_dash:
        if st.button("Dashboard", key="rnav_dash"):
            st.session_state.page = "dashboard"; st.rerun()
    with col_hist:
        if st.button("History", key="rnav_hist"):
            st.session_state.page = "history"; st.rerun()


# ═══════════════════════════════════════════════════════
# 🏠  HOME — Full Landing Page
# ═══════════════════════════════════════════════════════
if st.session_state.page == "home":
    render_nav()

    # ── HERO ──────────────────────────────────────────
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">
            <div class="badge-dot"></div>
            AI-Powered Truth Verification for Documents
        </div>
        <h1 class="hero-headline">
            Stop misinformation<br>before it <span class="ital">spreads.</span>
        </h1>
        <p class="hero-tagline">
            Upload any PDF. FactChecker AI extracts every factual claim, cross-references live web sources, and delivers a verdict with confidence scores and corrected facts — in under 60 seconds.
        </p>
        <div class="hero-actions">
            <span class="btn-primary" id="hero-cta">📤 Analyze Document — Free</span>
            <span class="btn-ghost">↓ See how it works</span>
        </div>
        <div class="hero-stats">
            <div>
                <div class="hero-stat-num">4-step</div>
                <div class="hero-stat-label">Automated pipeline</div>
            </div>
            <div>
                <div class="hero-stat-num">&lt;60s</div>
                <div class="hero-stat-label">Full verification time</div>
            </div>
            <div>
                <div class="hero-stat-num">4</div>
                <div class="hero-stat-label">Live sources per claim</div>
            </div>
            <div>
                <div class="hero-stat-num">100%</div>
                <div class="hero-stat-label">Automated, no manual review</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_cta1, col_cta2, _ = st.columns([1,1,4])
    with col_cta1:
        if st.button("📤  Analyze Document", key="hero_upload"):
            st.session_state.page = "upload"; st.rerun()
    with col_cta2:
        if st.button("📊  View Results", key="hero_results"):
            st.session_state.page = "check"; st.rerun()

    # ── DIVIDER ──────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── FEATURES ──────────────────────────────────────
    st.markdown("""
    <div class="section" id="features">
        <span class="section-label">Features</span>
        <h2 class="section-title">Everything you need to audit a document</h2>
        <p class="section-sub">A complete verification pipeline built for journalists, researchers, and enterprises who can't afford to publish false information.</p>
        <div class="features-grid">
            <div class="feat-card">
                <div class="feat-icon">🎯</div>
                <div class="feat-title">Claim Detection</div>
                <div class="feat-desc">Automatically identifies every verifiable statement in your document — statistics, percentages, market figures, user counts, dates, and technical specifications. No manual tagging required.</div>
            </div>
            <div class="feat-card">
                <div class="feat-icon">🌐</div>
                <div class="feat-title">Live Web Validation</div>
                <div class="feat-desc">Every extracted claim is matched against four live web sources in real time via Tavily search. No stale cached databases — only current, trusted evidence from across the internet.</div>
            </div>
            <div class="feat-card">
                <div class="feat-icon">🤖</div>
                <div class="feat-title">AI Fact Analysis</div>
                <div class="feat-desc">LLaMA 3.3 70B cross-references web evidence with each claim and returns a structured verdict with a 0–100 confidence score, detailed reasoning, and corrected facts where needed.</div>
            </div>
            <div class="feat-card">
                <div class="feat-icon">📥</div>
                <div class="feat-title">Verification Reports</div>
                <div class="feat-desc">Download a full structured report containing every verdict, corrected fact, AI reasoning, source citations, a document trust score, and marketing language flags — ready to share.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DIVIDER ──────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── HOW IT WORKS ──────────────────────────────────
    st.markdown("""
    <div class="section" id="how-it-works">
        <span class="section-label">How It Works</span>
        <h2 class="section-title">Four steps from document to verified truth</h2>
        <p class="section-sub">An automated pipeline that handles the entire fact-checking workflow — no manual effort needed.</p>
        <div class="steps-grid">
            <div class="step-card">
                <div class="step-number"><span class="step-num-pill">01</span></div>
                <span class="step-icon">📤</span>
                <div class="step-title">Upload Your PDF</div>
                <div class="step-desc">Drop any report, article, whitepaper, or marketing deck. Supports files up to 50 MB. Text is extracted automatically.</div>
            </div>
            <div class="step-card">
                <div class="step-number"><span class="step-num-pill">02</span></div>
                <span class="step-icon">🧠</span>
                <div class="step-title">AI Extracts Claims</div>
                <div class="step-desc">LLaMA 3.3 70B reads the document and identifies every verifiable factual statement — stats, figures, technical claims.</div>
            </div>
            <div class="step-card">
                <div class="step-number"><span class="step-num-pill">03</span></div>
                <span class="step-icon">🌐</span>
                <div class="step-title">Live Web Search</div>
                <div class="step-desc">Each claim is searched against real-time web sources via Tavily — four sources per claim, no cached data, always current.</div>
            </div>
            <div class="step-card">
                <div class="step-number"><span class="step-num-pill">04</span></div>
                <span class="step-icon">📊</span>
                <div class="step-title">Report Generated</div>
                <div class="step-desc">Receive a full report: ✅ Verified, ⚠️ Outdated, ❌ False — with confidence scores, corrected facts, and source links.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DIVIDER ──────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── ABOUT ────────────────────────────────────────
    st.markdown("""
    <div class="section" id="about">
        <span class="section-label">About the Project</span>
        <div class="about-grid">
            <div>
                <h2 class="section-title">Built to fight misinformation at the source</h2>
                <div class="about-body">
                    <p>PDFs are one of the primary ways misinformation spreads in professional contexts — reports, whitepapers, marketing decks, and articles circulate without scrutiny. Traditional fact-checking is slow, expensive, and manual.</p>
                    <p><strong>FactChecker AI automates the entire pipeline.</strong> Upload a document, and the system extracts every falsifiable claim, runs a live web search for each one, and uses a large language model to reason about whether the claim is verified, outdated, or false — returning corrected facts and source links in under 60 seconds.</p>
                    <p>Built for journalists, researchers, compliance teams, and anyone who needs to trust the documents they publish or distribute.</p>
                </div>
            </div>
            <div class="about-right">
                <div class="problem-card">
                    <div class="problem-label">⚠️ The Problem</div>
                    <div class="problem-text">False statistics and outdated data in PDFs are impossible to catch manually at scale. A single misleading figure in a distributed report can cause real-world harm — to businesses, policy decisions, and public trust.</div>
                </div>
                <div class="tech-stack-card">
                    <div class="tech-stack-label">Tech Stack</div>
                    <div class="tech-chips">
                        <span class="tech-chip">LLaMA 3.3 70B</span>
                        <span class="tech-chip">Groq</span>
                        <span class="tech-chip">Tavily</span>
                        <span class="tech-chip">pdfplumber</span>
                        <span class="tech-chip">Streamlit</span>
                        <span class="tech-chip">Python 3.11</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FOOTER ───────────────────────────────────────
    st.markdown("""
    <div class="site-footer">
        <div>
            <div class="footer-brand">🛡️ FactChecker AI</div>
            <div class="footer-sub">AI-Powered Truth Verification for Documents</div>
        </div>
        <div class="footer-links">
            <a class="footer-link" href="https://github.com/ishamishra0421-gif/fact-checker" target="_blank">⬡ GitHub</a>
            <a class="footer-link" href="https://streamlit.io/cloud" target="_blank">🚀 Streamlit Cloud</a>
            <a class="footer-link" href="https://groq.com" target="_blank">⚡ Groq</a>
            <a class="footer-link" href="https://tavily.com" target="_blank">🌐 Tavily</a>
            <span class="footer-tag">v1.0.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# 📤  UPLOAD PDF
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "upload":
    render_nav()
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-page-header">
        <h1 class="upload-page-title">Analyze your document</h1>
        <p class="upload-page-sub">Upload any PDF report, article, or whitepaper. FactChecker AI will extract every factual claim and verify it against live web sources.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF (Max 50MB)", type="pdf", label_visibility="collapsed")

    if not uploaded_file:
        st.markdown("""
        <div class="upload-dropzone">
            <div class="upload-icon-wrap">☁️</div>
            <div class="upload-dz-title">Drop your PDF here</div>
            <div class="upload-dz-sub">or use the file picker · PDF only · up to 50 MB</div>
            <div class="upload-dz-hint">🔒 Processed in memory — nothing is stored or shared</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:600;color:var(--txt-1);font-size:0.95rem;margin-bottom:1rem;">Sample documents to try</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="feat-card" style="cursor:default;">
                <div class="feat-icon">📋</div>
                <div class="feat-title">Demo PDF — Real Facts</div>
                <div class="feat-desc">Contains accurate, verifiable statistics to demonstrate what a clean verification report looks like.</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="feat-card" style="cursor:default;">
                <div class="feat-icon">⚠️</div>
                <div class="feat-title">Trap PDF — False Data</div>
                <div class="feat-desc">Contains intentionally outdated and false statistics to test the full detection and correction pipeline.</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("🔒 Your PDF is processed in memory only. No data is stored, uploaded to any server, or shared with third parties.")

    else:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.results = None
        file_size = len(uploaded_file.getvalue()) / 1024
        st.success(f"✅  **{uploaded_file.name}** is ready to analyze.")
        st.markdown(f"""
        <div class="file-card-ready">
            <div>
                <div class="file-card-name">📄 {uploaded_file.name}</div>
                <div class="file-card-meta">{file_size:.1f} KB &nbsp;·&nbsp; PDF Document &nbsp;·&nbsp; Ready for analysis</div>
            </div>
            <span class="vbadge vbadge-v">Ready</span>
        </div>
        """, unsafe_allow_html=True)

        col_go, col_back, _ = st.columns([1,1,4])
        with col_go:
            if st.button("🚀  Start Fact Check →", key="start_check"):
                st.session_state.page = "check"; st.rerun()
        with col_back:
            if st.button("← Upload Different File", key="back_upload"):
                st.session_state.uploaded_file = None; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# ✅  FACT CHECK (Processing + Results)
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "check":
    render_nav()
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)

    uploaded_file = st.session_state.get("uploaded_file")

    # ── No file uploaded ──────────────────────────────
    if uploaded_file is None:
        st.markdown("""
        <div class="hist-empty">
            <span class="hist-empty-icon">📄</span>
            <div class="hist-empty-title">No document uploaded</div>
            <div class="hist-empty-sub">Upload a PDF first to run the fact-checking pipeline.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Go to Upload"):
            st.session_state.page = "upload"; st.rerun()

    # ── Processing ────────────────────────────────────
    elif st.session_state.results is None:
        st.markdown("""
        <div style="margin-bottom:2rem;">
            <h1 style="font-family:'Instrument Serif',serif;font-size:2.2rem;font-weight:400;color:var(--txt-1);letter-spacing:-0.02em;margin-bottom:0.35rem;">Verifying your document…</h1>
            <p style="font-size:0.9rem;color:var(--txt-2);font-weight:300;">Extracting claims and cross-referencing with live web sources. This usually takes under 60 seconds.</p>
        </div>
        """, unsafe_allow_html=True)

        stepper_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_msg   = st.empty()

        STEPS = [
            ("📄","Reading PDF","Extracting text from all pages"),
            ("🧠","Extracting Claims","AI scanning for verifiable facts"),
            ("🌐","Searching the Web","Live search · 4 sources per claim"),
            ("🔍","Verifying Facts","Cross-referencing with AI analysis"),
            ("📊","Generating Report","Compiling your verification report"),
        ]

        def render_stepper(active):
            html = '<div class="stepper-card"><div class="stepper-title">Verification Pipeline</div><div class="stepper-sub">Processing your document step by step</div>'
            for i,(icon,title,sub) in enumerate(STEPS):
                if i < active:    state, show = "s-done",    "✓"
                elif i == active: state, show = "s-active",  icon
                else:             state, show = "s-pending",  icon
                tc = "var(--txt-1)" if state != "s-pending" else "var(--txt-3)"
                html += f'<div class="s-row"><div class="s-orb {state}">{show}</div><div><div class="s-text-title" style="color:{tc}">{title}</div><div class="s-text-sub">{sub}</div></div></div>'
            stepper_placeholder.markdown(html + "</div>", unsafe_allow_html=True)

        render_stepper(0)
        try:
            text = extract_text(uploaded_file)
            suspicious = find_suspicious(text)
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
            status_msg.markdown(
                f'<div style="font-size:0.79rem;color:var(--txt-2);padding:0.3rem 0;">'
                f'Verifying claim <b style="color:var(--blue-400)">{i+1}</b> of <b>{len(claims)}</b> '
                f'— <span style="font-style:italic;color:var(--txt-3)">{claim[:72]}…</span></div>',
                unsafe_allow_html=True
            )
            try:
                result = verify_claim(claim)
            except:
                result = {"verdict":"NO_EVIDENCE","explanation":"Verification service unavailable.","correct_fact":"","ai_reasoning":"","confidence":0,"sources":[]}
            results_list.append((claim, result))
            v = result.get("verdict","NO_EVIDENCE")
            if v == "VERIFIED":    verified_count += 1
            elif v == "INACCURATE": inaccurate_count += 1
            elif v == "FALSE":      false_count += 1
            else:                   noev_count += 1
            progress_bar.progress((i+1)/len(claims))

        render_stepper(4)
        status_msg.empty()

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
            "ai_summary": ai_summary, "suspicious": suspicious,
        }
        st.session_state.history.append({**st.session_state.results, "claims": None})
        st.rerun()

    # ── Results ───────────────────────────────────────
    else:
        r  = st.session_state.results
        tc = trust_color(r["trust_score"])
        tl = trust_label(r["trust_score"])

        st.markdown(f"""
        <div style="margin-bottom:2.25rem;">
            <h1 style="font-family:'Instrument Serif',serif;font-size:2.4rem;font-weight:400;color:var(--txt-1);letter-spacing:-0.025em;margin-bottom:0.3rem;">Verification complete ✓</h1>
            <p style="font-size:0.85rem;color:var(--txt-3);font-weight:300;">📄 {r['filename']} &nbsp;·&nbsp; {r['date']}</p>
        </div>
        """, unsafe_allow_html=True)

        # AI Summary
        st.markdown(f'<div class="ai-summary-box"><div class="ai-summary-label">🤖 AI Summary</div><div class="ai-summary-text">{r.get("ai_summary","")}</div></div>', unsafe_allow_html=True)

        # Metrics + Trust
        col_metrics, col_trust = st.columns([3,1])
        with col_metrics:
            st.markdown(f"""<div class="metrics-row">
                <div class="metric-tile"><div class="metric-tile-num" style="color:var(--txt-1)">{r['total']}</div><div class="metric-tile-label">Total Claims</div></div>
                <div class="metric-tile"><div class="metric-tile-num" style="color:var(--green)">{r['verified']}</div><div class="metric-tile-label">✅ Verified</div></div>
                <div class="metric-tile"><div class="metric-tile-num" style="color:var(--amber)">{r['inaccurate']}</div><div class="metric-tile-label">⚠️ Outdated</div></div>
                <div class="metric-tile"><div class="metric-tile-num" style="color:var(--red)">{r['false']}</div><div class="metric-tile-label">❌ False</div></div>
            </div>""", unsafe_allow_html=True)
        with col_trust:
            st.markdown(f"""<div class="trust-display">
                <div class="trust-score-label">Trust Score</div>
                {donut_svg(r['verified'],r['inaccurate'],r['false'],r['noevidence'],r['total'])}
                <div class="trust-score-num" style="color:{tc}">{r['trust_score']}</div>
                <div class="trust-score-sub">/100 &nbsp;·&nbsp; <span style="color:{tc}">{tl}</span></div>
            </div>""", unsafe_allow_html=True)

        # Suspicious language
        if r.get("suspicious"):
            chips = "".join([f'<span class="susp-chip">"{p}"</span>' for p in r["suspicious"]])
            st.markdown(f'<div class="suspicious-box"><div class="suspicious-label">🚨 Suspicious Marketing Language</div><div class="suspicious-chips">{chips}</div></div>', unsafe_allow_html=True)

        # Action buttons
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊  View Dashboard"):
                st.session_state.page = "dashboard"; st.rerun()
        with c2:
            if st.button("🔄  Analyze Another PDF"):
                st.session_state.results = None; st.session_state.uploaded_file = None
                st.session_state.page = "upload"; st.rerun()
        with c3:
            lines = [f"FactChecker AI — {r['filename']}",f"Date: {r['date']}",f"Trust Score: {r['trust_score']}/100 ({tl})",
                     f"Total: {r['total']} | Verified: {r['verified']} | Outdated: {r['inaccurate']} | False: {r['false']}","",
                     f"AI Summary: {r.get('ai_summary','')}","","="*60,""]
            for i,(claim,res) in enumerate(r["claims"],1):
                lines += [f"{i}. [{res.get('verdict','?')}] {claim}",f"   Explanation: {res.get('explanation','')}",f"   Confidence: {res.get('confidence',0)}%"]
                if res.get("correct_fact"):  lines.append(f"   Correct Fact: {res['correct_fact']}")
                if res.get("ai_reasoning"):  lines.append(f"   AI Reasoning: {res['ai_reasoning']}")
                for s in res.get("sources",[])[:2]:
                    if s.get("url"): lines.append(f"   Source: {s['url']}")
                lines.append("")
            st.download_button("📥  Download Report", data="\n".join(lines),
                               file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")

        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:600;font-size:1rem;color:var(--txt-1);margin-bottom:1.25rem;letter-spacing:-0.01em;">Detailed Results</div>', unsafe_allow_html=True)

        for claim, result in r["claims"]:
            verdict   = result.get("verdict","NO_EVIDENCE")
            c_class   = css_class(verdict)
            correct   = result.get("correct_fact","")
            sources   = result.get("sources",[])
            conf      = result.get("confidence",50)
            ai_reason = result.get("ai_reasoning","")

            if correct and verdict in ["FALSE","INACCURATE"]:
                extra = f'<div class="before-after"><div class="ba-box ba-before"><div class="ba-label">✕ Original Claim</div><div class="ba-text">{claim}</div></div><div class="ba-box ba-after"><div class="ba-label">✓ Correct Fact</div><div class="ba-text">{correct}</div></div></div>'
            elif correct:
                extra = f'<div class="ai-reason"><div class="ai-reason-label">📌 Note</div><div class="ai-reason-text">{correct}</div></div>'
            else:
                extra = ""

            reasoning = f'<div class="ai-reason"><div class="ai-reason-label">🤖 AI Reasoning</div><div class="ai-reason-text">{ai_reason}</div></div>' if ai_reason else ""
            src_html  = "".join([f'<a class="source-chip" href="{s["url"]}" target="_blank">🔗 {(s["title"] or s["url"])[:36]}…</a>' for s in sources[:3] if s.get("url")])
            sources_html = f'<div class="source-chips">{src_html}</div>' if src_html else ""

            st.markdown(f"""<div class="claim-card {c_class}">
                <div class="claim-top">
                    <div class="claim-text">{claim}</div>
                    <div>{verdict_badge(verdict)}</div>
                </div>
                <div class="claim-explanation">{result.get('explanation','')}</div>
                {confidence_html(conf)}
                {extra}{reasoning}{sources_html}
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# 📊  DASHBOARD
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "dashboard":
    render_nav()
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:2.5rem;">
        <h1 style="font-family:'Instrument Serif',serif;font-size:2.4rem;font-weight:400;color:var(--txt-1);letter-spacing:-0.025em;margin-bottom:0.3rem;">Dashboard</h1>
        <p style="font-size:0.88rem;color:var(--txt-3);font-weight:300;">Analytics overview of your last verification session.</p>
    </div>
    """, unsafe_allow_html=True)

    r = st.session_state.results
    if r is None:
        st.markdown("""
        <div class="hist-empty">
            <span class="hist-empty-icon">📊</span>
            <div class="hist-empty-title">No analysis yet</div>
            <div class="hist-empty-sub">Upload and verify a document to see analytics here.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Analyze a Document"):
            st.session_state.page = "upload"; st.rerun()
    else:
        total = r["total"] or 1
        trust = r["trust_score"]
        tc    = trust_color(trust)

        st.markdown(f"""<div class="metrics-row">
            <div class="metric-tile"><div class="metric-tile-num" style="color:var(--txt-1)">{r['total']}</div><div class="metric-tile-label">Total Claims</div></div>
            <div class="metric-tile"><div class="metric-tile-num" style="color:var(--green)">{r['verified']}</div><div class="metric-tile-label">✅ Verified</div></div>
            <div class="metric-tile"><div class="metric-tile-num" style="color:var(--amber)">{r['inaccurate']}</div><div class="metric-tile-label">⚠️ Outdated</div></div>
            <div class="metric-tile"><div class="metric-tile-num" style="color:var(--red)">{r['false']}</div><div class="metric-tile-label">❌ False</div></div>
        </div>""", unsafe_allow_html=True)

        donut = donut_svg(r["verified"],r["inaccurate"],r["false"],r["noevidence"],r["total"])
        st.markdown(f"""<div class="charts-pair">
            <div class="chart-card">
                <div class="chart-heading">Claim Distribution</div>
                {donut}
                <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div>Verified ({r['verified']})</div>
                <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Outdated ({r['inaccurate']})</div>
                <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>False ({r['false']})</div>
                <div class="legend-item"><div class="legend-dot" style="background:#4d6080"></div>No Evidence ({r['noevidence']})</div>
            </div>
            <div class="chart-card">
                <div class="chart-heading">Verification Breakdown</div>
                <div class="bar-row"><div class="bar-label">✅ Verified</div><div class="bar-track"><div class="bar-fill" style="width:{r['verified']/total*100:.0f}%;background:#22c55e;"></div></div><div class="bar-pct">{r['verified']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">⚠️ Outdated</div><div class="bar-track"><div class="bar-fill" style="width:{r['inaccurate']/total*100:.0f}%;background:#f59e0b;"></div></div><div class="bar-pct">{r['inaccurate']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❌ False</div><div class="bar-track"><div class="bar-fill" style="width:{r['false']/total*100:.0f}%;background:#ef4444;"></div></div><div class="bar-pct">{r['false']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❓ No Evidence</div><div class="bar-track"><div class="bar-fill" style="width:{r['noevidence']/total*100:.0f}%;background:#4d6080;"></div></div><div class="bar-pct">{r['noevidence']/total*100:.0f}%</div></div>
                <div style="margin-top:1.5rem;padding-top:1.3rem;border-top:1px solid var(--brd-dim);">
                    <div style="font-size:0.62rem;color:var(--txt-3);margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;">Document Trust Score</div>
                    <div style="font-family:'Instrument Serif',serif;font-size:3rem;font-weight:400;color:{tc};letter-spacing:-0.04em;line-height:1;">{trust}<span style="font-size:1.1rem;opacity:0.4">/100</span></div>
                    <div style="font-size:0.75rem;color:{tc};margin-top:4px;font-weight:500;">{trust_label(trust)}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if r.get("ai_summary"):
            st.markdown(f'<div class="ai-summary-box"><div class="ai-summary-label">🤖 AI Summary</div><div class="ai-summary-text">{r["ai_summary"]}</div></div>', unsafe_allow_html=True)

        if st.button("📋  View Full Results →"):
            st.session_state.page = "check"; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# 🕐  HISTORY
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "history":
    render_nav()
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:2.5rem;">
        <h1 style="font-family:'Instrument Serif',serif;font-size:2.4rem;font-weight:400;color:var(--txt-1);letter-spacing:-0.025em;margin-bottom:0.3rem;">History</h1>
        <p style="font-size:0.88rem;color:var(--txt-3);font-weight:300;">All documents verified in this session.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div class="hist-empty">
            <span class="hist-empty-icon">🕐</span>
            <div class="hist-empty-title">No history yet</div>
            <div class="hist-empty-sub">Verified documents will appear here after you run an analysis.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="hist-header">
            <div>Document</div>
            <div>Total</div><div>✅</div><div>⚠️</div><div>❌</div>
            <div>Date</div>
        </div>
        """, unsafe_allow_html=True)
        for h in reversed(st.session_state.history):
            tc = trust_color(h.get("trust_score",70))
            st.markdown(f"""<div class="hist-row">
                <div>
                    <div style="font-weight:600;color:var(--txt-1);font-size:0.88rem;">📄 {h["filename"]}</div>
                    <div style="font-size:0.7rem;color:var(--txt-3);margin-top:3px;">Trust: <span style="color:{tc};font-weight:700;">{h.get('trust_score',70)}/100</span></div>
                </div>
                <div style="font-weight:700;color:var(--txt-1);">{h["total"]}</div>
                <div style="color:var(--green);font-weight:700;">{h["verified"]}</div>
                <div style="color:var(--amber);font-weight:700;">{h["inaccurate"]}</div>
                <div style="color:var(--red);font-weight:700;">{h["false"]}</div>
                <div style="font-size:0.74rem;color:var(--txt-3);">{h["date"]}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
