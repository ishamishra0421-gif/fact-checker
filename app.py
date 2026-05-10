import streamlit as st
import pdfplumber
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import json
from groq import Groq

# Page config
st.set_page_config(page_title="FactLens AI", page_icon="🔬", layout="wide")

# Load API keys
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    * { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #080b12; color: #e8e8e8; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 1rem 3rem 3rem 3rem; max-width: 1100px; }

    /* NAV */
    .nav { display: flex; align-items: center; justify-content: space-between; padding: 1.2rem 0; border-bottom: 1px solid #1e2535; margin-bottom: 2rem; }
    .nav-logo { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #00ffaa, #00b4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }

    /* HERO */
    .hero { text-align: center; padding: 4rem 0 3rem 0; }
    .hero-badge { display: inline-block; background: rgba(0,255,170,0.08); border: 1px solid rgba(0,255,170,0.25); color: #00ffaa; font-size: 0.75rem; font-weight: 500; letter-spacing: 0.15em; text-transform: uppercase; padding: 0.35em 1em; border-radius: 100px; margin-bottom: 1.5rem; }
    .hero-title { font-family: 'Syne', sans-serif; font-size: clamp(2.8rem, 7vw, 5rem); font-weight: 800; line-height: 1.05; letter-spacing: -0.03em; color: #ffffff; margin: 0 0 1.2rem 0; }
    .hero-title span { background: linear-gradient(135deg, #00ffaa 0%, #00b4ff 50%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .hero-sub { font-size: 1.15rem; color: #7a8399; font-weight: 300; max-width: 520px; margin: 0 auto 2.5rem auto; line-height: 1.8; }

    /* FEATURE CARDS */
    .features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; margin: 3rem 0; }
    .feature-card { background: #0d1117; border: 1px solid #1e2535; border-radius: 16px; padding: 2rem 1.5rem; transition: all 0.3s ease; }
    .feature-card:hover { border-color: #2a3042; transform: translateY(-3px); }
    .feature-icon { font-size: 2.2rem; margin-bottom: 1rem; }
    .feature-title { font-family: 'Syne', sans-serif; font-weight: 700; color: #fff; font-size: 1.05rem; margin-bottom: 0.5rem; }
    .feature-desc { color: #4a5568; font-size: 0.88rem; line-height: 1.7; }

    /* STATS BANNER */
    .stats-banner { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; background: #0d1117; border: 1px solid #1e2535; border-radius: 16px; padding: 2rem; margin: 2rem 0; text-align: center; }
    .banner-stat-num { font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #00ffaa, #00b4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .banner-stat-label { color: #4a5568; font-size: 0.82rem; margin-top: 0.25rem; }

    /* RESULT STATS */
    .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 2rem 0; }
    .stat-card { background: #0d1117; border: 1px solid #1e2535; border-radius: 14px; padding: 1.5rem; text-align: center; position: relative; overflow: hidden; }
    .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }
    .stat-card.verified::before { background: linear-gradient(90deg, #00ffaa, #00b4ff); }
    .stat-card.inaccurate::before { background: linear-gradient(90deg, #ff9500, #ffcc00); }
    .stat-card.false::before { background: linear-gradient(90deg, #ff3b5c, #ff6b35); }
    .stat-number { font-family: 'Syne', sans-serif; font-size: 2.8rem; font-weight: 800; line-height: 1; margin-bottom: 0.25rem; }
    .stat-card.verified .stat-number { color: #00ffaa; }
    .stat-card.inaccurate .stat-number { color: #ff9500; }
    .stat-card.false .stat-number { color: #ff3b5c; }
    .stat-label { color: #4a5568; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; }

    /* CLAIM CARDS */
    .claim-card { background: #0d1117; border: 1px solid #1e2535; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem; position: relative; overflow: hidden; transition: all 0.2s ease; }
    .claim-card:hover { border-color: #2a3042; transform: translateY(-1px); }
    .claim-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; }
    .claim-card.verified::before { background: #00ffaa; }
    .claim-card.inaccurate::before { background: #ff9500; }
    .claim-card.false::before { background: #ff3b5c; }
    .verdict-badge { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.2em 0.7em; border-radius: 100px; }
    .verdict-badge.verified { background: rgba(0,255,170,0.1); color: #00ffaa; }
    .verdict-badge.inaccurate { background: rgba(255,149,0,0.1); color: #ff9500; }
    .verdict-badge.false { background: rgba(255,59,92,0.1); color: #ff3b5c; }
    .claim-text { color: #c8d0e0; font-size: 0.95rem; line-height: 1.5; margin-top: 0.5rem; }
    .claim-explanation { color: #5a6478; font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.6; }
    .correct-fact { background: rgba(0,180,255,0.06); border: 1px solid rgba(0,180,255,0.15); border-radius: 8px; padding: 0.6rem 0.9rem; margin-top: 0.6rem; color: #00b4ff; font-size: 0.85rem; }
    .correct-fact-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.7; margin-bottom: 0.2rem; }

    /* ABOUT */
    .step-item { display: flex; gap: 1.5rem; align-items: flex-start; padding: 1.5rem; background: #0d1117; border: 1px solid #1e2535; border-radius: 14px; margin-bottom: 1rem; }
    .step-num { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; color: #1e2535; min-width: 3rem; }
    .step-content-title { font-family: 'Syne', sans-serif; font-weight: 700; color: #fff; margin-bottom: 0.3rem; }
    .step-content-desc { color: #4a5568; font-size: 0.88rem; line-height: 1.7; }
    .tech-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1.5rem 0; }
    .tech-card { background: #0d1117; border: 1px solid #1e2535; border-radius: 12px; padding: 1.25rem; }
    .tech-name { font-family: 'Syne', sans-serif; font-weight: 700; color: #00ffaa; margin-bottom: 0.3rem; }
    .tech-desc { color: #4a5568; font-size: 0.85rem; }

    .section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; color: #ffffff; margin: 2rem 0 1rem 0; }
    .stButton > button { background: linear-gradient(135deg, #00ffaa, #00b4ff) !important; color: #080b12 !important; font-weight: 700 !important; font-family: 'Syne', sans-serif !important; border: none !important; border-radius: 10px !important; padding: 0.75rem 2rem !important; font-size: 1rem !important; width: 100% !important; }
    .stProgress > div > div { background: linear-gradient(90deg, #00ffaa, #00b4ff) !important; }
    .stSuccess { background: rgba(0,255,170,0.08) !important; border-color: #00ffaa33 !important; color: #00ffaa !important; border-radius: 10px !important; }
    hr { border-color: #1e2535 !important; margin: 2rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── NAV ──────────────────────────────────────────────
st.markdown('<div class="nav"><div class="nav-logo">🔬 FactLens AI</div></div>', unsafe_allow_html=True)

page = st.radio("", ["🏠 Home", "🔍 Fact Checker", "📖 About"], horizontal=True, label_visibility="collapsed")
st.markdown("<hr>", unsafe_allow_html=True)

# ─── HELPERS ──────────────────────────────────────────
def extract_text(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def extract_claims(text):
    prompt = f"""Extract all specific verifiable claims from this text.
Focus on: statistics, percentages, dates, financial figures, technical facts.
Return ONLY a JSON list like: ["claim 1", "claim 2"]
No extra text, just the JSON list.
Text: {text[:4000]}"""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    return json.loads(clean)

def verify_claim(claim):
    results = tavily.search(claim, max_results=3)
    prompt = f"""Claim: "{claim}"
Web results: {results['results']}
Classify as VERIFIED, INACCURATE, or FALSE.
Reply ONLY: {{"verdict": "VERIFIED or INACCURATE or FALSE", "explanation": "one sentence", "correct_fact": "real fact if wrong"}}"""
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    return json.loads(clean)

# ═══════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">🔬 AI-Powered Fact Verification</div>
        <h1 class="hero-title">Every Claim.<br><span>Verified.</span></h1>
        <p class="hero-sub">Upload any PDF and our AI instantly extracts every factual claim and cross-references it against live web data.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stats-banner">
        <div><div class="banner-stat-num">3-Step</div><div class="banner-stat-label">Simple Process</div></div>
        <div><div class="banner-stat-num">Live</div><div class="banner-stat-label">Web Verification</div></div>
        <div><div class="banner-stat-num">100%</div><div class="banner-stat-label">Free to Use</div></div>
    </div>
    <div class="features-grid">
        <div class="feature-card"><div class="feature-icon">📄</div><div class="feature-title">Smart Extraction</div><div class="feature-desc">AI reads your PDF and identifies every verifiable claim, stat, date, and figure automatically.</div></div>
        <div class="feature-card"><div class="feature-icon">🌐</div><div class="feature-title">Live Web Search</div><div class="feature-desc">Each claim is cross-referenced against real-time web data using Tavily search engine.</div></div>
        <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Instant Verdict</div><div class="feature-desc">Get color-coded results: Verified ✅, Inaccurate ⚠️, or False ❌ — with corrections.</div></div>
        <div class="feature-card"><div class="feature-icon">⚡</div><div class="feature-title">Lightning Fast</div><div class="feature-desc">Powered by Groq's ultra-fast LLaMA model for near-instant claim analysis.</div></div>
        <div class="feature-card"><div class="feature-icon">🔒</div><div class="feature-title">Private & Secure</div><div class="feature-desc">Your PDF is processed locally. No data is stored or shared with third parties.</div></div>
        <div class="feature-card"><div class="feature-icon">📊</div><div class="feature-title">Detailed Reports</div><div class="feature-desc">Full breakdown with explanations and correct facts for every inaccurate claim found.</div></div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════
# 🔍 FACT CHECKER
# ═══════════════════════════════════
elif page == "🔍 Fact Checker":
    st.markdown("""
    <div style="text-align:center; padding:2rem 0 1.5rem;">
        <h2 style="font-family:Syne,sans-serif; font-size:2rem; font-weight:800; color:#fff; margin:0;">Upload Your PDF</h2>
        <p style="color:#7a8399; margin-top:0.5rem;">We'll extract and verify every factual claim</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        st.success(f"✅ Ready: **{uploaded_file.name}**")
        if st.button("🚀 Start Fact Checking"):
            with st.spinner("📄 Reading PDF..."):
                text = extract_text(uploaded_file)
            with st.spinner("🧠 Extracting claims..."):
                try:
                    claims = extract_claims(text)
                except Exception as e:
                    st.error(f"Error: {e}")
                    claims = []

            if not claims:
                st.warning("⚠️ No verifiable claims found. Try a PDF with statistics or factual data.")
            else:
                st.markdown(f'<div class="section-title">Found <span style="color:#00ffaa">{len(claims)}</span> claims</div>', unsafe_allow_html=True)
                progress = st.progress(0)
                status = st.empty()
                verified_count = inaccurate_count = false_count = 0
                results_list = []

                for i, claim in enumerate(claims):
                    status.markdown(f"<p style='color:#5a6478;font-size:0.85rem'>🔎 Verifying {i+1} of {len(claims)}...</p>", unsafe_allow_html=True)
                    try:
                        result = verify_claim(claim)
                    except:
                        result = {"verdict": "FALSE", "explanation": "Could not verify.", "correct_fact": ""}
                    results_list.append((claim, result))
                    v = result.get("verdict", "FALSE")
                    if v == "VERIFIED": verified_count += 1
                    elif v == "INACCURATE": inaccurate_count += 1
                    else: false_count += 1
                    progress.progress((i + 1) / len(claims))

                status.empty()
                st.markdown(f"""
                <div class="stats-row">
                    <div class="stat-card verified"><div class="stat-number">{verified_count}</div><div class="stat-label">✅ Verified</div></div>
                    <div class="stat-card inaccurate"><div class="stat-number">{inaccurate_count}</div><div class="stat-label">⚠️ Inaccurate</div></div>
                    <div class="stat-card false"><div class="stat-number">{false_count}</div><div class="stat-label">❌ False</div></div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 Detailed Results</div>', unsafe_allow_html=True)

                for claim, result in results_list:
                    verdict = result.get("verdict", "FALSE")
                    css_class = verdict.lower() if verdict in ["VERIFIED", "INACCURATE", "FALSE"] else "false"
                    emoji = "✅" if verdict == "VERIFIED" else "⚠️" if verdict == "INACCURATE" else "❌"
                    correct = result.get("correct_fact", "")
                    correct_html = f'<div class="correct-fact"><div class="correct-fact-label">📌 Correct Fact</div>{correct}</div>' if correct and verdict != "VERIFIED" else ""
                    st.markdown(f"""
                    <div class="claim-card {css_class}">
                        <span class="verdict-badge {css_class}">{emoji} {verdict}</span>
                        <div class="claim-text">{claim}</div>
                        <div class="claim-explanation">{result.get("explanation","")}</div>
                        {correct_html}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:center; padding:3rem; border:1.5px dashed #1e2535; border-radius:16px; margin-top:1rem;'>
            <div style='font-size:3rem; margin-bottom:1rem;'>📄</div>
            <div style='font-family:Syne,sans-serif; font-size:1.2rem; color:#3a4052; font-weight:700;'>Drop your PDF above</div>
            <div style='font-size:0.85rem; margin-top:0.5rem; color:#2a3042;'>Works with research papers, reports, news articles, marketing docs</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════
# 📖 ABOUT
# ═══════════════════════════════════
elif page == "📖 About":
    st.markdown("""
    <div style="text-align:center; padding:2rem 0;">
        <h2 style="font-family:Syne,sans-serif; font-size:2.5rem; font-weight:800; color:#fff;">How FactLens Works</h2>
        <p style="color:#7a8399; max-width:500px; margin:0.5rem auto; line-height:1.8;">A 4-step AI pipeline that turns any PDF into a fully verified fact report.</p>
    </div>
    <div>
        <div class="step-item"><div class="step-num">01</div><div><div class="step-content-title">📄 PDF Text Extraction</div><div class="step-content-desc">We use pdfplumber to extract all readable text from your uploaded PDF. Works with research papers, reports, news articles, and marketing documents.</div></div></div>
        <div class="step-item"><div class="step-num">02</div><div><div class="step-content-title">🧠 AI Claim Detection</div><div class="step-content-desc">Text is sent to Groq's LLaMA 3.3 model which identifies all verifiable claims — statistics, dates, financial figures, and technical facts.</div></div></div>
        <div class="step-item"><div class="step-num">03</div><div><div class="step-content-title">🌐 Live Web Verification</div><div class="step-content-desc">Each claim is searched on the live web using Tavily API. AI analyzes results to determine if the claim is Verified, Inaccurate, or False.</div></div></div>
        <div class="step-item"><div class="step-num">04</div><div><div class="step-content-title">📊 Detailed Report</div><div class="step-content-desc">You get a color-coded report showing every claim with its verdict, explanation, and the correct fact where applicable.</div></div></div>
    </div>
    <div class="section-title">🛠️ Tech Stack</div>
    <div class="tech-grid">
        <div class="tech-card"><div class="tech-name">⚡ Groq + LLaMA 3.3</div><div class="tech-desc">Ultra-fast AI for claim extraction and verdict generation.</div></div>
        <div class="tech-card"><div class="tech-name">🌐 Tavily Search</div><div class="tech-desc">Real-time web search API for live fact verification.</div></div>
        <div class="tech-card"><div class="tech-name">📄 pdfplumber</div><div class="tech-desc">Accurate text extraction from any PDF document.</div></div>
        <div class="tech-card"><div class="tech-name">🎨 Streamlit</div><div class="tech-desc">Fast Python web framework for building the UI.</div></div>
    </div>
    <hr>
    <div style="text-align:center; padding:2rem; background:#0d1117; border:1px solid #1e2535; border-radius:16px;">
        <div style="font-family:Syne,sans-serif; font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:0.5rem;">Ready to fact-check your PDF?</div>
        <div style="color:#4a5568; font-size:0.9rem;">Switch to the Fact Checker tab and upload your document</div>
    </div>
    """, unsafe_allow_html=True)
