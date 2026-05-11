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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Bricolage+Grotesque:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #0a0e1a !important;
    color: #e2e8f0 !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1080px !important;
}

@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 2rem 0.75rem !important; }
    .metrics-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .steps-row { grid-template-columns: repeat(2, 1fr) !important; }
    .features-grid { grid-template-columns: 1fr !important; }
    .hero-title { font-size: 2rem !important; }
    .charts-row { grid-template-columns: 1fr !important; }
    .before-after { grid-template-columns: 1fr !important; }
    .sample-grid { grid-template-columns: 1fr !important; }
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #0d1224 !important;
    border-right: 1px solid #1e2a45 !important;
}
section[data-testid="stSidebar"] > div { padding: 1.25rem 0.75rem !important; }

.sidebar-logo {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0.75rem 1.25rem 0.75rem;
    border-bottom: 1px solid #1e2a45; margin-bottom: 1rem;
}
.sidebar-logo-text {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.05rem; font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sidebar-logo-sub { font-size: 0.62rem; color: #4a5568; }
.sidebar-section {
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: #2d3748;
    padding: 0 0.75rem; margin: 1rem 0 0.4rem 0;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    font-size: 0.88rem !important; width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

/* ── CARDS ── */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
}

/* ── METRICS ── */
.metrics-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 1.25rem; text-align: center;
}
.metric-num {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 2.2rem; font-weight: 800; line-height: 1;
}
.metric-label { font-size: 0.73rem; color: #64748b; margin-top: 0.3rem; font-weight: 500; }
.metric-total .metric-num { color: #e2e8f0; }
.metric-verified .metric-num { color: #10b981; }
.metric-inaccurate .metric-num { color: #f59e0b; }
.metric-false .metric-num { color: #ef4444; }

/* ── PAGE HEADER ── */
.page-header { margin-bottom: 1.75rem; }
.page-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.6rem; font-weight: 800; color: #f1f5f9; margin-bottom: 0.25rem;
}
.page-subtitle { color: #64748b; font-size: 0.86rem; }

/* ── HERO ── */
.hero-section {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px; padding: 3rem 2.5rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
}
.hero-section::before {
    content: ''; position: absolute; top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4);
    color: #a5b4fc; font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.3em 1em; border-radius: 100px; margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 3rem; font-weight: 800; line-height: 1.1;
    color: #f1f5f9; margin-bottom: 0.75rem;
}
.hero-title span {
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { font-size: 0.97rem; color: #94a3b8; max-width: 480px; line-height: 1.75; margin-bottom: 1.5rem; }
.hero-bullets { list-style: none; display: flex; flex-direction: column; gap: 0.4rem; }
.hero-bullets li { font-size: 0.85rem; color: #a5b4fc; }
.hero-bullets li::before { content: '✦ '; color: #818cf8; }

/* ── STEPS ── */
.steps-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }
.step-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.4rem 1rem; text-align: center; transition: border-color 0.2s;
}
.step-card:hover { border-color: rgba(99,102,241,0.4); }
.step-num {
    font-size: 0.62rem; font-weight: 800; letter-spacing: 0.1em;
    color: #818cf8; background: rgba(99,102,241,0.15);
    border-radius: 100px; display: inline-block; padding: 0.2em 0.75em; margin-bottom: 0.75rem;
}
.step-icon { font-size: 1.7rem; margin-bottom: 0.5rem; }
.step-title { font-weight: 700; color: #e2e8f0; font-size: 0.87rem; margin-bottom: 0.3rem; }
.step-desc { font-size: 0.77rem; color: #64748b; line-height: 1.6; }

/* ── PROCESSING STEPPER ── */
.process-stepper {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 1.5rem; margin: 1rem 0;
}
.process-step {
    display: flex; align-items: center; gap: 1rem;
    padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.process-step:last-child { border-bottom: none; }
.step-indicator {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.step-indicator.active { animation: pulse 1.5s infinite; }
.step-text-title { font-weight: 600; font-size: 0.87rem; color: #e2e8f0; }
.step-text-sub { font-size: 0.73rem; color: #64748b; margin-top: 0.1rem; }

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
    50% { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
}

/* ── TRUST SCORE ── */
.trust-score-card {
    background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(99,102,241,0.08));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px; padding: 1.5rem; text-align: center; margin-bottom: 0;
    height: 100%;
}
.trust-score-num {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 3.5rem; font-weight: 800;
    background: linear-gradient(135deg, #10b981, #6366f1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.risk-badge {
    display: inline-block; padding: 0.3em 1em; border-radius: 100px;
    font-size: 0.73rem; font-weight: 700; margin-top: 0.75rem;
}
.risk-low { background: rgba(16,185,129,0.15); color: #10b981; }
.risk-med { background: rgba(245,158,11,0.15); color: #f59e0b; }
.risk-high { background: rgba(239,68,68,0.15); color: #ef4444; }

/* ── AI SUMMARY ── */
.ai-summary {
    background: rgba(99,102,241,0.07); border: 1px solid rgba(99,102,241,0.2);
    border-left: 4px solid #6366f1; border-radius: 12px;
    padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
}
.ai-summary-label {
    font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #818cf8; margin-bottom: 0.5rem;
}
.ai-summary-text { font-size: 0.9rem; color: #c7d2fe; line-height: 1.75; }

/* ── CLAIM CARDS ── */
.claim-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
    border-left: 4px solid rgba(255,255,255,0.1); transition: background 0.2s;
}
.claim-card:hover { background: rgba(255,255,255,0.05); }
.claim-card.verified { border-left-color: #10b981; }
.claim-card.inaccurate { border-left-color: #f59e0b; }
.claim-card.false { border-left-color: #ef4444; }
.claim-card.noevidence { border-left-color: #64748b; }

.claim-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 1rem; margin-bottom: 0.6rem; flex-wrap: wrap;
}
.claim-text { font-size: 0.92rem; font-weight: 600; color: #e2e8f0; line-height: 1.5; flex: 1; min-width: 180px; }
.claim-explanation { font-size: 0.82rem; color: #94a3b8; line-height: 1.65; margin-top: 0.4rem; }

.before-after { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.75rem; }
.before-box {
    background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15);
    border-radius: 10px; padding: 0.75rem;
}
.after-box {
    background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15);
    border-radius: 10px; padding: 0.75rem;
}
.ba-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.3rem; }
.before-box .ba-label { color: #ef4444; }
.after-box .ba-label { color: #10b981; }
.ba-text { font-size: 0.82rem; color: #cbd5e1; line-height: 1.5; }

.ai-reasoning {
    background: rgba(139,92,246,0.06); border: 1px solid rgba(139,92,246,0.15);
    border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.75rem;
}
.ai-reasoning-label { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; color: #a78bfa; margin-bottom: 0.3rem; }
.ai-reasoning-text { font-size: 0.81rem; color: #c4b5fd; line-height: 1.65; }

.sources-list { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
.source-chip {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; padding: 0.25rem 0.65rem;
    font-size: 0.73rem; color: #818cf8; text-decoration: none; transition: background 0.15s;
}
.source-chip:hover { background: rgba(99,102,241,0.15); }

/* ── BADGES ── */
.badge {
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
    text-transform: uppercase; padding: 0.25em 0.8em; border-radius: 100px; white-space: nowrap;
}
.badge-verified { background: rgba(16,185,129,0.15); color: #10b981; }
.badge-inaccurate { background: rgba(245,158,11,0.15); color: #f59e0b; }
.badge-false { background: rgba(239,68,68,0.15); color: #ef4444; }
.badge-noevidence { background: rgba(100,116,139,0.15); color: #94a3b8; }

/* ── CONFIDENCE BAR ── */
.conf-wrap { margin-top: 0.6rem; display: flex; align-items: center; gap: 0.75rem; }
.conf-label { font-size: 0.73rem; color: #64748b; white-space: nowrap; min-width: 78px; }
.conf-track { flex: 1; background: rgba(255,255,255,0.06); border-radius: 100px; height: 6px; }
.conf-fill { height: 6px; border-radius: 100px; }
.conf-high { background: linear-gradient(90deg, #10b981, #34d399); }
.conf-med { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.conf-low { background: linear-gradient(90deg, #ef4444, #f87171); }
.conf-pct { font-size: 0.76rem; font-weight: 700; min-width: 34px; }

/* ── FEATURES GRID ── */
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.25rem 0; }
.feature-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.4rem; transition: border-color 0.2s;
}
.feature-card:hover { border-color: rgba(99,102,241,0.3); }
.feature-icon { font-size: 1.7rem; margin-bottom: 0.65rem; }
.feature-title { font-weight: 700; color: #e2e8f0; font-size: 0.88rem; margin-bottom: 0.35rem; }
.feature-desc { font-size: 0.78rem; color: #64748b; line-height: 1.65; }

/* ── SAMPLE CARDS ── */
.sample-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }
.sample-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.25rem; text-align: center;
}
.sample-title { font-weight: 700; color: #e2e8f0; font-size: 0.88rem; margin-bottom: 0.3rem; }
.sample-desc { font-size: 0.77rem; color: #64748b; line-height: 1.55; }

/* ── CHARTS ── */
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }
.chart-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.25rem;
}
.chart-title { font-weight: 700; color: #e2e8f0; font-size: 0.87rem; margin-bottom: 1rem; }
.donut-svg { width: 100%; max-width: 150px; display: block; margin: 0 auto; }
.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.77rem; color: #94a3b8; margin-bottom: 0.35rem; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
.bar-label { font-size: 0.73rem; color: #94a3b8; min-width: 80px; }
.bar-track { flex: 1; background: rgba(255,255,255,0.06); border-radius: 100px; height: 10px; }
.bar-val { font-size: 0.73rem; color: #e2e8f0; font-weight: 700; min-width: 28px; text-align: right; }

/* ── SUSPICIOUS ── */
.suspicious-list { margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
.suspicious-chip {
    background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.25);
    color: #fb923c; border-radius: 6px; padding: 0.2rem 0.6rem; font-size: 0.73rem; font-weight: 600;
}

/* ── UPLOAD ZONE ── */
.drop-zone {
    border: 2px dashed rgba(99,102,241,0.3); border-radius: 16px; padding: 2.5rem 2rem;
    text-align: center; background: rgba(99,102,241,0.04); margin: 0.5rem 0;
}
.drop-title { font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.05rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.4rem; }
.drop-sub { font-size: 0.8rem; color: #4a5568; }

/* ── MISC ── */
.stProgress > div > div { background: linear-gradient(90deg, #6366f1, #8b5cf6) !important; }
.stSuccess { background: rgba(16,185,129,0.1) !important; border-color: rgba(16,185,129,0.3) !important; color: #6ee7b7 !important; border-radius: 10px !important; }
.stWarning { background: rgba(245,158,11,0.1) !important; border-color: rgba(245,158,11,0.3) !important; color: #fcd34d !important; border-radius: 10px !important; }
.stInfo { background: rgba(99,102,241,0.1) !important; border-color: rgba(99,102,241,0.3) !important; border-radius: 10px !important; }
[data-testid="stFileUploader"] { background: rgba(99,102,241,0.04) !important; border: 2px dashed rgba(99,102,241,0.3) !important; border-radius: 14px !important; }
div[data-testid="stRadio"] { display: none !important; }
hr { border-color: rgba(255,255,255,0.06) !important; margin: 1.5rem 0 !important; }
[data-testid="stDownloadButton"] > button {
    background: rgba(16,185,129,0.12) !important; color: #10b981 !important;
    border: 1px solid rgba(16,185,129,0.3) !important; box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.15);border-radius:12px;padding:1rem;font-size:0.73rem;color:#64748b;">
        <div style="color:#a5b4fc;font-weight:700;margin-bottom:0.5rem;">⚙️ Architecture</div>
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
            <div style="font-size:0.6rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Trust Score</div>
            <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.8rem;font-weight:800;color:{color};">{trust}/100</div>
            <div style="font-size:0.75rem;color:#64748b;">{risk} Risk</div>
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
    return f"""<svg viewBox="0 0 150 150" class="donut-svg">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="16"/>
        {"".join(paths)}
        <text x="{cx}" y="{cy-6}" text-anchor="middle" fill="#f1f5f9" font-size="20" font-weight="800" font-family="Bricolage Grotesque,sans-serif">{total}</text>
        <text x="{cx}" y="{cy+12}" text-anchor="middle" fill="#64748b" font-size="10">claims</text>
    </svg>"""

# ═══════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.markdown("""
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

    st.markdown("""
    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:800;color:#f1f5f9;margin-bottom:1rem;">How It Works</div>
    <div class="steps-row">
        <div class="step-card"><div class="step-num">STEP 01</div><div class="step-icon">📤</div><div class="step-title">Upload PDF</div><div class="step-desc">Upload any document — report, research, article, or marketing material.</div></div>
        <div class="step-card"><div class="step-num">STEP 02</div><div class="step-icon">🧠</div><div class="step-title">Extract Claims</div><div class="step-desc">AI detects all verifiable stats, dates, figures, and facts.</div></div>
        <div class="step-card"><div class="step-num">STEP 03</div><div class="step-icon">🌐</div><div class="step-title">Verify on Web</div><div class="step-desc">Each claim is cross-checked against live web sources.</div></div>
        <div class="step-card"><div class="step-num">STEP 04</div><div class="step-icon">📊</div><div class="step-title">Get Report</div><div class="step-desc">Receive verdicts, confidence scores, sources, and correct facts.</div></div>
    </div>
    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:800;color:#f1f5f9;margin:1.75rem 0 1rem;">Features</div>
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
        st.markdown('<div style="font-weight:700;color:#e2e8f0;margin-bottom:0.75rem;font-size:0.93rem;">📋 Try Our Sample PDFs</div>', unsafe_allow_html=True)
        st.markdown("""
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
                <div style="font-weight:700;color:#e2e8f0;">📄 {uploaded_file.name}</div>
                <div style="font-size:0.76rem;color:#64748b;margin-top:0.2rem;">Size: {file_size:.1f} KB · PDF Document</div>
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
                tc = "#10b981" if state=="done" else "#e2e8f0" if state=="active" else "#4a5568"
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
            status_txt.markdown(f'<div style="font-size:0.8rem;color:#64748b;padding:0.4rem 0;">🔎 Verifying <b style="color:#818cf8">{i+1}</b> of <b>{len(claims)}</b>: <span style="color:#94a3b8;font-style:italic;">{claim[:70]}...</span></div>', unsafe_allow_html=True)
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
                <div style="font-size:0.65rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem;">Trust Score</div>
                <div class="trust-score-num">{trust}</div>
                <div style="font-size:0.65rem;color:#64748b;">/100</div>
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
        st.markdown('<div style="font-family:Bricolage Grotesque,sans-serif;font-size:1.05rem;font-weight:800;color:#f1f5f9;margin-bottom:1rem;">📋 Detailed Results</div>', unsafe_allow_html=True)

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
                <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.06);">
                    <div style="font-size:0.72rem;color:#64748b;margin-bottom:0.3rem;">Trust Score</div>
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
        st.markdown('<div style="text-align:center;padding:3rem;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:16px;"><div style="font-size:2.5rem;margin-bottom:1rem;">🕐</div><div style="font-weight:700;color:#e2e8f0;margin-bottom:.5rem;">No history yet</div><div style="font-size:.83rem;color:#4a5568;">Your fact-check results will appear here after analyzing a PDF.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:.5rem 1.25rem;font-size:.66rem;font-weight:700;color:#4a5568;text-transform:uppercase;letter-spacing:.08em;"><div>Document</div><div>Total</div><div>✅</div><div>⚠️</div><div>❌</div><div>Date</div></div>', unsafe_allow_html=True)
        for h in reversed(st.session_state.history):
            trust = h.get("trust_score",70)
            tc = "#10b981" if trust>=70 else "#f59e0b" if trust>=45 else "#ef4444"
            st.markdown(f'<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:1rem 1.25rem;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;margin-bottom:.5rem;align-items:center;"><div><div style="font-weight:600;color:#e2e8f0;font-size:.87rem;">📄 {h["filename"]}</div><div style="font-size:.68rem;color:#4a5568;margin-top:.15rem;">Trust: <span style="color:{tc};font-weight:700;">{trust}/100</span></div></div><div style="font-weight:700;color:#e2e8f0;">{h["total"]}</div><div style="color:#10b981;font-weight:700;">{h["verified"]}</div><div style="color:#f59e0b;font-weight:700;">{h["inaccurate"]}</div><div style="color:#ef4444;font-weight:700;">{h["false"]}</div><div style="font-size:.76rem;color:#4a5568;">{h["date"]}</div></div>', unsafe_allow_html=True)
