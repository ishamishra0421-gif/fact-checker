import streamlit as st
import pdfplumber
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
import time
from groq import Groq
from datetime import datetime

# ─── PAGE CONFIG ──────────────────────────────────────
st.set_page_config(
    page_title="FactCheck",
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
    ("page", "Home"),
    ("uploaded_file", None),
    ("theme", "dark"),
    ("auth_page", None),   # "login" | "signup" | None
    ("user", None),        # {"name": ..., "email": ...}
    ("users_db", {}),      # email -> {name, password}
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── THEME VARS ────────────────────────────────────────
DARK = {
    "bg": "#0a0e1a",
    "sidebar_bg": "#0d1224",
    "sidebar_border": "#1e2a45",
    "card_bg": "rgba(255,255,255,0.04)",
    "card_border": "rgba(255,255,255,0.08)",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "hero_bg": "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)",
    "hero_border": "rgba(99,102,241,0.3)",
    "nav_bg": "#0d1224",
    "nav_border": "#1e2a45",
    "input_bg": "rgba(255,255,255,0.06)",
    "input_border": "rgba(255,255,255,0.12)",
}
LIGHT = {
    "bg": "#f8fafc",
    "sidebar_bg": "#ffffff",
    "sidebar_border": "#e2e8f0",
    "card_bg": "rgba(0,0,0,0.03)",
    "card_border": "rgba(0,0,0,0.08)",
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "hero_bg": "linear-gradient(135deg, #ede9fe 0%, #ddd6fe 50%, #ede9fe 100%)",
    "hero_border": "rgba(99,102,241,0.25)",
    "nav_bg": "#ffffff",
    "nav_border": "#e2e8f0",
    "input_bg": "rgba(0,0,0,0.04)",
    "input_border": "rgba(0,0,0,0.12)",
}

T = DARK if st.session_state.theme == "dark" else LIGHT

# ─── CSS ──────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Bricolage+Grotesque:wght@400;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: {T['bg']} !important;
    color: {T['text_primary']} !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

.block-container {{
    padding: 0 2rem 3rem 2rem !important;
    max-width: 1080px !important;
}}

@media (max-width: 768px) {{
    .block-container {{ padding: 0 0.75rem 2rem 0.75rem !important; }}
    .metrics-grid {{ grid-template-columns: repeat(2, 1fr) !important; }}
    .steps-row {{ grid-template-columns: repeat(2, 1fr) !important; }}
    .features-grid {{ grid-template-columns: 1fr !important; }}
    .charts-row {{ grid-template-columns: 1fr !important; }}
    .before-after {{ grid-template-columns: 1fr !important; }}
    .sample-grid {{ grid-template-columns: 1fr !important; }}
    .nav-links {{ gap: 0.5rem !important; }}
}}

/* ── SIDEBAR hidden by default ── */
section[data-testid="stSidebar"] {{ display: none !important; }}

/* ── TOP NAVBAR ── */
.top-navbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    height: 62px;
    background: {T['nav_bg']};
    border-bottom: 1px solid {T['nav_border']};
    position: sticky;
    top: 0;
    z-index: 999;
    margin-left: -2rem;
    margin-right: -2rem;
    margin-bottom: 2rem;
    width: calc(100% + 4rem);
}}
.nav-brand {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    cursor: pointer;
    text-decoration: none;
}}
.nav-logo-box {{
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 800; color: white;
    letter-spacing: -0.5px;
}}
.nav-brand-name {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.05rem; font-weight: 800;
    color: {T['text_primary']};
}}
.nav-links {{
    display: flex; align-items: center; gap: 0.3rem;
}}
.nav-link {{
    padding: 0.4rem 0.85rem;
    border-radius: 8px;
    font-size: 0.83rem; font-weight: 600;
    color: {T['text_secondary']};
    cursor: pointer;
    transition: all 0.15s;
    border: none; background: transparent;
}}
.nav-link:hover {{
    background: {'rgba(99,102,241,0.1)' if st.session_state.theme == 'dark' else 'rgba(99,102,241,0.08)'};
    color: #818cf8;
}}
.nav-link.active {{
    color: #6366f1;
    background: rgba(99,102,241,0.12);
}}
.nav-btn-login {{
    padding: 0.4rem 1rem;
    border-radius: 8px;
    font-size: 0.82rem; font-weight: 700;
    color: {T['text_primary']};
    cursor: pointer;
    border: 1px solid {T['card_border']};
    background: {T['card_bg']};
    transition: all 0.15s;
}}
.nav-btn-login:hover {{
    border-color: rgba(99,102,241,0.4);
    color: #818cf8;
}}
.nav-btn-signup {{
    padding: 0.4rem 1rem;
    border-radius: 8px;
    font-size: 0.82rem; font-weight: 700;
    color: white;
    cursor: pointer;
    border: none;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    transition: all 0.15s;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3);
}}
.nav-btn-signup:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99,102,241,0.4);
}}
.theme-btn {{
    width: 34px; height: 34px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    cursor: pointer;
    border: 1px solid {T['card_border']};
    background: {T['card_bg']};
    color: {T['text_secondary']};
    transition: all 0.15s;
    margin-left: 0.25rem;
}}
.theme-btn:hover {{
    border-color: rgba(99,102,241,0.4);
}}
.user-chip {{
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.3rem 0.75rem;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 100px;
    font-size: 0.78rem; font-weight: 600;
    color: #818cf8;
}}

/* ── BUTTONS ── */
.stButton > button {{
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    font-size: 0.88rem !important; width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.25) !important;
}}
.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}}

/* ── CARDS ── */
.glass-card {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
}}

/* ── METRICS ── */
.metrics-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}}
.metric-card {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 1.25rem; text-align: center;
}}
.metric-num {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 2.2rem; font-weight: 800; line-height: 1;
}}
.metric-label {{ font-size: 0.73rem; color: {T['text_muted']}; margin-top: 0.3rem; font-weight: 500; }}
.metric-total .metric-num {{ color: {T['text_primary']}; }}
.metric-verified .metric-num {{ color: #10b981; }}
.metric-inaccurate .metric-num {{ color: #f59e0b; }}
.metric-false .metric-num {{ color: #ef4444; }}

/* ── PAGE HEADER ── */
.page-header {{ margin-bottom: 1.75rem; }}
.page-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.6rem; font-weight: 800; color: {T['text_primary']}; margin-bottom: 0.25rem;
}}
.page-subtitle {{ color: {T['text_muted']}; font-size: 0.86rem; }}

/* ── HOME HERO (no box) ── */
.home-hero {{
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
}}
.home-hero-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 3rem; font-weight: 800; line-height: 1.1;
    color: {T['text_primary']}; margin-bottom: 0.85rem;
}}
.home-hero-title span {{
    background: linear-gradient(135deg, #6366f1, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.home-hero-desc {{
    font-size: 1rem; color: {T['text_secondary']};
    max-width: 520px; margin: 0 auto 2rem auto; line-height: 1.75;
}}
.home-upload-wrap {{
    display: flex; justify-content: center; margin-bottom: 3rem;
}}

/* ── STEPS ── */
.steps-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }}
.step-card {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 1.4rem 1rem; text-align: center; transition: border-color 0.2s;
}}
.step-card:hover {{ border-color: rgba(99,102,241,0.4); }}
.step-num {{
    font-size: 0.62rem; font-weight: 800; letter-spacing: 0.1em;
    color: #818cf8; background: rgba(99,102,241,0.15);
    border-radius: 100px; display: inline-block; padding: 0.2em 0.75em; margin-bottom: 0.75rem;
}}
.step-icon {{ font-size: 1.7rem; margin-bottom: 0.5rem; }}
.step-title {{ font-weight: 700; color: {T['text_primary']}; font-size: 0.87rem; margin-bottom: 0.3rem; }}
.step-desc {{ font-size: 0.77rem; color: {T['text_muted']}; line-height: 1.6; }}

/* ── SECTION TITLE ── */
.section-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.15rem; font-weight: 800; color: {T['text_primary']}; margin-bottom: 1rem;
}}

/* ── FEATURES GRID ── */
.features-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.25rem 0; }}
.feature-card {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 1.4rem; transition: border-color 0.2s;
}}
.feature-card:hover {{ border-color: rgba(99,102,241,0.3); }}
.feature-icon {{ font-size: 1.7rem; margin-bottom: 0.65rem; }}
.feature-title {{ font-weight: 700; color: {T['text_primary']}; font-size: 0.88rem; margin-bottom: 0.35rem; }}
.feature-desc {{ font-size: 0.78rem; color: {T['text_muted']}; line-height: 1.65; }}

/* ── ABOUT SECTION ── */
.about-section {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 20px;
    padding: 2.5rem;
    margin: 2rem 0;
    text-align: center;
}}
.about-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.6rem; font-weight: 800; color: {T['text_primary']}; margin-bottom: 0.75rem;
}}
.about-desc {{
    font-size: 0.93rem; color: {T['text_secondary']};
    max-width: 600px; margin: 0 auto 1.5rem auto; line-height: 1.8;
}}
.about-tags {{
    display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-bottom: 1.5rem;
}}
.about-tag {{
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25);
    color: #818cf8; border-radius: 100px;
    font-size: 0.75rem; font-weight: 600; padding: 0.25em 0.9em;
}}
.github-btn {{
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: {'#1a1f35' if st.session_state.theme == 'dark' else '#f1f5f9'};
    border: 1px solid {T['card_border']};
    color: {T['text_primary']};
    border-radius: 10px; padding: 0.6rem 1.4rem;
    font-size: 0.85rem; font-weight: 700;
    text-decoration: none; transition: all 0.2s;
}}
.github-btn:hover {{
    border-color: rgba(99,102,241,0.5);
    color: #818cf8;
    transform: translateY(-1px);
}}

/* ── AUTH FORM ── */
.auth-container {{
    max-width: 420px; margin: 2rem auto;
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 20px; padding: 2.5rem;
}}
.auth-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.5rem; font-weight: 800; color: {T['text_primary']};
    text-align: center; margin-bottom: 0.5rem;
}}
.auth-sub {{
    text-align: center; font-size: 0.83rem; color: {T['text_muted']};
    margin-bottom: 1.75rem;
}}
.auth-switch {{
    text-align: center; font-size: 0.82rem; color: {T['text_muted']};
    margin-top: 1.25rem;
}}
.auth-switch span {{
    color: #818cf8; cursor: pointer; font-weight: 600; text-decoration: underline;
}}

/* ── PROCESSING STEPPER ── */
.process-stepper {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 16px; padding: 1.5rem; margin: 1rem 0;
}}
.process-step {{
    display: flex; align-items: center; gap: 1rem;
    padding: 0.75rem 0; border-bottom: 1px solid {'rgba(255,255,255,0.05)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.05)'};
}}
.process-step:last-child {{ border-bottom: none; }}
.step-indicator {{
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}}
.step-indicator.active {{ animation: pulse 1.5s infinite; }}
.step-text-title {{ font-weight: 600; font-size: 0.87rem; color: {T['text_primary']}; }}
.step-text-sub {{ font-size: 0.73rem; color: {T['text_muted']}; margin-top: 0.1rem; }}

@keyframes pulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }}
    50% {{ box-shadow: 0 0 0 8px rgba(99,102,241,0); }}
}}

/* ── TRUST SCORE ── */
.trust-score-card {{
    background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(99,102,241,0.08));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px; padding: 1.5rem; text-align: center; margin-bottom: 0; height: 100%;
}}
.trust-score-num {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 3.5rem; font-weight: 800;
    background: linear-gradient(135deg, #10b981, #6366f1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.risk-badge {{
    display: inline-block; padding: 0.3em 1em; border-radius: 100px;
    font-size: 0.73rem; font-weight: 700; margin-top: 0.75rem;
}}
.risk-low {{ background: rgba(16,185,129,0.15); color: #10b981; }}
.risk-med {{ background: rgba(245,158,11,0.15); color: #f59e0b; }}
.risk-high {{ background: rgba(239,68,68,0.15); color: #ef4444; }}

/* ── AI SUMMARY ── */
.ai-summary {{
    background: rgba(99,102,241,0.07); border: 1px solid rgba(99,102,241,0.2);
    border-left: 4px solid #6366f1; border-radius: 12px;
    padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
}}
.ai-summary-label {{
    font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #818cf8; margin-bottom: 0.5rem;
}}
.ai-summary-text {{ font-size: 0.9rem; color: #c7d2fe; line-height: 1.75; }}

/* ── CLAIM CARDS ── */
.claim-card {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
    border-left: 4px solid rgba(255,255,255,0.1); transition: background 0.2s;
}}
.claim-card:hover {{ background: {'rgba(255,255,255,0.05)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.04)'}; }}
.claim-card.verified {{ border-left-color: #10b981; }}
.claim-card.inaccurate {{ border-left-color: #f59e0b; }}
.claim-card.false {{ border-left-color: #ef4444; }}
.claim-card.noevidence {{ border-left-color: #64748b; }}
.claim-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 1rem; margin-bottom: 0.6rem; flex-wrap: wrap;
}}
.claim-text {{ font-size: 0.92rem; font-weight: 600; color: {T['text_primary']}; line-height: 1.5; flex: 1; min-width: 180px; }}
.claim-explanation {{ font-size: 0.82rem; color: {T['text_secondary']}; line-height: 1.65; margin-top: 0.4rem; }}
.before-after {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.75rem; }}
.before-box {{
    background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15);
    border-radius: 10px; padding: 0.75rem;
}}
.after-box {{
    background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15);
    border-radius: 10px; padding: 0.75rem;
}}
.ba-label {{ font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.3rem; }}
.before-box .ba-label {{ color: #ef4444; }}
.after-box .ba-label {{ color: #10b981; }}
.ba-text {{ font-size: 0.82rem; color: {T['text_secondary']}; line-height: 1.5; }}
.ai-reasoning {{
    background: rgba(139,92,246,0.06); border: 1px solid rgba(139,92,246,0.15);
    border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.75rem;
}}
.ai-reasoning-label {{ font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; color: #a78bfa; margin-bottom: 0.3rem; }}
.ai-reasoning-text {{ font-size: 0.81rem; color: #c4b5fd; line-height: 1.65; }}
.sources-list {{ margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.source-chip {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 8px; padding: 0.25rem 0.65rem;
    font-size: 0.73rem; color: #818cf8; text-decoration: none; transition: background 0.15s;
}}
.source-chip:hover {{ background: rgba(99,102,241,0.15); }}

/* ── BADGES ── */
.badge {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
    text-transform: uppercase; padding: 0.25em 0.8em; border-radius: 100px; white-space: nowrap;
}}
.badge-verified {{ background: rgba(16,185,129,0.15); color: #10b981; }}
.badge-inaccurate {{ background: rgba(245,158,11,0.15); color: #f59e0b; }}
.badge-false {{ background: rgba(239,68,68,0.15); color: #ef4444; }}
.badge-noevidence {{ background: rgba(100,116,139,0.15); color: #94a3b8; }}

/* ── CONFIDENCE BAR ── */
.conf-wrap {{ margin-top: 0.6rem; display: flex; align-items: center; gap: 0.75rem; }}
.conf-label {{ font-size: 0.73rem; color: {T['text_muted']}; white-space: nowrap; min-width: 78px; }}
.conf-track {{ flex: 1; background: {'rgba(255,255,255,0.06)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.06)'}; border-radius: 100px; height: 6px; }}
.conf-fill {{ height: 6px; border-radius: 100px; }}
.conf-high {{ background: linear-gradient(90deg, #10b981, #34d399); }}
.conf-med {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
.conf-low {{ background: linear-gradient(90deg, #ef4444, #f87171); }}
.conf-pct {{ font-size: 0.76rem; font-weight: 700; min-width: 34px; }}

/* ── SAMPLE CARDS ── */
.sample-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }}
.sample-card {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 1.25rem; text-align: center;
}}
.sample-title {{ font-weight: 700; color: {T['text_primary']}; font-size: 0.88rem; margin-bottom: 0.3rem; }}
.sample-desc {{ font-size: 0.77rem; color: {T['text_muted']}; line-height: 1.55; }}

/* ── CHARTS ── */
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }}
.chart-card {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 1.25rem;
}}
.chart-title {{ font-weight: 700; color: {T['text_primary']}; font-size: 0.87rem; margin-bottom: 1rem; }}
.donut-svg {{ width: 100%; max-width: 150px; display: block; margin: 0 auto; }}
.legend-item {{ display: flex; align-items: center; gap: 0.5rem; font-size: 0.77rem; color: {T['text_secondary']}; margin-bottom: 0.35rem; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
.bar-row {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }}
.bar-label {{ font-size: 0.73rem; color: {T['text_secondary']}; min-width: 80px; }}
.bar-track {{ flex: 1; background: {'rgba(255,255,255,0.06)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.06)'}; border-radius: 100px; height: 10px; }}
.bar-val {{ font-size: 0.73rem; color: {T['text_primary']}; font-weight: 700; min-width: 28px; text-align: right; }}

/* ── SUSPICIOUS ── */
.suspicious-list {{ margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.suspicious-chip {{
    background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.25);
    color: #fb923c; border-radius: 6px; padding: 0.2rem 0.6rem; font-size: 0.73rem; font-weight: 600;
}}

/* ── DROP ZONE ── */
.drop-zone {{
    border: 2px dashed rgba(99,102,241,0.3); border-radius: 16px; padding: 2.5rem 2rem;
    text-align: center; background: rgba(99,102,241,0.04); margin: 0.5rem 0;
}}
.drop-title {{ font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.05rem; font-weight: 700; color: {T['text_primary']}; margin-bottom: 0.4rem; }}
.drop-sub {{ font-size: 0.8rem; color: {T['text_muted']}; }}

/* ── MISC ── */
.stProgress > div > div {{ background: linear-gradient(90deg, #6366f1, #8b5cf6) !important; }}
[data-testid="stFileUploader"] {{
    background: rgba(99,102,241,0.04) !important;
    border: 2px dashed rgba(99,102,241,0.3) !important;
    border-radius: 14px !important;
}}
div[data-testid="stRadio"] {{ display: none !important; }}
hr {{ border-color: {'rgba(255,255,255,0.06)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.06)'} !important; margin: 1.5rem 0 !important; }}
[data-testid="stDownloadButton"] > button {{
    background: rgba(16,185,129,0.12) !important; color: #10b981 !important;
    border: 1px solid rgba(16,185,129,0.3) !important; box-shadow: none !important;
}}
.stTextInput > div > div > input {{
    background: {T['input_bg']} !important;
    border: 1px solid {T['input_border']} !important;
    color: {T['text_primary']} !important;
    border-radius: 10px !important;
}}
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ─────────────────────────────────────────
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
    prompt = f"""You are a fact-checking AI. Extract all specific verifiable factual claims from the text. Focus ONLY on: statistics, percentages, revenue/market figures, user counts, dates tied to events, technical specs, scientific statistics. Return ONLY a valid JSON array of claim strings. No markdown, no preamble. Example: ["India has 950M internet users", "OpenAI reached 100M users in 2023"] Text: {text[:4000]}"""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    return json.loads(clean)

def verify_claim(claim):
    results = tavily.search(claim, max_results=4)
    sources = [{"title":r.get("title",""),"url":r.get("url",""),"date":r.get("published_date","")} for r in results.get("results",[])]
    source_texts = "\n".join([f"- {r.get('title','')} ({r.get('url','')}): {r.get('content','')[:300]}" for r in results.get("results",[])])
    prompt = f"""You are a fact-checking AI. Analyze this claim against web evidence. Claim: "{claim}" Web Evidence: {source_texts}

Classify as: VERIFIED, INACCURATE, FALSE, or NO_EVIDENCE. Reply ONLY with this exact JSON (no markdown):
{{"verdict":"VERIFIED","explanation":"One clear sentence.","correct_fact":"Updated fact if wrong, else empty string.","ai_reasoning":"Brief note on which sources were checked and why confidence is high or low.","confidence":85}} confidence is 0-100 integer."""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    data = json.loads(clean)
    data["sources"] = sources
    return data

def generate_ai_summary(results_list, verified, inaccurate, false_count, noev, total):
    bad = [c for c,r in results_list if r.get("verdict") in ["FALSE","INACCURATE"]][:3]
    prompt = f"""Write a 2-3 sentence professional AI fact-check summary. Stats: {total} claims, {verified} verified, {inaccurate} inaccurate, {false_count} false, {noev} no evidence. Sample problematic claims: {bad} Write like: "This document contains X claims. Y appear verified, while Z contain outdated or unsupported data. Overall reliability is [assessment]." Return ONLY the summary text."""
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
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"
    return f"""<div class="conf-wrap">
        <div class="conf-label" style="color:{color};font-weight:600;">Confidence</div>
        <div class="conf-track"><div class="conf-fill {cls}" style="width:{score}%"></div></div>
        <div class="conf-pct" style="color:{color}">{score}%</div>
    </div>"""

def donut_chart(verified, inaccurate, false_count, noev, total):
    if total == 0: return ""
    cx, cy, r, circ = 75, 75, 55, 2*3.14159*55
    segments = [(verified/total,"#10b981"),(inaccurate/total,"#f59e0b"),(false_count/total,"#ef4444"),(noev/total,"#475569")]
    offset, paths = 0, []
    for ratio, color in segments:
        if ratio == 0: continue
        dash = ratio * circ
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="16" stroke-dasharray="{dash:.1f} {circ-dash:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash
    return f"""<svg viewBox="0 0 150 150" class="donut-svg">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="16"/>
        {"".join(paths)}
        <text x="{cx}" y="{cy-6}" text-anchor="middle" fill="{T['text_primary']}" font-size="20" font-weight="800" font-family="Bricolage Grotesque,sans-serif">{total}</text>
        <text x="{cx}" y="{cy+12}" text-anchor="middle" fill="{T['text_muted']}" font-size="10">claims</text>
    </svg>"""

# ─── TOP NAVBAR ────────────────────────────────────────
theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
theme_label = "Light" if st.session_state.theme == "dark" else "Dark"

nav_pages = ["Home", "Upload PDF", "Fact Check", "Dashboard", "History", "About"]

# Build nav link HTML
nav_links_html = ""
for p in nav_pages:
    active_cls = " active" if st.session_state.page == p else ""
    nav_links_html += f'<span class="nav-link{active_cls}" id="navlink_{p.replace(" ","_")}">{p}</span>'

# Auth area
if st.session_state.user:
    auth_html = f'<div class="user-chip">👤 {st.session_state.user["name"]}</div>'
else:
    auth_html = ""

st.markdown(f"""
<div class="top-navbar">
    <div class="nav-brand">
        <div class="nav-logo-box">FC</div>
        <div class="nav-brand-name">FactCheck</div>
    </div>
    <div class="nav-links">
        {nav_links_html}
    </div>
    <div style="display:flex;align-items:center;gap:0.5rem;">
        {auth_html}
    </div>
</div>
""", unsafe_allow_html=True)

# Navbar buttons using Streamlit (invisible but functional)
nav_cols = st.columns([1,1,1,1,1,1,0.5,0.7,0.7])
for i, p in enumerate(nav_pages):
    with nav_cols[i]:
        if st.button(p, key=f"nav_{p}", help=f"Go to {p}", use_container_width=True):
            st.session_state.page = p
            st.session_state.auth_page = None
            st.rerun()

with nav_cols[6]:
    if st.button(theme_icon, key="theme_toggle", help=f"Switch to {theme_label} mode"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

with nav_cols[7]:
    if st.session_state.user:
        if st.button("Logout", key="logout_btn"):
            st.session_state.user = None
            st.session_state.page = "Home"
            st.rerun()
    else:
        if st.button("Login", key="login_btn"):
            st.session_state.auth_page = "login"
            st.rerun()

with nav_cols[8]:
    if not st.session_state.user:
        if st.button("Sign Up", key="signup_btn"):
            st.session_state.auth_page = "signup"
            st.rerun()

# Hide the nav buttons visually (they overlap with navbar HTML)
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]:first-of-type > div > div > div > button {
    opacity: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    pointer-events: auto !important;
}
</style>
""", unsafe_allow_html=True)

# ─── AUTH PAGES ───────────────────────────────────────
if st.session_state.auth_page == "login":
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Welcome back</div><div class="auth-sub">Login to your FactCheck account</div>', unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="you@example.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="Your password", key="login_pass")

    if st.button("Login →", key="do_login"):
        users_db = st.session_state.users_db
        if email in users_db and users_db[email]["password"] == password:
            st.session_state.user = {"name": users_db[email]["name"], "email": email}
            st.session_state.auth_page = None
            st.session_state.page = "Home"
            st.success("✅ Logged in successfully!")
            st.rerun()
        else:
            st.error("❌ Invalid email or password.")

    st.markdown('<div class="auth-switch">Don\'t have an account? <span id="goto_signup">Sign up</span></div>', unsafe_allow_html=True)
    if st.button("Create an account instead", key="goto_signup_btn"):
        st.session_state.auth_page = "signup"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

elif st.session_state.auth_page == "signup":
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Create account</div><div class="auth-sub">Start fact-checking with AI today</div>', unsafe_allow_html=True)

    name = st.text_input("Full Name", placeholder="Your name", key="signup_name")
    email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
    password = st.text_input("Password", type="password", placeholder="Choose a password", key="signup_pass")
    confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="signup_confirm")

    if st.button("Create Account →", key="do_signup"):
        if not name or not email or not password:
            st.error("Please fill in all fields.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        elif email in st.session_state.users_db:
            st.error("❌ An account with this email already exists.")
        else:
            st.session_state.users_db[email] = {"name": name, "password": password}
            st.session_state.user = {"name": name, "email": email}
            st.session_state.auth_page = None
            st.session_state.page = "Home"
            st.success("✅ Account created!")
            st.rerun()

    st.markdown('<div class="auth-switch">Already have an account? <span>Login</span></div>', unsafe_allow_html=True)
    if st.button("Login instead", key="goto_login_btn"):
        st.session_state.auth_page = "login"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════
if st.session_state.page == "Home":
    # Hero — no box, just text
    st.markdown("""
    <div class="home-hero">
        <div class="home-hero-title">AI-Powered<br><span>Fact Checker</span></div>
        <p class="home-hero-desc">
            Upload any PDF and instantly detect fake, outdated, or misleading claims using
            live web search and AI reasoning — with confidence scores, source links, and detailed explanations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Centered upload button
    col_l, col_c, col_r = st.columns([1.5, 1, 1.5])
    with col_c:
        if st.button("📤 Upload Your PDF", key="home_upload"):
            st.session_state.page = "Upload PDF"; st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # How It Works
    st.markdown('<div class="section-title">How It Works</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="steps-row">
        <div class="step-card"><div class="step-num">STEP 01</div><div class="step-icon">📤</div><div class="step-title">Upload PDF</div><div class="step-desc">Upload any document — report, research, article, or marketing material.</div></div>
        <div class="step-card"><div class="step-num">STEP 02</div><div class="step-icon">🧠</div><div class="step-title">Extract Claims</div><div class="step-desc">AI detects all verifiable stats, dates, figures, and facts.</div></div>
        <div class="step-card"><div class="step-num">STEP 03</div><div class="step-icon">🌐</div><div class="step-title">Verify on Web</div><div class="step-desc">Each claim is cross-checked against live web sources.</div></div>
        <div class="step-card"><div class="step-num">STEP 04</div><div class="step-icon">📊</div><div class="step-title">Get Report</div><div class="step-desc">Receive verdicts, confidence scores, sources, and correct facts.</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Features
    st.markdown('<div class="section-title" style="margin-top:2rem;">Features</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="features-grid">
        <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Confidence Scores</div><div class="feature-desc">Each verdict includes a 0–100% confidence score based on source agreement.</div></div>
        <div class="feature-card"><div class="feature-icon">🔗</div><div class="feature-title">Live Source Links</div><div class="feature-desc">Every claim links to the real web sources used for verification.</div></div>
        <div class="feature-card"><div class="feature-icon">🤖</div><div class="feature-title">AI Reasoning</div><div class="feature-desc">Understand why each claim is flagged with detailed AI explanation.</div></div>
        <div class="feature-card"><div class="feature-icon">🔄</div><div class="feature-title">Before vs After</div><div class="feature-desc">See the uploaded claim vs the correct updated fact side by side.</div></div>
        <div class="feature-card"><div class="feature-icon">🚨</div><div class="feature-title">Suspicious Language</div><div class="feature-desc">Detects exaggerated marketing claims like "world's best" or "#1".</div></div>
        <div class="feature-card"><div class="feature-icon">📥</div><div class="feature-title">Export Report</div><div class="feature-desc">Download your full fact-check results as a clean text report.</div></div>
        <div class="feature-card"><div class="feature-icon">📊</div><div class="feature-title">Visual Dashboard</div><div class="feature-desc">Donut charts and bar graphs showing claim distribution at a glance.</div></div>
        <div class="feature-card"><div class="feature-icon">🕐</div><div class="feature-title">History Tracking</div><div class="feature-desc">All your previous fact-check sessions stored for easy reference.</div></div>
        <div class="feature-card"><div class="feature-icon">🌗</div><div class="feature-title">Dark & Light Mode</div><div class="feature-desc">Switch between dark and light themes using the toggle in the navbar.</div></div>
    </div>
    """, unsafe_allow_html=True)

    # About section on Home
    st.markdown("""
    <div class="about-section">
        <div class="about-title">About FactCheck AI</div>
        <p class="about-desc">
            FactCheck AI is an open-source tool that combines large language models with real-time web search
            to automatically verify factual claims in any PDF document. Built with Streamlit, Groq (LLaMA 3),
            and Tavily Search — it gives journalists, researchers, and businesses a fast, reliable way
            to audit content for misinformation.
        </p>
        <div class="about-tags">
            <span class="about-tag">Groq LLaMA 3</span>
            <span class="about-tag">Tavily Search</span>
            <span class="about-tag">Streamlit</span>
            <span class="about-tag">Open Source</span>
            <span class="about-tag">AI Fact-Checking</span>
        </div>
        <a class="github-btn" href="https://github.com/yourusername/factcheck-ai" target="_blank">
            ⭐ View on GitHub
        </a>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# ℹ️ ABOUT (standalone page)
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "About":
    st.markdown('<div class="page-header"><div class="page-title">About FactCheck AI</div><div class="page-subtitle">The story, the stack, and the mission.</div></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="about-section" style="text-align:left;">
        <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.3rem;font-weight:800;margin-bottom:0.75rem;">What is FactCheck AI?</div>
        <p style="font-size:0.93rem;color:#94a3b8;line-height:1.8;margin-bottom:1.25rem;">
            FactCheck AI is an AI-powered document verification tool that extracts every verifiable factual claim
            from a PDF — statistics, dates, market figures, technical specs — and cross-references each one against
            live web data in real time. Each claim receives a <strong style="color:#f1f5f9;">verdict</strong>
            (Verified / Inaccurate / False / No Evidence), a <strong style="color:#f1f5f9;">confidence score</strong>,
            clickable <strong style="color:#f1f5f9;">source links</strong>, and an <strong style="color:#f1f5f9;">AI explanation</strong>.
        </p>
        <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;font-weight:800;margin-bottom:0.65rem;">Tech Stack</div>
        <div class="about-tags" style="justify-content:flex-start;margin-bottom:1.25rem;">
            <span class="about-tag">🦙 Groq — LLaMA 3.3 70B</span>
            <span class="about-tag">🔍 Tavily Search API</span>
            <span class="about-tag">🖥️ Streamlit</span>
            <span class="about-tag">📄 pdfplumber</span>
            <span class="about-tag">🐍 Python</span>
        </div>
        <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;font-weight:800;margin-bottom:0.65rem;">Who is it for?</div>
        <p style="font-size:0.88rem;color:#94a3b8;line-height:1.75;margin-bottom:1.5rem;">
            Journalists fact-checking articles · Researchers validating data · Businesses auditing marketing materials ·
            Students verifying sources · Anyone who wants fast, trustworthy content verification.
        </p>
        <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;font-weight:800;margin-bottom:0.65rem;">Open Source</div>
        <p style="font-size:0.88rem;color:#94a3b8;line-height:1.75;margin-bottom:1.5rem;">
            FactCheck AI is fully open source. Contributions, bug reports, and feature requests are welcome.
            Star the repo if you find it useful!
        </p>
        <a class="github-btn" href="https://github.com/yourusername/factcheck-ai" target="_blank">
            ⭐ View on GitHub — yourusername/factcheck-ai
        </a>
    </div>
    """, unsafe_allow_html=True)

    # Feature recap
    st.markdown('<div class="section-title" style="margin-top:1.5rem;">Everything Included</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="features-grid">
        <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Confidence Scores</div><div class="feature-desc">Each verdict includes a 0–100% confidence score based on source agreement.</div></div>
        <div class="feature-card"><div class="feature-icon">🔗</div><div class="feature-title">Live Source Links</div><div class="feature-desc">Every claim links to the real web sources used for verification.</div></div>
        <div class="feature-card"><div class="feature-icon">🤖</div><div class="feature-title">AI Reasoning</div><div class="feature-desc">Understand why each claim is flagged with detailed AI explanation.</div></div>
        <div class="feature-card"><div class="feature-icon">🔄</div><div class="feature-title">Before vs After</div><div class="feature-desc">See the uploaded claim vs the correct updated fact side by side.</div></div>
        <div class="feature-card"><div class="feature-icon">🚨</div><div class="feature-title">Suspicious Language</div><div class="feature-desc">Detects exaggerated marketing claims like "world's best" or "#1".</div></div>
        <div class="feature-card"><div class="feature-icon">📥</div><div class="feature-title">Export Report</div><div class="feature-desc">Download your full fact-check results as a clean text report.</div></div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 📤 UPLOAD PDF
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Upload PDF":
    st.markdown('<div class="page-header"><div class="page-title">Upload Your PDF</div><div class="page-subtitle">Upload any document to start AI fact-checking.</div></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF (Max 50MB)", type="pdf", label_visibility="visible")

    if not uploaded_file:
        st.markdown("""
        <div class="drop-zone">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">☁️</div>
            <div class="drop-title">Drag & drop your PDF here</div>
            <div class="drop-sub" style="margin-top:0.3rem;">or use the uploader above · PDF · Max 50MB</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700;margin-bottom:0.75rem;font-size:0.93rem;">📋 Try Our Sample PDFs</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sample-grid">
            <div class="sample-card"><div style="font-size:2rem;margin-bottom:0.65rem;">📋</div><div class="sample-title">Demo PDF — Real Facts</div><div class="sample-desc">Contains accurate, verifiable claims and up-to-date statistics.</div></div>
            <div class="sample-card"><div style="font-size:2rem;margin-bottom:0.65rem;">⚠️</div><div class="sample-title">Trap PDF — Fake & Outdated</div><div class="sample-desc">Contains intentionally false and outdated statistics to test detection.</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.info("🔒 Your PDF is processed securely. No data is stored or shared.")
    else:
        st.success(f"✅ **{uploaded_file.name}** is ready!")
        st.session_state.uploaded_file = uploaded_file
        st.session_state.results = None
        file_size = len(uploaded_file.getvalue()) / 1024
        st.markdown(f"""
        <div class="glass-card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
            <div>
                <div style="font-weight:700;color:{T['text_primary']};">📄 {uploaded_file.name}</div>
                <div style="font-size:0.76rem;color:{T['text_muted']};margin-top:0.2rem;">Size: {file_size:.1f} KB · PDF Document</div>
            </div>
            <span class="badge badge-verified">Ready</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start Fact Checking"):
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
        st.markdown('<div class="page-header"><div class="page-title">Fact Check in Progress</div><div class="page-subtitle">Please wait while we extract and verify claims from your document.</div></div>', unsafe_allow_html=True)

        stepper = st.empty()
        def render_stepper(active):
            steps = [("📄","Reading PDF","Extracting text from document"),("🧠","Extracting Claims","AI identifying verifiable facts"),("🌐","Searching Web","Live web search for each claim"),("🔍","Verifying Facts","Cross-referencing sources"),("📊","Generating Report","Compiling your fact-check report")]
            html = '<div class="process-stepper">'
            for i,(icon,title,sub) in enumerate(steps):
                if i < active: state,color,show = "done","#10b981","✓"
                elif i == active: state,color,show = "active","#6366f1",icon
                else: state,color,show = "pending","#2d3748",icon
                bg = "rgba(16,185,129,.1)" if state=="done" else "rgba(99,102,241,.1)" if state=="active" else "rgba(255,255,255,.04)"
                tc = "#10b981" if state=="done" else T['text_primary'] if state=="active" else "#4a5568"
                html += f'<div class="process-step"><div class="step-indicator {state}" style="background:{bg};"><span style="color:{color}">{show}</span></div><div><div class="step-text-title" style="color:{tc}">{title}</div><div class="step-text-sub">{sub}</div></div></div>'
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
            status_txt.markdown(f'<div style="font-size:0.8rem;color:{T["text_muted"]};padding:0.4rem 0;">🔎 Verifying <b style="color:#818cf8">{i+1}</b> of <b>{len(claims)}</b>: <span style="color:{T["text_secondary"]};font-style:italic;">{claim[:70]}...</span></div>', unsafe_allow_html=True)
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

        st.markdown(f'<div class="page-header"><div class="page-title">✅ Fact Check Complete</div><div class="page-subtitle">📄 {r["filename"]} · {r["date"]}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-summary"><div class="ai-summary-label">🤖 AI Summary</div><div class="ai-summary-text">{r.get("ai_summary","")}</div></div>', unsafe_allow_html=True)

        col_trust, col_metrics = st.columns([1, 3])
        with col_trust:
            st.markdown(f"""<div class="trust-score-card">
                <div style="font-size:0.65rem;color:{T['text_muted']};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem;">Trust Score</div>
                <div class="trust-score-num">{trust}</div>
                <div style="font-size:0.65rem;color:{T['text_muted']};">/100</div>
                <div><span class="risk-badge {risk_cls}">{risk_label}</span></div>
            </div>""", unsafe_allow_html=True)
        with col_metrics:
            st.markdown(f"""<div class="metrics-grid">
                <div class="metric-card metric-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
                <div class="metric-card metric-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
                <div class="metric-card metric-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
                <div class="metric-card metric-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
            </div>""", unsafe_allow_html=True)

        if r.get("suspicious"):
            chips = "".join([f'<span class="suspicious-chip">"{p}"</span>' for p in r["suspicious"]])
            st.markdown(f'<div class="glass-card" style="border-color:rgba(249,115,22,.2);margin-bottom:1rem;"><div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#f97316;margin-bottom:.5rem;">🚨 Suspicious Marketing Language Detected</div><div class="suspicious-list">{chips}</div></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊 View Dashboard"):
                st.session_state.page = "Dashboard"; st.rerun()
        with c2:
            if st.button("🔄 Check Another PDF"):
                st.session_state.results = None; st.session_state.uploaded_file = None
                st.session_state.page = "Upload PDF"; st.rerun()
        with c3:
            lines = [f"FactCheck AI — {r['filename']}",f"Date: {r['date']}",f"Trust Score: {trust}/100 ({risk_label})",f"Total: {r['total']} | Verified: {r['verified']} | Inaccurate: {r['inaccurate']} | False: {r['false']}","",f"AI Summary: {r.get('ai_summary','')}","","="*60,""]
            for i,(claim,res) in enumerate(r["claims"],1):
                lines += [f"{i}. [{res.get('verdict','?')}] {claim}",f"   Explanation: {res.get('explanation','')}",f"   Confidence: {res.get('confidence',0)}%"]
                if res.get("correct_fact"): lines.append(f"   Correct Fact: {res['correct_fact']}")
                if res.get("ai_reasoning"): lines.append(f"   AI Reasoning: {res['ai_reasoning']}")
                for s in res.get("sources",[])[:2]:
                    if s.get("url"): lines.append(f"   Source: {s['url']}")
                lines.append("")
            st.download_button("📥 Download Report", data="\n".join(lines), file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:Bricolage Grotesque,sans-serif;font-size:1.05rem;font-weight:800;margin-bottom:1rem;">📋 Detailed Results</div>', unsafe_allow_html=True)

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
                extra = f'<div class="ai-reasoning"><div class="ai-reasoning-label">📌 Correct Fact</div><div class="ai-reasoning-text">{correct}</div></div>'
            else:
                extra = ""

            reasoning = f'<div class="ai-reasoning"><div class="ai-reasoning-label">🤖 AI Reasoning</div><div class="ai-reasoning-text">{ai_reason}</div></div>' if ai_reason else ""
            src_links = "".join([f'<a class="source-chip" href="{s["url"]}" target="_blank">🔗 {(s["title"] or s["url"])[:38]}...</a>' for s in sources[:3] if s.get("url")])
            sources_html = f'<div class="sources-list">{src_links}</div>' if src_links else ""

            st.markdown(f"""<div class="claim-card {c_class}">
                <div class="claim-header">
                    <div class="claim-text">{claim}</div>
                    <div>{verdict_badge(verdict)}</div>
                </div>
                <div class="claim-explanation">{result.get('explanation','')}</div>
                {confidence_html(confidence)}
                {extra}{reasoning}{sources_html}
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 📊 DASHBOARD
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Dashboard":
    st.markdown('<div class="page-header"><div class="page-title">📊 Dashboard</div><div class="page-subtitle">Analytics and overview of your last fact check.</div></div>', unsafe_allow_html=True)

    r = st.session_state.results
    if r is None:
        st.info("No results yet. Upload a PDF to get started.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()
    else:
        total = r["total"] or 1
        trust = r.get("trust_score",70)
        color = "#10b981" if trust>=70 else "#f59e0b" if trust>=45 else "#ef4444"

        st.markdown(f"""<div class="metrics-grid">
            <div class="metric-card metric-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
            <div class="metric-card metric-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
            <div class="metric-card metric-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
            <div class="metric-card metric-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
        </div>""", unsafe_allow_html=True)

        donut = donut_chart(r["verified"],r["inaccurate"],r["false"],r["noevidence"],r["total"])
        st.markdown(f"""<div class="charts-row">
            <div class="chart-card">
                <div class="chart-title">Claim Distribution</div>
                {donut}
                <div style="margin-top:0.75rem;">
                    <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>Verified ({r['verified']})</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Inaccurate ({r['inaccurate']})</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>False ({r['false']})</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#475569"></div>No Evidence ({r['noevidence']})</div>
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-title">Verification Breakdown</div>
                <div class="bar-row"><div class="bar-label">✅ Verified</div><div class="bar-track"><div style="width:{r['verified']/total*100:.0f}%;background:#10b981;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['verified']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">⚠️ Inaccurate</div><div class="bar-track"><div style="width:{r['inaccurate']/total*100:.0f}%;background:#f59e0b;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['inaccurate']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❌ False</div><div class="bar-track"><div style="width:{r['false']/total*100:.0f}%;background:#ef4444;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['false']/total*100:.0f}%</div></div>
                <div class="bar-row"><div class="bar-label">❓ No Evidence</div><div class="bar-track"><div style="width:{r['noevidence']/total*100:.0f}%;background:#475569;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['noevidence']/total*100:.0f}%</div></div>
                <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid {'rgba(255,255,255,.06)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,.06)'};">
                    <div style="font-size:0.72rem;color:{T['text_muted']};margin-bottom:0.3rem;">Trust Score</div>
                    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.8rem;font-weight:800;color:{color};">{trust}/100</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if r.get("ai_summary"):
            st.markdown(f'<div class="ai-summary"><div class="ai-summary-label">🤖 AI Summary</div><div class="ai-summary-text">{r["ai_summary"]}</div></div>', unsafe_allow_html=True)

        if st.button("📋 View Detailed Results"):
            st.session_state.page = "Fact Check"; st.rerun()

# ═══════════════════════════════════════════════════════
# 🕐 HISTORY
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "History":
    st.markdown('<div class="page-header"><div class="page-title">🕐 History</div><div class="page-subtitle">All your previously fact-checked documents.</div></div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown(f'<div style="text-align:center;padding:3rem;background:{T["card_bg"]};border:1px solid {T["card_border"]};border-radius:16px;"><div style="font-size:2.5rem;margin-bottom:1rem;">🕐</div><div style="font-weight:700;color:{T["text_primary"]};margin-bottom:.5rem;">No history yet</div><div style="font-size:.83rem;color:{T["text_muted"]};">Your fact-check results will appear here after analyzing a PDF.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:.5rem 1.25rem;font-size:.66rem;font-weight:700;color:{T["text_muted"]};text-transform:uppercase;letter-spacing:.08em;"><div>Document</div><div>Total</div><div>✅</div><div>⚠️</div><div>❌</div><div>Date</div></div>', unsafe_allow_html=True)
        for h in reversed(st.session_state.history):
            trust = h.get("trust_score",70)
            tc = "#10b981" if trust>=70 else "#f59e0b" if trust>=45 else "#ef4444"
            st.markdown(f'<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:1rem 1.25rem;background:{T["card_bg"]};border:1px solid {T["card_border"]};border-radius:12px;margin-bottom:.5rem;align-items:center;"><div><div style="font-weight:600;color:{T["text_primary"]};font-size:.87rem;">📄 {h["filename"]}</div><div style="font-size:.68rem;color:{T["text_muted"]};margin-top:.15rem;">Trust: <span style="color:{tc};font-weight:700;">{trust}/100</span></div></div><div style="font-weight:700;color:{T["text_primary"]};">{h["total"]}</div><div style="color:#10b981;font-weight:700;">{h["verified"]}</div><div style="color:#f59e0b;font-weight:700;">{h["inaccurate"]}</div><div style="color:#ef4444;font-weight:700;">{h["false"]}</div><div style="font-size:.76rem;color:{T["text_muted"]};">{h["date"]}</div></div>', unsafe_allow_html=True)
