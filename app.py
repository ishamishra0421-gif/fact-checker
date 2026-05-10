import streamlit as st
import pdfplumber
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
import time
import random
from groq import Groq
from datetime import datetime
import io

# ─── PAGE CONFIG ───────────────────────────────────────
st.set_page_config(page_title="FactChecker", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# ─── LOAD API KEYS ─────────────────────────────────────
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── SESSION STATE ─────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "results" not in st.session_state:
    st.session_state.results = None
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ─── CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Bricolage+Grotesque:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: #f4f6fb !important;
    color: #1a1d2e !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Main layout */
.block-container {
    padding: 2rem 2.5rem 3rem 2.5rem !important;
    max-width: 1100px !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e8ecf4 !important;
    width: 230px !important;
}
section[data-testid="stSidebar"] > div { padding: 1.5rem 1rem !important; }

.sidebar-logo {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0.75rem 1.5rem 0.75rem;
    border-bottom: 1px solid #e8ecf4;
    margin-bottom: 1.2rem;
}
.sidebar-logo-icon { font-size: 1.5rem; }
.sidebar-logo-text {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.1rem; font-weight: 700; color: #1a1d2e;
}
.sidebar-logo-sub { font-size: 0.65rem; color: #8b95a8; font-weight: 400; }

.sidebar-section {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #b0b9c8;
    padding: 0 0.75rem; margin: 1.2rem 0 0.5rem 0;
}

.nav-item {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.6rem 0.75rem; border-radius: 10px;
    font-size: 0.88rem; font-weight: 500; color: #4a5568;
    cursor: pointer; transition: all 0.15s; margin-bottom: 0.15rem;
    text-decoration: none;
}
.nav-item:hover { background: #f4f6fb; color: #1a1d2e; }
.nav-item.active { background: #eef2ff; color: #4f46e5; font-weight: 600; }
.nav-item .icon { font-size: 1rem; width: 1.2rem; text-align: center; }

/* ── CARDS ── */
.card {
    background: #ffffff;
    border: 1px solid #e8ecf4;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── PAGE HEADER ── */
.page-header { margin-bottom: 2rem; }
.page-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.75rem; font-weight: 800; color: #1a1d2e;
    margin-bottom: 0.3rem;
}
.page-subtitle { color: #6b7280; font-size: 0.92rem; }

/* ── METRIC CARDS ── */
.metrics-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;
}
.metric-card {
    background: #ffffff; border: 1px solid #e8ecf4; border-radius: 14px;
    padding: 1.25rem 1rem; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.metric-num {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 2.2rem; font-weight: 800; line-height: 1;
}
.metric-label { font-size: 0.78rem; color: #8b95a8; margin-top: 0.3rem; font-weight: 500; }
.metric-total .metric-num { color: #1a1d2e; }
.metric-verified .metric-num { color: #059669; }
.metric-inaccurate .metric-num { color: #d97706; }
.metric-false .metric-num { color: #dc2626; }

/* ── VERDICT BADGES ── */
.badge {
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 0.25em 0.75em; border-radius: 100px;
}
.badge-verified { background: #d1fae5; color: #065f46; }
.badge-inaccurate { background: #fef3c7; color: #92400e; }
.badge-false { background: #fee2e2; color: #991b1b; }
.badge-noevidence { background: #f3f4f6; color: #4b5563; }

/* ── CLAIM CARDS ── */
.claim-card {
    background: #ffffff; border: 1px solid #e8ecf4; border-radius: 14px;
    padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
    border-left: 4px solid #e8ecf4;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    transition: box-shadow 0.2s;
}
.claim-card.verified { border-left-color: #059669; }
.claim-card.inaccurate { border-left-color: #d97706; }
.claim-card.false { border-left-color: #dc2626; }
.claim-card.noevidence { border-left-color: #9ca3af; }

.claim-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.6rem; }
.claim-text { font-size: 0.95rem; font-weight: 500; color: #1a1d2e; line-height: 1.5; flex: 1; }
.claim-explanation { font-size: 0.85rem; color: #6b7280; line-height: 1.6; margin-top: 0.4rem; }

.correct-fact {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px;
    padding: 0.6rem 1rem; margin-top: 0.75rem;
    font-size: 0.85rem; color: #1e40af;
}
.correct-fact-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.2rem; color: #3b82f6; }

.sources-list { margin-top: 0.6rem; }
.source-link {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #f9fafb; border: 1px solid #e5e7eb;
    border-radius: 6px; padding: 0.25rem 0.6rem;
    font-size: 0.78rem; color: #4f46e5; text-decoration: none;
    margin-right: 0.4rem; margin-top: 0.3rem;
}

.confidence-bar-wrap { margin-top: 0.5rem; }
.confidence-label { font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.2rem; }
.confidence-bar-bg { background: #f3f4f6; border-radius: 100px; height: 5px; width: 120px; }
.confidence-bar-fill { height: 5px; border-radius: 100px; }
.conf-high { background: #059669; }
.conf-med { background: #d97706; }
.conf-low { background: #dc2626; }

/* ── STEPS (HOW IT WORKS) ── */
.steps-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }
.step-card {
    background: #fff; border: 1px solid #e8ecf4; border-radius: 14px;
    padding: 1.5rem 1.2rem; text-align: center;
}
.step-num {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 0.7rem; font-weight: 800; letter-spacing: 0.1em;
    color: #4f46e5; background: #eef2ff; border-radius: 100px;
    display: inline-block; padding: 0.2em 0.75em; margin-bottom: 0.75rem;
}
.step-icon { font-size: 1.75rem; margin-bottom: 0.5rem; }
.step-title { font-weight: 700; color: #1a1d2e; font-size: 0.9rem; margin-bottom: 0.3rem; }
.step-desc { font-size: 0.8rem; color: #6b7280; line-height: 1.6; }

/* ── HERO ── */
.hero-section {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    border-radius: 20px; padding: 3rem 2.5rem; color: white;
    margin-bottom: 2rem; position: relative; overflow: hidden;
}
.hero-section::after {
    content: '🛡️'; font-size: 8rem; position: absolute; right: 2rem; top: 50%;
    transform: translateY(-50%); opacity: 0.15;
}
.hero-badge {
    display: inline-block; background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    color: white; font-size: 0.75rem; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.3em 1em; border-radius: 100px; margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 2.8rem; font-weight: 800; line-height: 1.1;
    margin-bottom: 0.75rem;
}
.hero-sub { font-size: 1rem; opacity: 0.85; max-width: 480px; line-height: 1.7; margin-bottom: 1.5rem; }
.hero-bullets { list-style: none; display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0; }
.hero-bullets li { font-size: 0.88rem; opacity: 0.9; }
.hero-bullets li::before { content: '✓ '; font-weight: 700; }

/* ── FEATURE CARDS ── */
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.5rem 0; }
.feature-card {
    background: #fff; border: 1px solid #e8ecf4; border-radius: 14px;
    padding: 1.5rem; transition: box-shadow 0.2s;
}
.feature-card:hover { box-shadow: 0 4px 16px rgba(79,70,229,0.08); }
.feature-icon { font-size: 1.8rem; margin-bottom: 0.75rem; }
.feature-title { font-weight: 700; color: #1a1d2e; font-size: 0.95rem; margin-bottom: 0.4rem; }
.feature-desc { font-size: 0.83rem; color: #6b7280; line-height: 1.6; }

/* ── HISTORY TABLE ── */
.history-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 1.25rem; background: #fff; border: 1px solid #e8ecf4;
    border-radius: 12px; margin-bottom: 0.5rem;
}
.history-doc { font-weight: 600; color: #1a1d2e; font-size: 0.9rem; }
.history-date { font-size: 0.78rem; color: #9ca3af; margin-top: 0.2rem; }
.history-badges { display: flex; gap: 0.4rem; align-items: center; }

/* ── UPLOAD DROP ZONE ── */
.drop-zone {
    border: 2px dashed #c7d2fe; border-radius: 16px; padding: 3rem 2rem;
    text-align: center; background: #fafbff; margin: 1rem 0;
}
.drop-icon { font-size: 3rem; margin-bottom: 1rem; }
.drop-title { font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.2rem; font-weight: 700; color: #374151; margin-bottom: 0.5rem; }
.drop-sub { font-size: 0.85rem; color: #9ca3af; }

/* ── SAMPLE PDF CARDS ── */
.sample-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; }
.sample-card {
    background: #fff; border: 1px solid #e8ecf4; border-radius: 14px;
    padding: 1.25rem; text-align: center;
}
.sample-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.sample-title { font-weight: 700; color: #1a1d2e; font-size: 0.95rem; margin-bottom: 0.3rem; }
.sample-desc { font-size: 0.8rem; color: #6b7280; line-height: 1.5; }

/* ── PROGRESS STEPS ── */
.progress-steps { display: flex; gap: 0; margin: 1.5rem 0; }
.progress-step {
    flex: 1; text-align: center; font-size: 0.78rem; font-weight: 600;
    padding: 0.6rem 0.5rem; border-top: 3px solid #e5e7eb;
    color: #9ca3af;
}
.progress-step.done { border-top-color: #059669; color: #059669; }
.progress-step.active { border-top-color: #4f46e5; color: #4f46e5; }

/* ── BUTTONS ── */
.stButton > button {
    background: #4f46e5 !important; color: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 10px !important; padding: 0.65rem 1.75rem !important;
    font-size: 0.92rem !important; transition: all 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover { background: #4338ca !important; box-shadow: 0 4px 14px rgba(79,70,229,0.3) !important; }

.stProgress > div > div { background: #4f46e5 !important; }
.stSuccess { background: #d1fae5 !important; border-color: #6ee7b7 !important; color: #065f46 !important; border-radius: 10px !important; }
.stWarning { background: #fef3c7 !important; border-color: #fcd34d !important; color: #92400e !important; border-radius: 10px !important; }

hr { border-color: #e8ecf4 !important; margin: 1.5rem 0 !important; }

/* stFileUploader */
[data-testid="stFileUploader"] {
    background: #fafbff !important; border: 2px dashed #c7d2fe !important;
    border-radius: 16px !important; padding: 1.5rem !important;
}

/* Radio nav hidden */
div[data-testid="stRadio"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🛡️</div>
        <div>
            <div class="sidebar-logo-text">FactChecker</div>
            <div class="sidebar-logo-sub">Truth Layer for Your Content</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Main</div>', unsafe_allow_html=True)
    pages = [
        ("🏠", "Home"),
        ("📤", "Upload PDF"),
        ("✅", "Fact Check"),
        ("📊", "Dashboard"),
        ("🕐", "History"),
    ]
    for icon, label in pages:
        active = "active" if st.session_state.page == label else ""
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()

    st.markdown('<div class="sidebar-section">Resources</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">📄  Sample PDFs</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">⚙️  Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">ℹ️  About</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0.75rem; background:#f4f6fb; border-radius:12px; font-size:0.78rem; color:#6b7280;">
        <b style="color:#1a1d2e;">Architecture</b><br><br>
        PDF → LLM Claims → Web Search → Fact Validation → Report
    </div>
    """, unsafe_allow_html=True)

# ─── HELPERS ───────────────────────────────────────────
def extract_text(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

def extract_claims(text):
    prompt = f"""Extract all specific verifiable factual claims from this text.
Focus ONLY on: statistics, percentages, dates, revenue figures, user counts, technical facts, market sizes.
Examples of good claims: "India has 950M internet users", "OpenAI reached 100M users in 2023", "WHO reported 2B diabetes cases".
Return ONLY a JSON list: ["claim 1", "claim 2"]
No extra text. No markdown. Just the JSON list.
Text: {text[:4000]}"""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    return json.loads(clean)

def verify_claim(claim):
    results = tavily.search(claim, max_results=4)
    sources = [{"title": r.get("title",""), "url": r.get("url",""), "date": r.get("published_date","")} for r in results.get("results", [])]
    prompt = f"""Claim: "{claim}"
Web results: {results['results']}
Classify this claim as VERIFIED, INACCURATE, or FALSE, or NO_EVIDENCE.
- VERIFIED: claim matches current evidence
- INACCURATE: claim is partially wrong or outdated
- FALSE: claim is clearly wrong
- NO_EVIDENCE: cannot determine

Reply ONLY with this JSON (no markdown):
{{"verdict": "VERIFIED or INACCURATE or FALSE or NO_EVIDENCE", "explanation": "one clear sentence", "correct_fact": "the real/updated fact if wrong, else empty string", "confidence": 85}}

confidence is an integer 0-100 based on how many sources agree."""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    data = json.loads(clean)
    data["sources"] = sources
    return data

def verdict_badge(verdict):
    badges = {
        "VERIFIED": '<span class="badge badge-verified">✅ Verified</span>',
        "INACCURATE": '<span class="badge badge-inaccurate">⚠️ Inaccurate</span>',
        "FALSE": '<span class="badge badge-false">❌ False</span>',
        "NO_EVIDENCE": '<span class="badge badge-noevidence">❓ No Evidence</span>',
    }
    return badges.get(verdict, badges["NO_EVIDENCE"])

def css_class(verdict):
    return {"VERIFIED":"verified","INACCURATE":"inaccurate","FALSE":"false","NO_EVIDENCE":"noevidence"}.get(verdict,"noevidence")

def confidence_html(score):
    score = int(score) if score else 50
    cls = "conf-high" if score >= 75 else "conf-med" if score >= 50 else "conf-low"
    color = "#059669" if score >= 75 else "#d97706" if score >= 50 else "#dc2626"
    return f"""<div class="confidence-bar-wrap">
        <div class="confidence-label">Confidence: <b style="color:{color}">{score}%</b></div>
        <div class="confidence-bar-bg"><div class="confidence-bar-fill {cls}" style="width:{score}%"></div></div>
    </div>"""

# ═══════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.markdown("""
    <div class="hero-section">
        <div class="hero-badge">🛡️ AI-Powered Verification</div>
        <div class="hero-title">AI-Powered<br>Fact Checker</div>
        <p class="hero-sub">Upload a PDF and we'll find, verify & explain the facts using live web data.</p>
        <ul class="hero-bullets">
            <li>Detect fake, outdated or misleading claims</li>
            <li>Get correct facts with trusted sources</li>
            <li>Export clean, shareable fact check reports</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="page-title" style="font-size:1.3rem; margin-bottom:1rem;">How It Works</div>
    <div class="steps-row">
        <div class="step-card">
            <div class="step-num">STEP 01</div>
            <div class="step-icon">📤</div>
            <div class="step-title">Upload PDF</div>
            <div class="step-desc">Upload any document — report, research paper, or article.</div>
        </div>
        <div class="step-card">
            <div class="step-num">STEP 02</div>
            <div class="step-icon">🧠</div>
            <div class="step-title">Extract Claims</div>
            <div class="step-desc">AI detects all verifiable stats, dates, and figures.</div>
        </div>
        <div class="step-card">
            <div class="step-num">STEP 03</div>
            <div class="step-icon">🌐</div>
            <div class="step-title">Verify on Web</div>
            <div class="step-desc">Each claim is cross-checked against live web sources.</div>
        </div>
        <div class="step-card">
            <div class="step-num">STEP 04</div>
            <div class="step-icon">📊</div>
            <div class="step-title">Get Report</div>
            <div class="step-desc">Receive a detailed report with verdicts and sources.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-title" style="font-size:1.3rem; margin:1.5rem 0 1rem;">Features</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="features-grid">
        <div class="feature-card"><div class="feature-icon">📄</div><div class="feature-title">Smart Claim Extraction</div><div class="feature-desc">Automatically finds every statistic, date, figure, and verifiable claim in your document.</div></div>
        <div class="feature-card"><div class="feature-icon">🌐</div><div class="feature-title">Live Web Verification</div><div class="feature-desc">Cross-references each claim against real-time web data using Tavily search.</div></div>
        <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Confidence Scores</div><div class="feature-desc">Each verdict comes with a confidence score based on how many sources agree.</div></div>
        <div class="feature-card"><div class="feature-icon">🔗</div><div class="feature-title">Source Links</div><div class="feature-desc">Every result links to the real sources used for verification.</div></div>
        <div class="feature-card"><div class="feature-icon">📥</div><div class="feature-title">Export Report</div><div class="feature-desc">Download your fact-check results as a clean text report.</div></div>
        <div class="feature-card"><div class="feature-icon">🕐</div><div class="feature-title">History</div><div class="feature-desc">All your past fact checks are saved for easy reference and comparison.</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Upload Your PDF", key="home_upload"):
            st.session_state.page = "Upload PDF"
            st.rerun()
    with col2:
        if st.button("🎯 Try Demo PDF", key="home_demo"):
            st.session_state.page = "Upload PDF"
            st.rerun()

# ═══════════════════════════════════════════════════════
# 📤 UPLOAD PDF
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Upload PDF":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Upload Your PDF</div>
        <div class="page-subtitle">Upload a marketing report, research paper, or any document to get started.</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if not uploaded_file:
        st.markdown("""
        <div class="drop-zone">
            <div class="drop-icon">☁️</div>
            <div class="drop-title">Drag & drop your PDF here</div>
            <div class="drop-sub" style="margin-top:0.25rem; color:#6b7280;">or use the uploader above</div>
            <div class="drop-sub" style="margin-top:0.5rem;">Supported format: PDF (Max size: 50MB)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700; color:#1a1d2e; margin-bottom:0.75rem;">Try Our Sample PDFs</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="sample-grid">
            <div class="sample-card">
                <div class="sample-icon">📋</div>
                <div class="sample-title">Demo PDF (Real Facts)</div>
                <div class="sample-desc">Contains real claims and verifiable data to test the tool.</div>
            </div>
            <div class="sample-card">
                <div class="sample-icon">⚠️</div>
                <div class="sample-title">Trap PDF (Fake & Outdated)</div>
                <div class="sample-desc">Contains intentional fake and outdated statistics.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("🔒 Your data is secure and will only be used for fact checking.")
    else:
        st.success(f"✅ **{uploaded_file.name}** ready for fact checking")
        st.session_state.uploaded_file = uploaded_file

        if st.button("🚀 Start Fact Checking"):
            st.session_state.page = "Fact Check"
            st.rerun()

# ═══════════════════════════════════════════════════════
# ✅ FACT CHECK
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Fact Check":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Fact Check in Progress</div>
        <div class="page-subtitle">Please wait while we extract claims and verify them on the web.</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.session_state.get("uploaded_file", None)

    if uploaded_file is None:
        st.warning("⚠️ No PDF uploaded. Please go to Upload PDF first.")
        if st.button("Go to Upload"):
            st.session_state.page = "Upload PDF"
            st.rerun()
    else:
        if st.session_state.results is None:
            # Progress steps
            step_placeholder = st.empty()

            def show_steps(active_idx):
                steps = ["Upload PDF", "Extracting Claims", "Verifying on Web", "Generating Report"]
                html = '<div class="progress-steps">'
                for i, s in enumerate(steps):
                    cls = "done" if i < active_idx else "active" if i == active_idx else ""
                    html += f'<div class="progress-step {cls}">{"✓ " if i < active_idx else ""}{s}</div>'
                html += "</div>"
                step_placeholder.markdown(html, unsafe_allow_html=True)

            show_steps(0)
            with st.spinner("📄 Reading PDF..."):
                text = extract_text(uploaded_file)
            show_steps(1)
            with st.spinner("🧠 Extracting claims with AI..."):
                try:
                    claims = extract_claims(text)
                except Exception as e:
                    st.error(f"Claim extraction failed: {e}")
                    claims = []

            if not claims:
                st.warning("⚠️ No verifiable claims found. Try a PDF with statistics or factual data.")
                st.stop()

            show_steps(2)
            progress_bar = st.progress(0)
            status_txt = st.empty()
            verified_count = inaccurate_count = false_count = noev_count = 0
            results_list = []

            for i, claim in enumerate(claims):
                status_txt.markdown(f"<p style='color:#6b7280;font-size:0.85rem'>🔎 Verifying claim {i+1} of {len(claims)}: <i>{claim[:80]}...</i></p>", unsafe_allow_html=True)
                try:
                    result = verify_claim(claim)
                except:
                    result = {"verdict": "NO_EVIDENCE", "explanation": "Could not verify.", "correct_fact": "", "confidence": 0, "sources": []}
                results_list.append((claim, result))
                v = result.get("verdict", "NO_EVIDENCE")
                if v == "VERIFIED": verified_count += 1
                elif v == "INACCURATE": inaccurate_count += 1
                elif v == "FALSE": false_count += 1
                else: noev_count += 1
                progress_bar.progress((i + 1) / len(claims))

            show_steps(3)
            status_txt.empty()

            st.session_state.results = {
                "filename": uploaded_file.name,
                "date": datetime.now().strftime("%b %d, %Y"),
                "claims": results_list,
                "verified": verified_count,
                "inaccurate": inaccurate_count,
                "false": false_count,
                "noevidence": noev_count,
                "total": len(claims)
            }

            # Save to history
            st.session_state.history.append({
                "filename": uploaded_file.name,
                "date": datetime.now().strftime("%b %d, %Y"),
                "total": len(claims),
                "verified": verified_count,
                "inaccurate": inaccurate_count,
                "false": false_count,
                "noevidence": noev_count,
            })

        # Show results
        r = st.session_state.results
        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-card metric-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
            <div class="metric-card metric-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
            <div class="metric-card metric-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
            <div class="metric-card metric-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Dashboard"):
                st.session_state.page = "Dashboard"
                st.rerun()
        with col2:
            if st.button("🔄 Check Another PDF"):
                st.session_state.results = None
                st.session_state.uploaded_file = None
                st.session_state.page = "Upload PDF"
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:Bricolage Grotesque,sans-serif; font-size:1.1rem; font-weight:800; color:#1a1d2e; margin-bottom:1rem;">📋 Detailed Results</div>', unsafe_allow_html=True)

        for claim, result in r["claims"]:
            verdict = result.get("verdict", "NO_EVIDENCE")
            c_class = css_class(verdict)
            correct = result.get("correct_fact", "")
            sources = result.get("sources", [])
            confidence = result.get("confidence", 50)

            correct_html = ""
            if correct and verdict != "VERIFIED":
                correct_html = f'<div class="correct-fact"><div class="correct-fact-label">📌 Correct / Latest Fact</div>{correct}</div>'

            sources_html = ""
            if sources:
                links = "".join([f'<a class="source-link" href="{s["url"]}" target="_blank">🔗 {s["title"][:35] or s["url"][:35]}...</a>' for s in sources[:2] if s.get("url")])
                if links:
                    sources_html = f'<div class="sources-list">{links}</div>'

            st.markdown(f"""
            <div class="claim-card {c_class}">
                <div class="claim-header">
                    <div class="claim-text">{claim}</div>
                    <div>{verdict_badge(verdict)}</div>
                </div>
                <div class="claim-explanation">{result.get("explanation","")}</div>
                {confidence_html(confidence)}
                {correct_html}
                {sources_html}
            </div>
            """, unsafe_allow_html=True)

        # Export
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:Bricolage Grotesque,sans-serif; font-size:1.1rem; font-weight:800; color:#1a1d2e; margin-bottom:1rem;">📥 Export Report</div>', unsafe_allow_html=True)

        report_lines = [
            f"FactChecker Report — {r['filename']}",
            f"Date: {r['date']}",
            f"Total Claims: {r['total']} | Verified: {r['verified']} | Inaccurate: {r['inaccurate']} | False: {r['false']}",
            "=" * 60, ""
        ]
        for i, (claim, result) in enumerate(r["claims"], 1):
            verdict = result.get("verdict", "NO_EVIDENCE")
            report_lines.append(f"{i}. [{verdict}] {claim}")
            report_lines.append(f"   Explanation: {result.get('explanation','')}")
            if result.get("correct_fact"):
                report_lines.append(f"   Correct Fact: {result['correct_fact']}")
            for s in result.get("sources", [])[:2]:
                if s.get("url"):
                    report_lines.append(f"   Source: {s['url']}")
            report_lines.append("")

        report_text = "\n".join(report_lines)
        st.download_button("📥 Download Fact Check Report", data=report_text, file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")

# ═══════════════════════════════════════════════════════
# 📊 DASHBOARD
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "Dashboard":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Fact Check Summary</div>
        <div class="page-subtitle">Here's the overview of claims found in your document.</div>
    </div>
    """, unsafe_allow_html=True)

    r = st.session_state.results

    if r is None:
        st.info("No fact check results yet. Upload a PDF to get started.")
        if st.button("Go to Upload PDF"):
            st.session_state.page = "Upload PDF"
            st.rerun()
    else:
        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-card metric-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
            <div class="metric-card metric-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
            <div class="metric-card metric-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
            <div class="metric-card metric-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False / No Evidence</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Percentages
        total = r["total"] or 1
        st.markdown(f"""
        <div class="card">
            <div style="font-weight:700; color:#1a1d2e; margin-bottom:1rem;">Status Distribution</div>
            <div style="margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#6b7280; margin-bottom:0.3rem;"><span>✅ Verified</span><span>{r['verified']/total*100:.1f}%</span></div>
                <div style="background:#e5e7eb; border-radius:100px; height:8px;"><div style="background:#059669; width:{r['verified']/total*100}%; height:8px; border-radius:100px;"></div></div>
            </div>
            <div style="margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#6b7280; margin-bottom:0.3rem;"><span>⚠️ Inaccurate</span><span>{r['inaccurate']/total*100:.1f}%</span></div>
                <div style="background:#e5e7eb; border-radius:100px; height:8px;"><div style="background:#d97706; width:{r['inaccurate']/total*100}%; height:8px; border-radius:100px;"></div></div>
            </div>
            <div>
                <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#6b7280; margin-bottom:0.3rem;"><span>❌ False</span><span>{r['false']/total*100:.1f}%</span></div>
                <div style="background:#e5e7eb; border-radius:100px; height:8px;"><div style="background:#dc2626; width:{r['false']/total*100}%; height:8px; border-radius:100px;"></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <div style="font-weight:700; color:#1a1d2e; margin-bottom:0.75rem;">Document</div>
            <div style="font-size:0.88rem; color:#6b7280;">📄 {r['filename']} &nbsp;·&nbsp; {r['date']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📋 View Detailed Results"):
            st.session_state.page = "Fact Check"
            st.rerun()

# ═══════════════════════════════════════════════════════
# 🕐 HISTORY
# ═══════════════════════════════════════════════════════
elif st.session_state.page == "History":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">History</div>
        <div class="page-subtitle">View your previously uploaded documents and results.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div style="text-align:center; padding:3rem; background:#fff; border:1px solid #e8ecf4; border-radius:16px;">
            <div style="font-size:2.5rem; margin-bottom:1rem;">🕐</div>
            <div style="font-weight:700; color:#1a1d2e; margin-bottom:0.5rem;">No history yet</div>
            <div style="font-size:0.85rem; color:#9ca3af;">Your fact check results will appear here.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Header row
        st.markdown("""
        <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr; gap:1rem; padding:0.5rem 1.25rem; font-size:0.75rem; font-weight:700; color:#9ca3af; text-transform:uppercase; letter-spacing:0.08em;">
            <div>Document Name</div><div>Total</div><div>Verified</div><div>Inaccurate</div><div>False</div><div>Date</div>
        </div>
        """, unsafe_allow_html=True)

        for h in reversed(st.session_state.history):
            st.markdown(f"""
            <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr; gap:1rem; padding:1rem 1.25rem; background:#fff; border:1px solid #e8ecf4; border-radius:12px; margin-bottom:0.5rem; align-items:center;">
                <div>
                    <div style="font-weight:600; color:#1a1d2e; font-size:0.9rem;">📄 {h['filename']}</div>
                </div>
                <div style="font-weight:700; color:#1a1d2e;">{h['total']}</div>
                <div style="color:#059669; font-weight:700;">{h['verified']}</div>
                <div style="color:#d97706; font-weight:700;">{h['inaccurate']}</div>
                <div style="color:#dc2626; font-weight:700;">{h['false']}</div>
                <div style="font-size:0.82rem; color:#9ca3af;">{h['date']}</div>
            </div>
            """, unsafe_allow_html=True)
