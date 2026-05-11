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
    ("theme", "dark"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── THEME VARIABLES ───────────────────────────────────
def get_theme_vars(theme):
    if theme == "dark":
        return {
            "bg_main": "#0a0e1a",
            "bg_sidebar": "#0d1224",
            "bg_card": "rgba(255,255,255,0.04)",
            "bg_card_hover": "rgba(255,255,255,0.06)",
            "border": "rgba(255,255,255,0.08)",
            "border_sidebar": "#1e2a45",
            "text_primary": "#f1f5f9",
            "text_secondary": "#e2e8f0",
            "text_muted": "#64748b",
            "text_dimmed": "#4a5568",
            "text_dimmed2": "#2d3748",
            "hero_bg": "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)",
            "hero_border": "rgba(99,102,241,0.3)",
            "hero_badge_bg": "rgba(99,102,241,0.2)",
            "hero_badge_border": "rgba(99,102,241,0.4)",
            "hero_badge_text": "#a5b4fc",
            "hero_sub": "#94a3b8",
            "hero_bullets": "#a5b4fc",
            "hero_bullet_mark": "#818cf8",
            "step_bg": "rgba(255,255,255,0.03)",
            "step_border": "rgba(255,255,255,0.07)",
            "step_hover": "rgba(99,102,241,0.4)",
            "step_title": "#e2e8f0",
            "step_desc": "#64748b",
            "step_num_bg": "rgba(99,102,241,0.15)",
            "step_num_text": "#818cf8",
            "feature_card_bg": "rgba(255,255,255,0.03)",
            "feature_card_border": "rgba(255,255,255,0.07)",
            "feature_hover": "rgba(99,102,241,0.3)",
            "feature_title": "#e2e8f0",
            "feature_desc": "#64748b",
            "sample_card_bg": "rgba(255,255,255,0.03)",
            "sample_card_border": "rgba(255,255,255,0.07)",
            "sample_title": "#e2e8f0",
            "sample_desc": "#64748b",
            "ai_summary_bg": "rgba(99,102,241,0.07)",
            "ai_summary_border": "rgba(99,102,241,0.2)",
            "ai_summary_label": "#818cf8",
            "ai_summary_text": "#c7d2fe",
            "claim_bg": "rgba(255,255,255,0.03)",
            "claim_hover": "rgba(255,255,255,0.05)",
            "claim_border": "rgba(255,255,255,0.07)",
            "claim_text": "#e2e8f0",
            "claim_explanation": "#94a3b8",
            "before_bg": "rgba(239,68,68,0.06)",
            "before_border": "rgba(239,68,68,0.15)",
            "after_bg": "rgba(16,185,129,0.06)",
            "after_border": "rgba(16,185,129,0.15)",
            "ba_text": "#cbd5e1",
            "ai_reason_bg": "rgba(139,92,246,0.06)",
            "ai_reason_border": "rgba(139,92,246,0.15)",
            "ai_reason_label": "#a78bfa",
            "ai_reason_text": "#c4b5fd",
            "source_chip_bg": "rgba(255,255,255,0.04)",
            "source_chip_border": "rgba(255,255,255,0.1)",
            "source_chip_text": "#818cf8",
            "source_chip_hover": "rgba(99,102,241,0.15)",
            "conf_track": "rgba(255,255,255,0.06)",
            "chart_bg": "rgba(255,255,255,0.03)",
            "chart_border": "rgba(255,255,255,0.07)",
            "chart_title": "#e2e8f0",
            "legend_text": "#94a3b8",
            "bar_text": "#94a3b8",
            "bar_track": "rgba(255,255,255,0.06)",
            "bar_val": "#e2e8f0",
            "metric_card_bg": "rgba(255,255,255,0.04)",
            "metric_card_border": "rgba(255,255,255,0.08)",
            "trust_bg": "linear-gradient(135deg, rgba(16,185,129,0.08), rgba(99,102,241,0.08))",
            "trust_border": "rgba(99,102,241,0.2)",
            "process_bg": "rgba(255,255,255,0.03)",
            "process_border": "rgba(255,255,255,0.07)",
            "process_step_border": "rgba(255,255,255,0.05)",
            "process_title": "#e2e8f0",
            "drop_zone_border": "rgba(99,102,241,0.3)",
            "drop_zone_bg": "rgba(99,102,241,0.04)",
            "drop_title": "#e2e8f0",
            "drop_sub": "#4a5568",
            "glass_card_bg": "rgba(255,255,255,0.04)",
            "glass_card_border": "rgba(255,255,255,0.08)",
            "arch_bg": "rgba(99,102,241,0.08)",
            "arch_border": "rgba(99,102,241,0.15)",
            "arch_title": "#a5b4fc",
            "arch_text": "#64748b",
            "about_bg": "rgba(255,255,255,0.03)",
            "about_border": "rgba(255,255,255,0.08)",
            "about_card_bg": "rgba(99,102,241,0.08)",
            "about_card_border": "rgba(99,102,241,0.2)",
            "about_story_label": "#818cf8",
            "about_title": "#f1f5f9",
            "about_cert_bg": "rgba(255,255,255,0.06)",
            "about_cert_border": "rgba(255,255,255,0.12)",
            "about_cert_title": "#c7d2fe",
            "about_cert_desc": "#64748b",
            "about_text": "#94a3b8",
            "about_btn_primary": "linear-gradient(135deg, #6366f1, #8b5cf6)",
            "about_btn_outline": "rgba(255,255,255,0.05)",
            "about_btn_outline_border": "rgba(255,255,255,0.15)",
            "about_btn_outline_text": "#e2e8f0",
            "history_header_bg": "rgba(255,255,255,0.03)",
            "history_header_border": "rgba(255,255,255,0.07)",
            "history_row_bg": "rgba(255,255,255,0.03)",
            "history_row_border": "rgba(255,255,255,0.07)",
            "history_col_text": "#4a5568",
            "sidebar_logo_sub": "#4a5568",
            "sidebar_section_text": "#2d3748",
            "theme_icon": "☀️",
            "theme_label": "Light Mode",
            "susp_bg": "rgba(249,115,22,0.1)",
            "susp_border": "rgba(249,115,22,0.25)",
            "hr_color": "rgba(255,255,255,0.06)",
        }
    else:
        return {
            "bg_main": "#f8fafc",
            "bg_sidebar": "#ffffff",
            "bg_card": "rgba(0,0,0,0.03)",
            "bg_card_hover": "rgba(0,0,0,0.05)",
            "border": "rgba(0,0,0,0.08)",
            "border_sidebar": "#e2e8f0",
            "text_primary": "#0f172a",
            "text_secondary": "#1e293b",
            "text_muted": "#64748b",
            "text_dimmed": "#94a3b8",
            "text_dimmed2": "#cbd5e1",
            "hero_bg": "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 50%, #eef2ff 100%)",
            "hero_border": "rgba(99,102,241,0.25)",
            "hero_badge_bg": "rgba(99,102,241,0.1)",
            "hero_badge_border": "rgba(99,102,241,0.3)",
            "hero_badge_text": "#4338ca",
            "hero_sub": "#475569",
            "hero_bullets": "#4338ca",
            "hero_bullet_mark": "#6366f1",
            "step_bg": "rgba(0,0,0,0.02)",
            "step_border": "rgba(0,0,0,0.07)",
            "step_hover": "rgba(99,102,241,0.3)",
            "step_title": "#0f172a",
            "step_desc": "#64748b",
            "step_num_bg": "rgba(99,102,241,0.12)",
            "step_num_text": "#4338ca",
            "feature_card_bg": "#ffffff",
            "feature_card_border": "#e2e8f0",
            "feature_hover": "rgba(99,102,241,0.2)",
            "feature_title": "#0f172a",
            "feature_desc": "#64748b",
            "sample_card_bg": "#ffffff",
            "sample_card_border": "#e2e8f0",
            "sample_title": "#0f172a",
            "sample_desc": "#64748b",
            "ai_summary_bg": "rgba(99,102,241,0.05)",
            "ai_summary_border": "rgba(99,102,241,0.2)",
            "ai_summary_label": "#4338ca",
            "ai_summary_text": "#3730a3",
            "claim_bg": "#ffffff",
            "claim_hover": "#f8fafc",
            "claim_border": "#e2e8f0",
            "claim_text": "#0f172a",
            "claim_explanation": "#475569",
            "before_bg": "rgba(239,68,68,0.04)",
            "before_border": "rgba(239,68,68,0.2)",
            "after_bg": "rgba(16,185,129,0.04)",
            "after_border": "rgba(16,185,129,0.2)",
            "ba_text": "#334155",
            "ai_reason_bg": "rgba(139,92,246,0.04)",
            "ai_reason_border": "rgba(139,92,246,0.2)",
            "ai_reason_label": "#7c3aed",
            "ai_reason_text": "#5b21b6",
            "source_chip_bg": "rgba(0,0,0,0.03)",
            "source_chip_border": "#e2e8f0",
            "source_chip_text": "#4338ca",
            "source_chip_hover": "rgba(99,102,241,0.1)",
            "conf_track": "rgba(0,0,0,0.06)",
            "chart_bg": "#ffffff",
            "chart_border": "#e2e8f0",
            "chart_title": "#0f172a",
            "legend_text": "#475569",
            "bar_text": "#475569",
            "bar_track": "rgba(0,0,0,0.06)",
            "bar_val": "#0f172a",
            "metric_card_bg": "#ffffff",
            "metric_card_border": "#e2e8f0",
            "trust_bg": "linear-gradient(135deg, rgba(16,185,129,0.06), rgba(99,102,241,0.06))",
            "trust_border": "rgba(99,102,241,0.2)",
            "process_bg": "#ffffff",
            "process_border": "#e2e8f0",
            "process_step_border": "rgba(0,0,0,0.05)",
            "process_title": "#0f172a",
            "drop_zone_border": "rgba(99,102,241,0.3)",
            "drop_zone_bg": "rgba(99,102,241,0.03)",
            "drop_title": "#0f172a",
            "drop_sub": "#94a3b8",
            "glass_card_bg": "rgba(0,0,0,0.02)",
            "glass_card_border": "#e2e8f0",
            "arch_bg": "rgba(99,102,241,0.05)",
            "arch_border": "rgba(99,102,241,0.15)",
            "arch_title": "#4338ca",
            "arch_text": "#64748b",
            "about_bg": "#ffffff",
            "about_border": "#e2e8f0",
            "about_card_bg": "rgba(99,102,241,0.05)",
            "about_card_border": "rgba(99,102,241,0.15)",
            "about_story_label": "#4338ca",
            "about_title": "#0f172a",
            "about_cert_bg": "rgba(99,102,241,0.08)",
            "about_cert_border": "rgba(99,102,241,0.2)",
            "about_cert_title": "#3730a3",
            "about_cert_desc": "#64748b",
            "about_text": "#475569",
            "about_btn_primary": "linear-gradient(135deg, #6366f1, #8b5cf6)",
            "about_btn_outline": "rgba(0,0,0,0.03)",
            "about_btn_outline_border": "#e2e8f0",
            "about_btn_outline_text": "#0f172a",
            "history_header_bg": "#f1f5f9",
            "history_header_border": "#e2e8f0",
            "history_row_bg": "#ffffff",
            "history_row_border": "#e2e8f0",
            "history_col_text": "#94a3b8",
            "sidebar_logo_sub": "#94a3b8",
            "sidebar_section_text": "#94a3b8",
            "theme_icon": "🌙",
            "theme_label": "Dark Mode",
            "susp_bg": "rgba(249,115,22,0.08)",
            "susp_border": "rgba(249,115,22,0.2)",
            "hr_color": "rgba(0,0,0,0.06)",
        }

T = get_theme_vars(st.session_state.theme)

# ─── CSS ───────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Bricolage+Grotesque:wght@400;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: {T['bg_main']} !important;
    color: {T['text_secondary']} !important;
    transition: background 0.3s ease, color 0.3s ease;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

.block-container {{
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1080px !important;
}}

@media (max-width: 768px) {{
    .block-container {{ padding: 1rem 0.75rem 2rem 0.75rem !important; }}
    .metrics-grid {{ grid-template-columns: repeat(2, 1fr) !important; }}
    .steps-row {{ grid-template-columns: repeat(2, 1fr) !important; }}
    .features-grid {{ grid-template-columns: 1fr !important; }}
    .hero-title {{ font-size: 2rem !important; }}
    .charts-row {{ grid-template-columns: 1fr !important; }}
    .before-after {{ grid-template-columns: 1fr !important; }}
    .sample-grid {{ grid-template-columns: 1fr !important; }}
}}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {{
    background: {T['bg_sidebar']} !important;
    border-right: 1px solid {T['border_sidebar']} !important;
    transition: background 0.3s ease;
}}
section[data-testid="stSidebar"] > div {{ padding: 1.25rem 0.75rem !important; }}

.sidebar-logo {{
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0.75rem 1.25rem 0.75rem;
    border-bottom: 1px solid {T['border_sidebar']}; margin-bottom: 1rem;
}}
.sidebar-logo-text {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.05rem; font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.sidebar-logo-sub {{ font-size: 0.62rem; color: {T['sidebar_logo_sub']}; }}
.sidebar-section {{
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: {T['sidebar_section_text']};
    padding: 0 0.75rem; margin: 1rem 0 0.4rem 0;
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
    background: {T['glass_card_bg']};
    border: 1px solid {T['glass_card_border']};
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
}}

/* ── METRICS ── */
.metrics-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}}
.metric-card {{
    background: {T['metric_card_bg']};
    border: 1px solid {T['metric_card_border']};
    border-radius: 14px; padding: 1.25rem; text-align: center;
}}
.metric-num {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 2.2rem; font-weight: 800; line-height: 1;
}}
.metric-label {{ font-size: 0.73rem; color: {T['text_muted']}; margin-top: 0.3rem; font-weight: 500; }}
.metric-total .metric-num {{ color: {T['text_secondary']}; }}
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

/* ── HERO ── */
.hero-section {{
    background: {T['hero_bg']};
    border: 1px solid {T['hero_border']};
    border-radius: 20px; padding: 3rem 2.5rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
}}
.hero-section::before {{
    content: ''; position: absolute; top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero-badge {{
    display: inline-block;
    background: {T['hero_badge_bg']}; border: 1px solid {T['hero_badge_border']};
    color: {T['hero_badge_text']}; font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.3em 1em; border-radius: 100px; margin-bottom: 1rem;
}}
.hero-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 3rem; font-weight: 800; line-height: 1.1;
    color: {T['text_primary']}; margin-bottom: 0.75rem;
}}
.hero-title span {{
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero-sub {{ font-size: 0.97rem; color: {T['hero_sub']}; max-width: 480px; line-height: 1.75; margin-bottom: 1.5rem; }}
.hero-bullets {{ list-style: none; display: flex; flex-direction: column; gap: 0.4rem; }}
.hero-bullets li {{ font-size: 0.85rem; color: {T['hero_bullets']}; }}
.hero-bullets li::before {{ content: '✦ '; color: {T['hero_bullet_mark']}; }}

/* ── STEPS ── */
.steps-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }}
.step-card {{
    background: {T['step_bg']}; border: 1px solid {T['step_border']};
    border-radius: 14px; padding: 1.4rem 1rem; text-align: center; transition: border-color 0.2s;
}}
.step-card:hover {{ border-color: {T['step_hover']}; }}
.step-num {{
    font-size: 0.62rem; font-weight: 800; letter-spacing: 0.1em;
    color: {T['step_num_text']}; background: {T['step_num_bg']};
    border-radius: 100px; display: inline-block; padding: 0.2em 0.75em; margin-bottom: 0.75rem;
}}
.step-icon {{ font-size: 1.7rem; margin-bottom: 0.5rem; }}
.step-title {{ font-weight: 700; color: {T['step_title']}; font-size: 0.87rem; margin-bottom: 0.3rem; }}
.step-desc {{ font-size: 0.77rem; color: {T['step_desc']}; line-height: 1.6; }}

/* ── PROCESSING STEPPER ── */
.process-stepper {{
    background: {T['process_bg']}; border: 1px solid {T['process_border']};
    border-radius: 16px; padding: 1.5rem; margin: 1rem 0;
}}
.process-step {{
    display: flex; align-items: center; gap: 1rem;
    padding: 0.75rem 0; border-bottom: 1px solid {T['process_step_border']};
}}
.process-step:last-child {{ border-bottom: none; }}
.step-indicator {{
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}}
.step-indicator.active {{ animation: pulse 1.5s infinite; }}
.step-text-title {{ font-weight: 600; font-size: 0.87rem; color: {T['process_title']}; }}
.step-text-sub {{ font-size: 0.73rem; color: {T['text_muted']}; margin-top: 0.1rem; }}

@keyframes pulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }}
    50% {{ box-shadow: 0 0 0 8px rgba(99,102,241,0); }}
}}

/* ── TRUST SCORE ── */
.trust-score-card {{
    background: {T['trust_bg']};
    border: 1px solid {T['trust_border']};
    border-radius: 16px; padding: 1.5rem; text-align: center; margin-bottom: 0;
    height: 100%;
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
    background: {T['ai_summary_bg']}; border: 1px solid {T['ai_summary_border']};
    border-left: 4px solid #6366f1; border-radius: 12px;
    padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
}}
.ai-summary-label {{
    font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: {T['ai_summary_label']}; margin-bottom: 0.5rem;
}}
.ai-summary-text {{ font-size: 0.9rem; color: {T['ai_summary_text']}; line-height: 1.75; }}

/* ── CLAIM CARDS ── */
.claim-card {{
    background: {T['claim_bg']}; border: 1px solid {T['claim_border']};
    border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
    border-left: 4px solid rgba(255,255,255,0.1); transition: background 0.2s;
}}
.claim-card:hover {{ background: {T['claim_hover']}; }}
.claim-card.verified {{ border-left-color: #10b981; }}
.claim-card.inaccurate {{ border-left-color: #f59e0b; }}
.claim-card.false {{ border-left-color: #ef4444; }}
.claim-card.noevidence {{ border-left-color: #64748b; }}
.claim-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 1rem; margin-bottom: 0.6rem; flex-wrap: wrap;
}}
.claim-text {{ font-size: 0.92rem; font-weight: 600; color: {T['claim_text']}; line-height: 1.5; flex: 1; min-width: 180px; }}
.claim-explanation {{ font-size: 0.82rem; color: {T['claim_explanation']}; line-height: 1.65; margin-top: 0.4rem; }}
.before-after {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.75rem; }}
.before-box {{
    background: {T['before_bg']}; border: 1px solid {T['before_border']};
    border-radius: 10px; padding: 0.75rem;
}}
.after-box {{
    background: {T['after_bg']}; border: 1px solid {T['after_border']};
    border-radius: 10px; padding: 0.75rem;
}}
.ba-label {{ font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.3rem; }}
.before-box .ba-label {{ color: #ef4444; }}
.after-box .ba-label {{ color: #10b981; }}
.ba-text {{ font-size: 0.82rem; color: {T['ba_text']}; line-height: 1.5; }}
.ai-reasoning {{
    background: {T['ai_reason_bg']}; border: 1px solid {T['ai_reason_border']};
    border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.75rem;
}}
.ai-reasoning-label {{ font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; color: {T['ai_reason_label']}; margin-bottom: 0.3rem; }}
.ai-reasoning-text {{ font-size: 0.81rem; color: {T['ai_reason_text']}; line-height: 1.65; }}
.sources-list {{ margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.source-chip {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: {T['source_chip_bg']}; border: 1px solid {T['source_chip_border']};
    border-radius: 8px; padding: 0.25rem 0.65rem;
    font-size: 0.73rem; color: {T['source_chip_text']}; text-decoration: none; transition: background 0.15s;
}}
.source-chip:hover {{ background: {T['source_chip_hover']}; }}

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
.conf-track {{ flex: 1; background: {T['conf_track']}; border-radius: 100px; height: 6px; }}
.conf-fill {{ height: 6px; border-radius: 100px; }}
.conf-high {{ background: linear-gradient(90deg, #10b981, #34d399); }}
.conf-med {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
.conf-low {{ background: linear-gradient(90deg, #ef4444, #f87171); }}
.conf-pct {{ font-size: 0.76rem; font-weight: 700; min-width: 34px; }}

/* ── FEATURES GRID ── */
.features-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.25rem 0; }}
.feature-card {{
    background: {T['feature_card_bg']}; border: 1px solid {T['feature_card_border']};
    border-radius: 14px; padding: 1.4rem; transition: border-color 0.2s;
}}
.feature-card:hover {{ border-color: {T['feature_hover']}; }}
.feature-icon {{ font-size: 1.7rem; margin-bottom: 0.65rem; }}
.feature-title {{ font-weight: 700; color: {T['feature_title']}; font-size: 0.88rem; margin-bottom: 0.35rem; }}
.feature-desc {{ font-size: 0.78rem; color: {T['feature_desc']}; line-height: 1.65; }}

/* ── SAMPLE CARDS ── */
.sample-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }}
.sample-card {{
    background: {T['sample_card_bg']}; border: 1px solid {T['sample_card_border']};
    border-radius: 14px; padding: 1.25rem; text-align: center;
}}
.sample-title {{ font-weight: 700; color: {T['sample_title']}; font-size: 0.88rem; margin-bottom: 0.3rem; }}
.sample-desc {{ font-size: 0.77rem; color: {T['sample_desc']}; line-height: 1.55; }}

/* ── CHARTS ── */
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }}
.chart-card {{
    background: {T['chart_bg']}; border: 1px solid {T['chart_border']};
    border-radius: 14px; padding: 1.25rem;
}}
.chart-title {{ font-weight: 700; color: {T['chart_title']}; font-size: 0.87rem; margin-bottom: 1rem; }}
.donut-svg {{ width: 100%; max-width: 150px; display: block; margin: 0 auto; }}
.legend-item {{ display: flex; align-items: center; gap: 0.5rem; font-size: 0.77rem; color: {T['legend_text']}; margin-bottom: 0.35rem; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
.bar-row {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }}
.bar-label {{ font-size: 0.73rem; color: {T['bar_text']}; min-width: 80px; }}
.bar-track {{ flex: 1; background: {T['bar_track']}; border-radius: 100px; height: 10px; }}
.bar-val {{ font-size: 0.73rem; color: {T['bar_val']}; font-weight: 700; min-width: 28px; text-align: right; }}

/* ── SUSPICIOUS ── */
.suspicious-list {{ margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.suspicious-chip {{
    background: {T['susp_bg']}; border: 1px solid {T['susp_border']};
    color: #fb923c; border-radius: 6px; padding: 0.2rem 0.6rem; font-size: 0.73rem; font-weight: 600;
}}

/* ── UPLOAD ZONE ── */
.drop-zone {{
    border: 2px dashed {T['drop_zone_border']}; border-radius: 16px; padding: 2.5rem 2rem;
    text-align: center; background: {T['drop_zone_bg']}; margin: 0.5rem 0;
}}
.drop-title {{ font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.05rem; font-weight: 700; color: {T['drop_title']}; margin-bottom: 0.4rem; }}
.drop-sub {{ font-size: 0.8rem; color: {T['drop_sub']}; }}

/* ── ABOUT SECTION ── */
.about-section {{
    background: {T['about_bg']}; border: 1px solid {T['about_border']};
    border-radius: 20px; padding: 3rem 2.5rem; margin-top: 2rem;
    text-align: center; position: relative; overflow: hidden;
}}
.about-section::before {{
    content: ''; position: absolute; top: -30%; left: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
    border-radius: 50%; pointer-events: none;
}}
.about-story-label {{
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.18em;
    text-transform: uppercase; color: {T['about_story_label']}; margin-bottom: 0.75rem;
}}
.about-title {{
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 2rem; font-weight: 800; color: {T['about_title']}; margin-bottom: 0.5rem;
}}
.about-subtitle {{ font-size: 0.82rem; color: {T['text_muted']}; margin-bottom: 1.5rem; }}
.about-card {{
    background: {T['about_card_bg']}; border: 1px solid {T['about_card_border']};
    border-radius: 14px; padding: 1rem 1.25rem; max-width: 360px; margin: 0 auto 1.5rem auto;
}}
.about-cert-row {{
    display: flex; align-items: center; gap: 0.75rem;
    background: {T['about_cert_bg']}; border: 1px solid {T['about_cert_border']};
    border-radius: 10px; padding: 0.65rem 1rem; margin-bottom: 0.75rem;
}}
.about-cert-title {{ font-weight: 700; font-size: 0.85rem; color: {T['about_cert_title']}; }}
.about-cert-desc {{ font-size: 0.73rem; color: {T['about_cert_desc']}; margin-top: 0.1rem; }}
.about-text {{ font-size: 0.88rem; color: {T['about_text']}; line-height: 1.75; max-width: 520px; margin: 0 auto 1.75rem auto; }}
.about-btns {{ display: flex; justify-content: center; gap: 0.75rem; flex-wrap: wrap; }}
.about-btn-primary {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: {T['about_btn_primary']}; color: white;
    font-weight: 700; font-size: 0.85rem;
    padding: 0.65rem 1.5rem; border-radius: 10px; text-decoration: none;
    border: none; cursor: pointer; transition: all 0.2s;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3);
}}
.about-btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(99,102,241,0.45); }}
.about-btn-outline {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: {T['about_btn_outline']}; color: {T['about_btn_outline_text']};
    font-weight: 700; font-size: 0.85rem;
    padding: 0.65rem 1.5rem; border-radius: 10px; text-decoration: none;
    border: 1px solid {T['about_btn_outline_border']}; cursor: pointer; transition: all 0.2s;
}}
.about-btn-outline:hover {{ background: {T['source_chip_hover']}; }}

/* ── THEME TOGGLE ── */
.theme-toggle-btn {{
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: {T['about_btn_outline']}; border: 1px solid {T['about_btn_outline_border']};
    color: {T['text_secondary']}; font-size: 0.78rem; font-weight: 700;
    padding: 0.45rem 1rem; border-radius: 100px; cursor: pointer;
    transition: all 0.2s; width: 100%; justify-content: center;
    margin-top: 0.5rem;
}}

/* ── MISC ── */
.stProgress > div > div {{ background: linear-gradient(90deg, #6366f1, #8b5cf6) !important; }}
[data-testid="stFileUploader"] {{ background: {T['drop_zone_bg']} !important; border: 2px dashed {T['drop_zone_border']} !important; border-radius: 14px !important; }}
div[data-testid="stRadio"] {{ display: none !important; }}
hr {{ border-color: {T['hr_color']} !important; margin: 1.5rem 0 !important; }}
[data-testid="stDownloadButton"] > button {{
    background: rgba(16,185,129,0.12) !important; color: #10b981 !important;
    border: 1px solid rgba(16,185,129,0.3) !important; box-shadow: none !important;
}}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-logo">
        <div style="font-size:1.4rem">🛡️</div>
        <div>
            <div class="sidebar-logo-text">FactChecker AI</div>
            <div class="sidebar-logo-sub">Truth Layer for Your Content</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
    for icon, label in [("🏠","Home"),("📤","Upload PDF"),("✅","Fact Check"),("📊","Dashboard"),("🕐","History")]:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()

    st.markdown('<div class="sidebar-section">Appearance</div>', unsafe_allow_html=True)
    theme_label = f"{T['theme_icon']}  {T['theme_label']}"
    if st.button(theme_label, key="theme_toggle", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:{T['arch_bg']};border:1px solid {T['arch_border']};border-radius:12px;padding:1rem;font-size:0.73rem;color:{T['arch_text']};">
        <div style="color:{T['arch_title']};font-weight:700;margin-bottom:0.5rem;">⚙️ Architecture</div>
        PDF → LLM Claims<br>→ Web Search<br>→ Fact Validation<br>→ Report
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.results:
        r = st.session_state.results
        trust = r.get("trust_score", 70)
        risk = "🟢 Low" if trust >= 70 else "🟡 Medium" if trust >= 45 else "🔴 High"
        color = "#10b981" if trust >= 70 else "#f59e0b" if trust >= 45 else "#ef4444"
        st.markdown(f"""
        <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);border-radius:12px;padding:1rem;margin-top:0.75rem;text-align:center;">
            <div style="font-size:0.6rem;color:{T['text_muted']};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Trust Score</div>
            <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.8rem;font-weight:800;color:{color};">{trust}/100</div>
            <div style="font-size:0.75rem;color:{T['text_muted']};">{risk} Risk</div>
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
    txt_fill = T['text_primary']
    return f"""<svg viewBox="0 0 150 150" class="donut-svg">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(128,128,128,0.1)" stroke-width="16"/>
        {"".join(paths)}
        <text x="{cx}" y="{cy-6}" text-anchor="middle" fill="{txt_fill}" font-size="20" font-weight="800" font-family="Bricolage Grotesque,sans-serif">{total}</text>
        <text x="{cx}" y="{cy+12}" text-anchor="middle" fill="{T['text_muted']}" font-size="10">claims</text>
    </svg>"""

# ═══════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-badge">🛡️ AI-Powered Verification</div>
        <div class="hero-title">AI-Powered<br><span>Fact Checker</span></div>
        <p class="hero-sub">Upload a PDF and we'll find, verify & explain every factual claim using live web data and AI reasoning.</p>
        <ul class="hero-bullets">
            <li>Detect fake, outdated or misleading claims instantly</li>
            <li>Get correct facts with trusted, clickable source links</li>
            <li>Confidence scores and AI reasoning for every verdict</li>
            <li>Export clean, shareable fact-check reports</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:800;color:{T['text_primary']};margin-bottom:1rem;">How It Works</div>
    <div class="steps-row">
        <div class="step-card"><div class="step-num">STEP 01</div><div class="step-icon">📤</div><div class="step-title">Upload PDF</div><div class="step-desc">Upload any document — report, research, article, or marketing material.</div></div>
        <div class="step-card"><div class="step-num">STEP 02</div><div class="step-icon">🧠</div><div class="step-title">Extract Claims</div><div class="step-desc">AI detects all verifiable stats, dates, figures, and facts.</div></div>
        <div class="step-card"><div class="step-num">STEP 03</div><div class="step-icon">🌐</div><div class="step-title">Verify on Web</div><div class="step-desc">Each claim is cross-checked against live web sources.</div></div>
        <div class="step-card"><div class="step-num">STEP 04</div><div class="step-icon">📊</div><div class="step-title">Get Report</div><div class="step-desc">Receive verdicts, confidence scores, sources, and correct facts.</div></div>
    </div>
    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:800;color:{T['text_primary']};margin:1.75rem 0 1rem;">Features</div>
    <div class="features-grid">
        <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Confidence Scores</div><div class="feature-desc">Each verdict includes a 0–100% confidence score based on source agreement.</div></div>
        <div class="feature-card"><div class="feature-icon">🔗</div><div class="feature-title">Live Source Links</div><div class="feature-desc">Every claim links to the real web sources used for verification.</div></div>
        <div class="feature-card"><div class="feature-icon">🤖</div><div class="feature-title">AI Reasoning</div><div class="feature-desc">Understand why each claim is flagged with detailed AI explanation.</div></div>
        <div class="feature-card"><div class="feature-icon">🔄</div><div class="feature-title">Before vs After</div><div class="feature-desc">See the uploaded claim vs the correct updated fact side by side.</div></div>
        <div class="feature-card"><div class="feature-icon">🚨</div><div class="feature-title">Suspicious Language</div><div class="feature-desc">Detects exaggerated marketing claims like "world's best" or "#1".</div></div>
        <div class="feature-card"><div class="feature-icon">📥</div><div class="feature-title">Export Report</div><div class="feature-desc">Download your full fact-check results as a clean report.</div></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📤 Upload Your PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()
    with c2:
        if st.button("📊 View Dashboard"):
            st.session_state.page = "Dashboard"; st.rerun()

    # ── ABOUT PROJECT SECTION ──
    st.markdown(f"""
    <div class="about-section">
        <div class="about-story-label">THE STORY</div>
        <div class="about-title">About this project</div>
        <div class="about-subtitle">Built by a student, for everyone</div>

        <div class="about-card">
            <div class="about-cert-row">
                <div style="font-size:1.4rem;">🏅</div>
                <div>
                    <div class="about-cert-title">Anthropic AI Fluency Certificate</div>
                    <div class="about-cert-desc">Built as part of Anthropic's AI Fluency program</div>
                </div>
            </div>
        </div>

        <p class="about-text">
            FactChecker AI started as a college project exploring how large language models
            can make information more trustworthy. It grew into a real tool for
            anyone who wants to know if what they're reading is actually true —
            powered by Groq LLM and Tavily live search.
        </p>

        <div class="about-btns">
            <a class="about-btn-primary" onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'Upload PDF'}},'*')">
                ✦ Verify something now
            </a>
            <a class="about-btn-outline" href="https://github.com" target="_blank">
                ⌥ View on GitHub
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Invisible button to handle "Verify something now" click from about section
    col_hidden = st.columns([1,1,1])
    with col_hidden[1]:
        if st.button("✦ Start Verifying", key="about_cta"):
            st.session_state.page = "Upload PDF"; st.rerun()

# ═══════════════════════════════════════════════════════
# 📤 UPLOAD PDF
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Upload PDF":
    st.markdown(f'<div class="page-header"><div class="page-title">Upload Your PDF</div><div class="page-subtitle">Upload any document to start AI fact-checking.</div></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF (Max 50MB)", type="pdf", label_visibility="visible")

    if not uploaded_file:
        st.markdown(f"""
        <div class="drop-zone">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">☁️</div>
            <div class="drop-title">Drag & drop your PDF here</div>
            <div class="drop-sub" style="margin-top:0.3rem;">or use the uploader above · PDF · Max 50MB</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f'<div style="font-weight:700;color:{T["text_secondary"]};margin-bottom:0.75rem;font-size:0.93rem;">📋 Try Our Sample PDFs</div>', unsafe_allow_html=True)
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
                <div style="font-weight:700;color:{T['text_secondary']};">📄 {uploaded_file.name}</div>
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
        st.markdown(f'<div class="page-header"><div class="page-title">Fact Check</div></div>', unsafe_allow_html=True)
        st.warning("⚠️ No PDF uploaded. Please go to Upload PDF first.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"; st.rerun()

    elif st.session_state.results is None:
        st.markdown(f'<div class="page-header"><div class="page-title">Fact Check in Progress</div><div class="page-subtitle">Please wait while we extract and verify claims from your document.</div></div>', unsafe_allow_html=True)

        stepper = st.empty()
        def render_stepper(active):
            steps = [("📄","Reading PDF","Extracting text from document"),("🧠","Extracting Claims","AI identifying verifiable facts"),("🌐","Searching Web","Live web search for each claim"),("🔍","Verifying Facts","Cross-referencing sources"),("📊","Generating Report","Compiling your fact-check report")]
            html = '<div class="process-stepper">'
            for i,(icon,title,sub) in enumerate(steps):
                if i < active: state,color,show = "done","#10b981","✓"
                elif i == active: state,color,show = "active","#6366f1",icon
                else: state,color,show = "pending",T['text_dimmed2'],icon
                bg = "rgba(16,185,129,.1)" if state=="done" else "rgba(99,102,241,.1)" if state=="active" else T['bg_card']
                tc = "#10b981" if state=="done" else T['text_secondary'] if state=="active" else T['text_muted']
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
            status_txt.markdown(f'<div style="font-size:0.8rem;color:{T["text_muted"]};padding:0.4rem 0;">🔎 Verifying <b style="color:#818cf8">{i+1}</b> of <b>{len(claims)}</b>: <span style="color:{T["text_muted"]};font-style:italic;">{claim[:70]}...</span></div>', unsafe_allow_html=True)
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
            lines = [f"FactChecker AI — {r['filename']}",f"Date: {r['date']}",f"Trust Score: {trust}/100 ({risk_label})",f"Total: {r['total']} | Verified: {r['verified']} | Inaccurate: {r['inaccurate']} | False: {r['false']}","",f"AI Summary: {r.get('ai_summary','')}","","="*60,""]
            for i,(claim,res) in enumerate(r["claims"],1):
                lines += [f"{i}. [{res.get('verdict','?')}] {claim}",f"   Explanation: {res.get('explanation','')}",f"   Confidence: {res.get('confidence',0)}%"]
                if res.get("correct_fact"): lines.append(f"   Correct Fact: {res['correct_fact']}")
                if res.get("ai_reasoning"): lines.append(f"   AI Reasoning: {res['ai_reasoning']}")
                for s in res.get("sources",[])[:2]:
                    if s.get("url"): lines.append(f"   Source: {s['url']}")
                lines.append("")
            st.download_button("📥 Download Report", data="\n".join(lines), file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:Bricolage Grotesque,sans-serif;font-size:1.05rem;font-weight:800;color:{T["text_primary"]};margin-bottom:1rem;">📋 Detailed Results</div>', unsafe_allow_html=True)

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
    st.markdown(f'<div class="page-header"><div class="page-title">📊 Dashboard</div><div class="page-subtitle">Analytics and overview of your last fact check.</div></div>', unsafe_allow_html=True)

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
                <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid {T['hr_color']};">
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
    st.markdown(f'<div class="page-header"><div class="page-title">🕐 History</div><div class="page-subtitle">All your previously fact-checked documents.</div></div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown(f'<div style="text-align:center;padding:3rem;background:{T["bg_card"]};border:1px solid {T["border"]};border-radius:16px;"><div style="font-size:2.5rem;margin-bottom:1rem;">🕐</div><div style="font-weight:700;color:{T["text_secondary"]};margin-bottom:.5rem;">No history yet</div><div style="font-size:.83rem;color:{T["text_muted"]};">Your fact-check results will appear here after analyzing a PDF.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:.5rem 1.25rem;font-size:.66rem;font-weight:700;color:{T["text_muted"]};text-transform:uppercase;letter-spacing:.08em;"><div>Document</div><div>Total</div><div>✅</div><div>⚠️</div><div>❌</div><div>Date</div></div>', unsafe_allow_html=True)
        for h in reversed(st.session_state.history):
            trust = h.get("trust_score",70)
            tc = "#10b981" if trust>=70 else "#f59e0b" if trust>=45 else "#ef4444"
            st.markdown(f'<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:1rem 1.25rem;background:{T["bg_card"]};border:1px solid {T["border"]};border-radius:12px;margin-bottom:.5rem;align-items:center;"><div><div style="font-weight:600;color:{T["text_secondary"]};font-size:.87rem;">📄 {h["filename"]}</div><div style="font-size:.68rem;color:{T["text_muted"]};margin-top:.15rem;">Trust: <span style="color:{tc};font-weight:700;">{trust}/100</span></div></div><div style="font-weight:700;color:{T["text_secondary"]};">{h["total"]}</div><div style="color:#10b981;font-weight:700;">{h["verified"]}</div><div style="color:#f59e0b;font-weight:700;">{h["inaccurate"]}</div><div style="color:#ef4444;font-weight:700;">{h["false"]}</div><div style="font-size:.76rem;color:{T["text_muted"]};">{h["date"]}</div></div>', unsafe_allow_html=True)
