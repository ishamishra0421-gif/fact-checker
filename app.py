import streamlit as st
2
import pdfplumber
3
from tavily import TavilyClient
4
from dotenv import load_dotenv
5
import os
6
import json
7
import time
8
from groq import Groq
9
from datetime import datetime
10
 
11
# ─── PAGE CONFIG ───────────────────────────────────────
12
st.set_page_config(
13
    page_title="FactChecker AI",
14
    page_icon="🛡️",
15
    layout="wide",
16
    initial_sidebar_state="expanded"
17
)
18
 
19
# ─── LOAD API KEYS ─────────────────────────────────────
20
load_dotenv()
21
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
22
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
23
 
24
# ─── SESSION STATE ─────────────────────────────────────
25
for key, default in [
26
    ("history", []),
27
    ("results", None),
28
    ("page", "Home"),
29
    ("uploaded_file", None),
30
]:
31
    if key not in st.session_state:
32
        st.session_state[key] = default
33
 
34
# ─── CSS ───────────────────────────────────────────────
35
st.markdown("""
36
<style>
37
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Bricolage+Grotesque:wght@400;600;700;800&display=swap');
38
 
39
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
40
 
41
html, body, .stApp {
42
    font-family: 'Plus Jakarta Sans', sans-serif !important;
43
    background: #0a0e1a !important;
44
    color: #e2e8f0 !important;
45
}
46
 
47
#MainMenu, footer, header { visibility: hidden; }
48
.stDeployButton { display: none; }
49
 
50
.block-container {
51
    padding: 1.5rem 2rem 3rem 2rem !important;
52
    max-width: 1080px !important;
53
}
54
 
55
@media (max-width: 768px) {
56
    .block-container { padding: 1rem 0.75rem 2rem 0.75rem !important; }
57
    .metrics-grid { grid-template-columns: repeat(2, 1fr) !important; }
58
    .steps-row { grid-template-columns: repeat(2, 1fr) !important; }
59
    .features-grid { grid-template-columns: 1fr !important; }
60
    .hero-title { font-size: 2rem !important; }
61
    .charts-row { grid-template-columns: 1fr !important; }
62
    .before-after { grid-template-columns: 1fr !important; }
63
    .sample-grid { grid-template-columns: 1fr !important; }
64
}
65
 
66
/* ── SIDEBAR ── */
67
section[data-testid="stSidebar"] {
68
    background: #0d1224 !important;
69
    border-right: 1px solid #1e2a45 !important;
70
}
71
section[data-testid="stSidebar"] > div { padding: 1.25rem 0.75rem !important; }
72
 
73
.sidebar-logo {
74
    display: flex; align-items: center; gap: 0.6rem;
75
    padding: 0.5rem 0.75rem 1.25rem 0.75rem;
76
    border-bottom: 1px solid #1e2a45; margin-bottom: 1rem;
77
}
78
.sidebar-logo-text {
79
    font-family: 'Bricolage Grotesque', sans-serif;
80
    font-size: 1.05rem; font-weight: 800;
81
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
82
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
83
}
84
.sidebar-logo-sub { font-size: 0.62rem; color: #4a5568; }
85
.sidebar-section {
86
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.14em;
87
    text-transform: uppercase; color: #2d3748;
88
    padding: 0 0.75rem; margin: 1rem 0 0.4rem 0;
89
}
90
 
91
/* ── BUTTONS ── */
92
.stButton > button {
93
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
94
    color: white !important;
95
    font-family: 'Plus Jakarta Sans', sans-serif !important;
96
    font-weight: 700 !important; border: none !important;
97
    border-radius: 10px !important;
98
    padding: 0.65rem 1.5rem !important;
99
    font-size: 0.88rem !important; width: 100% !important;
100
    transition: all 0.2s !important;
101
    box-shadow: 0 4px 15px rgba(99,102,241,0.25) !important;
102
}
103
.stButton > button:hover {
104
    transform: translateY(-1px) !important;
105
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
106
}
107
 
108
/* ── CARDS ── */
109
.glass-card {
110
    background: rgba(255,255,255,0.04);
111
    border: 1px solid rgba(255,255,255,0.08);
112
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
113
}
114
 
115
/* ── METRICS ── */
116
.metrics-grid {
117
    display: grid; grid-template-columns: repeat(4, 1fr);
118
    gap: 1rem; margin-bottom: 1.5rem;
119
}
120
.metric-card {
121
    background: rgba(255,255,255,0.04);
122
    border: 1px solid rgba(255,255,255,0.08);
123
    border-radius: 14px; padding: 1.25rem; text-align: center;
124
}
125
.metric-num {
126
    font-family: 'Bricolage Grotesque', sans-serif;
127
    font-size: 2.2rem; font-weight: 800; line-height: 1;
128
}
129
.metric-label { font-size: 0.73rem; color: #64748b; margin-top: 0.3rem; font-weight: 500; }
130
.metric-total .metric-num { color: #e2e8f0; }
131
.metric-verified .metric-num { color: #10b981; }
132
.metric-inaccurate .metric-num { color: #f59e0b; }
133
.metric-false .metric-num { color: #ef4444; }
134
 
135
/* ── PAGE HEADER ── */
136
.page-header { margin-bottom: 1.75rem; }
137
.page-title {
138
    font-family: 'Bricolage Grotesque', sans-serif;
139
    font-size: 1.6rem; font-weight: 800; color: #f1f5f9; margin-bottom: 0.25rem;
140
}
141
.page-subtitle { color: #64748b; font-size: 0.86rem; }
142
 
143
/* ── HERO ── */
144
.hero-section {
145
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
146
    border: 1px solid rgba(99,102,241,0.3);
147
    border-radius: 20px; padding: 3rem 2.5rem;
148
    margin-bottom: 2rem; position: relative; overflow: hidden;
149
}
150
.hero-section::before {
151
    content: ''; position: absolute; top: -50%; right: -10%;
152
    width: 400px; height: 400px;
153
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
154
    border-radius: 50%;
155
}
156
.hero-badge {
157
    display: inline-block;
158
    background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4);
159
    color: #a5b4fc; font-size: 0.7rem; font-weight: 700;
160
    letter-spacing: 0.1em; text-transform: uppercase;
161
    padding: 0.3em 1em; border-radius: 100px; margin-bottom: 1rem;
162
}
163
.hero-title {
164
    font-family: 'Bricolage Grotesque', sans-serif;
165
    font-size: 3rem; font-weight: 800; line-height: 1.1;
166
    color: #f1f5f9; margin-bottom: 0.75rem;
167
}
168
.hero-title span {
169
    background: linear-gradient(135deg, #818cf8, #c084fc);
170
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
171
}
172
.hero-sub { font-size: 0.97rem; color: #94a3b8; max-width: 480px; line-height: 1.75; margin-bottom: 1.5rem; }
173
.hero-bullets { list-style: none; display: flex; flex-direction: column; gap: 0.4rem; }
174
.hero-bullets li { font-size: 0.85rem; color: #a5b4fc; }
175
.hero-bullets li::before { content: '✦ '; color: #818cf8; }
176
 
177
/* ── STEPS ── */
178
.steps-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }
179
.step-card {
180
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
181
    border-radius: 14px; padding: 1.4rem 1rem; text-align: center; transition: border-color 0.2s;
182
}
183
.step-card:hover { border-color: rgba(99,102,241,0.4); }
184
.step-num {
185
    font-size: 0.62rem; font-weight: 800; letter-spacing: 0.1em;
186
    color: #818cf8; background: rgba(99,102,241,0.15);
187
    border-radius: 100px; display: inline-block; padding: 0.2em 0.75em; margin-bottom: 0.75rem;
188
}
189
.step-icon { font-size: 1.7rem; margin-bottom: 0.5rem; }
190
.step-title { font-weight: 700; color: #e2e8f0; font-size: 0.87rem; margin-bottom: 0.3rem; }
191
.step-desc { font-size: 0.77rem; color: #64748b; line-height: 1.6; }
192
 
193
/* ── PROCESSING STEPPER ── */
194
.process-stepper {
195
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
196
    border-radius: 16px; padding: 1.5rem; margin: 1rem 0;
197
}
198
.process-step {
199
    display: flex; align-items: center; gap: 1rem;
200
    padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);
201
}
202
.process-step:last-child { border-bottom: none; }
203
.step-indicator {
204
    width: 36px; height: 36px; border-radius: 50%;
205
    display: flex; align-items: center; justify-content: center;
206
    font-size: 1rem; flex-shrink: 0;
207
}
208
.step-indicator.active { animation: pulse 1.5s infinite; }
209
.step-text-title { font-weight: 600; font-size: 0.87rem; color: #e2e8f0; }
210
.step-text-sub { font-size: 0.73rem; color: #64748b; margin-top: 0.1rem; }
211
 
212
@keyframes pulse {
213
    0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
214
    50% { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
215
}
216
 
217
/* ── TRUST SCORE ── */
218
.trust-score-card {
219
    background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(99,102,241,0.08));
220
    border: 1px solid rgba(99,102,241,0.2);
221
    border-radius: 16px; padding: 1.5rem; text-align: center; margin-bottom: 0;
222
    height: 100%;
223
}
224
.trust-score-num {
225
    font-family: 'Bricolage Grotesque', sans-serif;
226
    font-size: 3.5rem; font-weight: 800;
227
    background: linear-gradient(135deg, #10b981, #6366f1);
228
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
229
}
230
.risk-badge {
231
    display: inline-block; padding: 0.3em 1em; border-radius: 100px;
232
    font-size: 0.73rem; font-weight: 700; margin-top: 0.75rem;
233
}
234
.risk-low { background: rgba(16,185,129,0.15); color: #10b981; }
235
.risk-med { background: rgba(245,158,11,0.15); color: #f59e0b; }
236
.risk-high { background: rgba(239,68,68,0.15); color: #ef4444; }
237
 
238
/* ── AI SUMMARY ── */
239
.ai-summary {
240
    background: rgba(99,102,241,0.07); border: 1px solid rgba(99,102,241,0.2);
241
    border-left: 4px solid #6366f1; border-radius: 12px;
242
    padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
243
}
244
.ai-summary-label {
245
    font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em;
246
    text-transform: uppercase; color: #818cf8; margin-bottom: 0.5rem;
247
}
248
.ai-summary-text { font-size: 0.9rem; color: #c7d2fe; line-height: 1.75; }
249
 
250
/* ── CLAIM CARDS ── */
251
.claim-card {
252
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
253
    border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
254
    border-left: 4px solid rgba(255,255,255,0.1); transition: background 0.2s;
255
}
256
.claim-card:hover { background: rgba(255,255,255,0.05); }
257
.claim-card.verified { border-left-color: #10b981; }
258
.claim-card.inaccurate { border-left-color: #f59e0b; }
259
.claim-card.false { border-left-color: #ef4444; }
260
.claim-card.noevidence { border-left-color: #64748b; }
261
 
262
.claim-header {
263
    display: flex; justify-content: space-between; align-items: flex-start;
264
    gap: 1rem; margin-bottom: 0.6rem; flex-wrap: wrap;
265
}
266
.claim-text { font-size: 0.92rem; font-weight: 600; color: #e2e8f0; line-height: 1.5; flex: 1; min-width: 180px; }
267
.claim-explanation { font-size: 0.82rem; color: #94a3b8; line-height: 1.65; margin-top: 0.4rem; }
268
 
269
.before-after { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.75rem; }
270
.before-box {
271
    background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15);
272
    border-radius: 10px; padding: 0.75rem;
273
}
274
.after-box {
275
    background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15);
276
    border-radius: 10px; padding: 0.75rem;
277
}
278
.ba-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.3rem; }
279
.before-box .ba-label { color: #ef4444; }
280
.after-box .ba-label { color: #10b981; }
281
.ba-text { font-size: 0.82rem; color: #cbd5e1; line-height: 1.5; }
282
 
283
.ai-reasoning {
284
    background: rgba(139,92,246,0.06); border: 1px solid rgba(139,92,246,0.15);
285
    border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.75rem;
286
}
287
.ai-reasoning-label { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; color: #a78bfa; margin-bottom: 0.3rem; }
288
.ai-reasoning-text { font-size: 0.81rem; color: #c4b5fd; line-height: 1.65; }
289
 
290
.sources-list { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
291
.source-chip {
292
    display: inline-flex; align-items: center; gap: 0.3rem;
293
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
294
    border-radius: 8px; padding: 0.25rem 0.65rem;
295
    font-size: 0.73rem; color: #818cf8; text-decoration: none; transition: background 0.15s;
296
}
297
.source-chip:hover { background: rgba(99,102,241,0.15); }
298
 
299
/* ── BADGES ── */
300
.badge {
301
    display: inline-flex; align-items: center; gap: 0.3rem;
302
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
303
    text-transform: uppercase; padding: 0.25em 0.8em; border-radius: 100px; white-space: nowrap;
304
}
305
.badge-verified { background: rgba(16,185,129,0.15); color: #10b981; }
306
.badge-inaccurate { background: rgba(245,158,11,0.15); color: #f59e0b; }
307
.badge-false { background: rgba(239,68,68,0.15); color: #ef4444; }
308
.badge-noevidence { background: rgba(100,116,139,0.15); color: #94a3b8; }
309
 
310
/* ── CONFIDENCE BAR ── */
311
.conf-wrap { margin-top: 0.6rem; display: flex; align-items: center; gap: 0.75rem; }
312
.conf-label { font-size: 0.73rem; color: #64748b; white-space: nowrap; min-width: 78px; }
313
.conf-track { flex: 1; background: rgba(255,255,255,0.06); border-radius: 100px; height: 6px; }
314
.conf-fill { height: 6px; border-radius: 100px; }
315
.conf-high { background: linear-gradient(90deg, #10b981, #34d399); }
316
.conf-med { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
317
.conf-low { background: linear-gradient(90deg, #ef4444, #f87171); }
318
.conf-pct { font-size: 0.76rem; font-weight: 700; min-width: 34px; }
319
 
320
/* ── FEATURES GRID ── */
321
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.25rem 0; }
322
.feature-card {
323
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
324
    border-radius: 14px; padding: 1.4rem; transition: border-color 0.2s;
325
}
326
.feature-card:hover { border-color: rgba(99,102,241,0.3); }
327
.feature-icon { font-size: 1.7rem; margin-bottom: 0.65rem; }
328
.feature-title { font-weight: 700; color: #e2e8f0; font-size: 0.88rem; margin-bottom: 0.35rem; }
329
.feature-desc { font-size: 0.78rem; color: #64748b; line-height: 1.65; }
330
 
331
/* ── SAMPLE CARDS ── */
332
.sample-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }
333
.sample-card {
334
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
335
    border-radius: 14px; padding: 1.25rem; text-align: center;
336
}
337
.sample-title { font-weight: 700; color: #e2e8f0; font-size: 0.88rem; margin-bottom: 0.3rem; }
338
.sample-desc { font-size: 0.77rem; color: #64748b; line-height: 1.55; }
339
 
340
/* ── CHARTS ── */
341
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.25rem 0; }
342
.chart-card {
343
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
344
    border-radius: 14px; padding: 1.25rem;
345
}
346
.chart-title { font-weight: 700; color: #e2e8f0; font-size: 0.87rem; margin-bottom: 1rem; }
347
.donut-svg { width: 100%; max-width: 150px; display: block; margin: 0 auto; }
348
.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.77rem; color: #94a3b8; margin-bottom: 0.35rem; }
349
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
350
.bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
351
.bar-label { font-size: 0.73rem; color: #94a3b8; min-width: 80px; }
352
.bar-track { flex: 1; background: rgba(255,255,255,0.06); border-radius: 100px; height: 10px; }
353
.bar-val { font-size: 0.73rem; color: #e2e8f0; font-weight: 700; min-width: 28px; text-align: right; }
354
 
355
/* ── SUSPICIOUS ── */
356
.suspicious-list { margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
357
.suspicious-chip {
358
    background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.25);
359
    color: #fb923c; border-radius: 6px; padding: 0.2rem 0.6rem; font-size: 0.73rem; font-weight: 600;
360
}
361
 
362
/* ── UPLOAD ZONE ── */
363
.drop-zone {
364
    border: 2px dashed rgba(99,102,241,0.3); border-radius: 16px; padding: 2.5rem 2rem;
365
    text-align: center; background: rgba(99,102,241,0.04); margin: 0.5rem 0;
366
}
367
.drop-title { font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.05rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.4rem; }
368
.drop-sub { font-size: 0.8rem; color: #4a5568; }
369
 
370
/* ── MISC ── */
371
.stProgress > div > div { background: linear-gradient(90deg, #6366f1, #8b5cf6) !important; }
372
.stSuccess { background: rgba(16,185,129,0.1) !important; border-color: rgba(16,185,129,0.3) !important; color: #6ee7b7 !important; border-radius: 10px !important; }
373
.stWarning { background: rgba(245,158,11,0.1) !important; border-color: rgba(245,158,11,0.3) !important; color: #fcd34d !important; border-radius: 10px !important; }
374
.stInfo { background: rgba(99,102,241,0.1) !important; border-color: rgba(99,102,241,0.3) !important; border-radius: 10px !important; }
375
[data-testid="stFileUploader"] { background: rgba(99,102,241,0.04) !important; border: 2px dashed rgba(99,102,241,0.3) !important; border-radius: 14px !important; }
376
div[data-testid="stRadio"] { display: none !important; }
377
hr { border-color: rgba(255,255,255,0.06) !important; margin: 1.5rem 0 !important; }
378
[data-testid="stDownloadButton"] > button {
379
    background: rgba(16,185,129,0.12) !important; color: #10b981 !important;
380
    border: 1px solid rgba(16,185,129,0.3) !important; box-shadow: none !important;
381
}
382
</style>
383
""", unsafe_allow_html=True)
384
 
385
# ─── SIDEBAR ───────────────────────────────────────────
386
with st.sidebar:
387
    st.markdown("""
388
    <div class="sidebar-logo">
389
        <div style="font-size:1.4rem">🛡️</div>
390
        <div>
391
            <div class="sidebar-logo-text">FactChecker AI</div>
392
            <div class="sidebar-logo-sub">Truth Layer for Your Content</div>
393
        </div>
394
    </div>
395
    """, unsafe_allow_html=True)
396
 
397
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
398
    for icon, label in [("🏠","Home"),("📤","Upload PDF"),("✅","Fact Check"),("📊","Dashboard"),("🕐","History")]:
399
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
400
            st.session_state.page = label
401
            st.rerun()
402
 
403
    st.markdown("<br>", unsafe_allow_html=True)
404
    st.markdown("""
405
    <div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.15);border-radius:12px;padding:1rem;font-size:0.73rem;color:#64748b;">
406
        <div style="color:#a5b4fc;font-weight:700;margin-bottom:0.5rem;">⚙️ Architecture</div>
407
        PDF → LLM Claims<br>→ Web Search<br>→ Fact Validation<br>→ Report
408
    </div>
409
    """, unsafe_allow_html=True)
410
 
411
    if st.session_state.results:
412
        r = st.session_state.results
413
        trust = r.get("trust_score", 70)
414
        risk = "🟢 Low" if trust >= 70 else "🟡 Medium" if trust >= 45 else "🔴 High"
415
        color = "#10b981" if trust >= 70 else "#f59e0b" if trust >= 45 else "#ef4444"
416
        st.markdown(f"""
417
        <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);border-radius:12px;padding:1rem;margin-top:0.75rem;text-align:center;">
418
            <div style="font-size:0.6rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Trust Score</div>
419
            <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.8rem;font-weight:800;color:{color};">{trust}/100</div>
420
            <div style="font-size:0.75rem;color:#64748b;">{risk} Risk</div>
421
        </div>
422
        """, unsafe_allow_html=True)
423
 
424
# ─── HELPERS ───────────────────────────────────────────
425
SUSPICIOUS_PHRASES = [
426
    "world's best","most trusted","#1","number one","best in class",
427
    "revolutionary","game-changing","unprecedented","unmatched","guaranteed",
428
    "100% proven","scientifically proven","doctors recommend","clinically proven",
429
    "fastest growing","market leader","industry leading","world-class",
430
]
431
 
432
def extract_text(pdf_file):
433
    with pdfplumber.open(pdf_file) as pdf:
434
        return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
435
 
436
def find_suspicious(text):
437
    return [p for p in SUSPICIOUS_PHRASES if p in text.lower()]
438
 
439
def extract_claims(text):
440
    prompt = f"""You are a fact-checking AI. Extract all specific verifiable factual claims from the text.
441
Focus ONLY on: statistics, percentages, revenue/market figures, user counts, dates tied to events, technical specs, scientific statistics.
442
Return ONLY a valid JSON array of claim strings. No markdown, no preamble.
443
Example: ["India has 950M internet users", "OpenAI reached 100M users in 2023"]
444
Text: {text[:4000]}"""
445
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
446
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
447
    return json.loads(clean)
448
 
449
def verify_claim(claim):
450
    results = tavily.search(claim, max_results=4)
451
    sources = [{"title":r.get("title",""),"url":r.get("url",""),"date":r.get("published_date","")} for r in results.get("results",[])]
452
    source_texts = "\n".join([f"- {r.get('title','')} ({r.get('url','')}): {r.get('content','')[:300]}" for r in results.get("results",[])])
453
    prompt = f"""You are a fact-checking AI. Analyze this claim against web evidence.
454
Claim: "{claim}"
455
Web Evidence:
456
{source_texts}
457
 
458
Classify as: VERIFIED, INACCURATE, FALSE, or NO_EVIDENCE.
459
Reply ONLY with this exact JSON (no markdown):
460
{{"verdict":"VERIFIED","explanation":"One clear sentence.","correct_fact":"Updated fact if wrong, else empty string.","ai_reasoning":"Brief note on which sources were checked and why confidence is high or low.","confidence":85}}
461
confidence is 0-100 integer."""
462
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
463
    clean = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
464
    data = json.loads(clean)
465
    data["sources"] = sources
466
    return data
467
 
468
def generate_ai_summary(results_list, verified, inaccurate, false_count, noev, total):
469
    bad = [c for c,r in results_list if r.get("verdict") in ["FALSE","INACCURATE"]][:3]
470
    prompt = f"""Write a 2-3 sentence professional AI fact-check summary.
471
Stats: {total} claims, {verified} verified, {inaccurate} inaccurate, {false_count} false, {noev} no evidence.
472
Sample problematic claims: {bad}
473
Write like: "This document contains X claims. Y appear verified, while Z contain outdated or unsupported data. Overall reliability is [assessment]."
474
Return ONLY the summary text."""
475
    r = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
476
    return r.choices[0].message.content.strip()
477
 
478
def compute_trust(verified, inaccurate, false_count, noev, total):
479
    if total == 0: return 50
480
    return max(0, min(100, int((verified*100 + inaccurate*50 + noev*40 + false_count*0) / total)))
481
 
482
def verdict_badge(verdict):
483
    return {
484
        "VERIFIED": '<span class="badge badge-verified">✅ Verified</span>',
485
        "INACCURATE": '<span class="badge badge-inaccurate">⚠️ Inaccurate</span>',
486
        "FALSE": '<span class="badge badge-false">❌ False</span>',
487
        "NO_EVIDENCE": '<span class="badge badge-noevidence">❓ No Evidence</span>',
488
    }.get(verdict, '<span class="badge badge-noevidence">❓ No Evidence</span>')
489
 
490
def css_class(verdict):
491
    return {"VERIFIED":"verified","INACCURATE":"inaccurate","FALSE":"false","NO_EVIDENCE":"noevidence"}.get(verdict,"noevidence")
492
 
493
def confidence_html(score):
494
    score = int(score) if score else 50
495
    cls = "conf-high" if score >= 70 else "conf-med" if score >= 45 else "conf-low"
496
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"
497
    return f"""<div class="conf-wrap">
498
        <div class="conf-label" style="color:{color};font-weight:600;">Confidence</div>
499
        <div class="conf-track"><div class="conf-fill {cls}" style="width:{score}%"></div></div>
500
        <div class="conf-pct" style="color:{color}">{score}%</div>
501
    </div>"""
502
 
503
def donut_chart(verified, inaccurate, false_count, noev, total):
504
    if total == 0: return ""
505
    cx, cy, r, circ = 75, 75, 55, 2*3.14159*55
506
    segments = [(verified/total,"#10b981"),(inaccurate/total,"#f59e0b"),(false_count/total,"#ef4444"),(noev/total,"#475569")]
507
    offset, paths = 0, []
508
    for ratio, color in segments:
509
        if ratio == 0: continue
510
        dash = ratio * circ
511
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="16" stroke-dasharray="{dash:.1f} {circ-dash:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
512
        offset += dash
513
    return f"""<svg viewBox="0 0 150 150" class="donut-svg">
514
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="16"/>
515
        {"".join(paths)}
516
        <text x="{cx}" y="{cy-6}" text-anchor="middle" fill="#f1f5f9" font-size="20" font-weight="800" font-family="Bricolage Grotesque,sans-serif">{total}</text>
517
        <text x="{cx}" y="{cy+12}" text-anchor="middle" fill="#64748b" font-size="10">claims</text>
518
    </svg>"""
519
 
520
# ═══════════════════════════════════════════════════════
521
# 🏠 HOME
522
# ═══════════════════════════════════════════════════════
523
if st.session_state.page == "Home":
524
    st.markdown("""
525
    <div class="hero-section">
526
        <div class="hero-badge">🛡️ AI-Powered Verification</div>
527
        <div class="hero-title">AI-Powered<br><span>Fact Checker</span></div>
528
        <p class="hero-sub">Upload a PDF and we'll find, verify & explain every factual claim using live web data and AI reasoning.</p>
529
        <ul class="hero-bullets">
530
            <li>Detect fake, outdated or misleading claims instantly</li>
531
            <li>Get correct facts with trusted, clickable source links</li>
532
            <li>Confidence scores and AI reasoning for every verdict</li>
533
            <li>Export clean, shareable fact-check reports</li>
534
        </ul>
535
    </div>
536
    """, unsafe_allow_html=True)
537
 
538
    st.markdown("""
539
    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:800;color:#f1f5f9;margin-bottom:1rem;">How It Works</div>
540
    <div class="steps-row">
541
        <div class="step-card"><div class="step-num">STEP 01</div><div class="step-icon">📤</div><div class="step-title">Upload PDF</div><div class="step-desc">Upload any document — report, research, article, or marketing material.</div></div>
542
        <div class="step-card"><div class="step-num">STEP 02</div><div class="step-icon">🧠</div><div class="step-title">Extract Claims</div><div class="step-desc">AI detects all verifiable stats, dates, figures, and facts.</div></div>
543
        <div class="step-card"><div class="step-num">STEP 03</div><div class="step-icon">🌐</div><div class="step-title">Verify on Web</div><div class="step-desc">Each claim is cross-checked against live web sources.</div></div>
544
        <div class="step-card"><div class="step-num">STEP 04</div><div class="step-icon">📊</div><div class="step-title">Get Report</div><div class="step-desc">Receive verdicts, confidence scores, sources, and correct facts.</div></div>
545
    </div>
546
    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:800;color:#f1f5f9;margin:1.75rem 0 1rem;">Features</div>
547
    <div class="features-grid">
548
        <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">Confidence Scores</div><div class="feature-desc">Each verdict includes a 0–100% confidence score based on source agreement.</div></div>
549
        <div class="feature-card"><div class="feature-icon">🔗</div><div class="feature-title">Live Source Links</div><div class="feature-desc">Every claim links to the real web sources used for verification.</div></div>
550
        <div class="feature-card"><div class="feature-icon">🤖</div><div class="feature-title">AI Reasoning</div><div class="feature-desc">Understand why each claim is flagged with detailed AI explanation.</div></div>
551
        <div class="feature-card"><div class="feature-icon">🔄</div><div class="feature-title">Before vs After</div><div class="feature-desc">See the uploaded claim vs the correct updated fact side by side.</div></div>
552
        <div class="feature-card"><div class="feature-icon">🚨</div><div class="feature-title">Suspicious Language</div><div class="feature-desc">Detects exaggerated marketing claims like "world's best" or "#1".</div></div>
553
        <div class="feature-card"><div class="feature-icon">📥</div><div class="feature-title">Export Report</div><div class="feature-desc">Download your full fact-check results as a clean report.</div></div>
554
    </div>
555
    """, unsafe_allow_html=True)
556
 
557
    c1, c2 = st.columns(2)
558
    with c1:
559
        if st.button("📤 Upload Your PDF"):
560
            st.session_state.page = "Upload PDF"; st.rerun()
561
    with c2:
562
        if st.button("📊 View Dashboard"):
563
            st.session_state.page = "Dashboard"; st.rerun()
564
 
565
# ═══════════════════════════════════════════════════════
566
# 📤 UPLOAD PDF
567
# ═══════════════════════════════════════════════════════
568
elif st.session_state.page == "Upload PDF":
569
    st.markdown('<div class="page-header"><div class="page-title">Upload Your PDF</div><div class="page-subtitle">Upload any document to start AI fact-checking.</div></div>', unsafe_allow_html=True)
570
 
571
    uploaded_file = st.file_uploader("Upload PDF (Max 50MB)", type="pdf", label_visibility="visible")
572
 
573
    if not uploaded_file:
574
        st.markdown("""
575
        <div class="drop-zone">
576
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">☁️</div>
577
            <div class="drop-title">Drag & drop your PDF here</div>
578
            <div class="drop-sub" style="margin-top:0.3rem;">or use the uploader above · PDF · Max 50MB</div>
579
        </div>
580
        """, unsafe_allow_html=True)
581
        st.markdown("<hr>", unsafe_allow_html=True)
582
        st.markdown('<div style="font-weight:700;color:#e2e8f0;margin-bottom:0.75rem;font-size:0.93rem;">📋 Try Our Sample PDFs</div>', unsafe_allow_html=True)
583
        st.markdown("""
584
        <div class="sample-grid">
585
            <div class="sample-card"><div style="font-size:2rem;margin-bottom:0.65rem;">📋</div><div class="sample-title">Demo PDF — Real Facts</div><div class="sample-desc">Contains accurate, verifiable claims and up-to-date statistics.</div></div>
586
            <div class="sample-card"><div style="font-size:2rem;margin-bottom:0.65rem;">⚠️</div><div class="sample-title">Trap PDF — Fake & Outdated</div><div class="sample-desc">Contains intentionally false and outdated statistics to test detection.</div></div>
587
        </div>
588
        """, unsafe_allow_html=True)
589
        st.info("🔒 Your PDF is processed securely. No data is stored or shared.")
590
    else:
591
        st.success(f"✅ **{uploaded_file.name}** is ready!")
592
        st.session_state.uploaded_file = uploaded_file
593
        st.session_state.results = None
594
        file_size = len(uploaded_file.getvalue()) / 1024
595
        st.markdown(f"""
596
        <div class="glass-card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
597
            <div>
598
                <div style="font-weight:700;color:#e2e8f0;">📄 {uploaded_file.name}</div>
599
                <div style="font-size:0.76rem;color:#64748b;margin-top:0.2rem;">Size: {file_size:.1f} KB · PDF Document</div>
600
            </div>
601
            <span class="badge badge-verified">Ready</span>
602
        </div>
603
        """, unsafe_allow_html=True)
604
        if st.button("🚀 Start Fact Checking"):
605
            st.session_state.page = "Fact Check"; st.rerun()
606
 
607
# ═══════════════════════════════════════════════════════
608
# ✅ FACT CHECK
609
# ═══════════════════════════════════════════════════════
610
elif st.session_state.page == "Fact Check":
611
    uploaded_file = st.session_state.get("uploaded_file")
612
 
613
    if uploaded_file is None:
614
        st.markdown('<div class="page-header"><div class="page-title">Fact Check</div></div>', unsafe_allow_html=True)
615
        st.warning("⚠️ No PDF uploaded. Please go to Upload PDF first.")
616
        if st.button("Go to Upload PDF"):
617
            st.session_state.page = "Upload PDF"; st.rerun()
618
 
619
    elif st.session_state.results is None:
620
        st.markdown('<div class="page-header"><div class="page-title">Fact Check in Progress</div><div class="page-subtitle">Please wait while we extract and verify claims from your document.</div></div>', unsafe_allow_html=True)
621
 
622
        stepper = st.empty()
623
        def render_stepper(active):
624
            steps = [("📄","Reading PDF","Extracting text from document"),("🧠","Extracting Claims","AI identifying verifiable facts"),("🌐","Searching Web","Live web search for each claim"),("🔍","Verifying Facts","Cross-referencing sources"),("📊","Generating Report","Compiling your fact-check report")]
625
            html = '<div class="process-stepper">'
626
            for i,(icon,title,sub) in enumerate(steps):
627
                if i < active: state,color,show = "done","#10b981","✓"
628
                elif i == active: state,color,show = "active","#6366f1",icon
629
                else: state,color,show = "pending","#2d3748",icon
630
                bg = "rgba(16,185,129,.1)" if state=="done" else "rgba(99,102,241,.1)" if state=="active" else "rgba(255,255,255,.04)"
631
                tc = "#10b981" if state=="done" else "#e2e8f0" if state=="active" else "#4a5568"
632
                html += f'<div class="process-step"><div class="step-indicator {state}" style="background:{bg};"><span style="color:{color}">{show}</span></div><div><div class="step-text-title" style="color:{tc}">{title}</div><div class="step-text-sub">{sub}</div></div></div>'
633
            stepper.markdown(html + "</div>", unsafe_allow_html=True)
634
 
635
        progress_bar = st.progress(0)
636
        status_txt = st.empty()
637
 
638
        render_stepper(0)
639
        try:
640
            text = extract_text(uploaded_file)
641
            suspicious_phrases = find_suspicious(text)
642
        except Exception as e:
643
            st.error(f"❌ Could not read PDF: {e}"); st.stop()
644
 
645
        render_stepper(1)
646
        try:
647
            claims = extract_claims(text)
648
        except Exception as e:
649
            st.error(f"❌ Claim extraction failed: {e}"); claims = []
650
 
651
        if not claims:
652
            st.warning("⚠️ No verifiable claims found. Try a PDF with statistics or factual data."); st.stop()
653
 
654
        render_stepper(2)
655
        verified_count = inaccurate_count = false_count = noev_count = 0
656
        results_list = []
657
 
658
        for i, claim in enumerate(claims):
659
            render_stepper(3)
660
            status_txt.markdown(f'<div style="font-size:0.8rem;color:#64748b;padding:0.4rem 0;">🔎 Verifying <b style="color:#818cf8">{i+1}</b> of <b>{len(claims)}</b>: <span style="color:#94a3b8;font-style:italic;">{claim[:70]}...</span></div>', unsafe_allow_html=True)
661
            try:
662
                result = verify_claim(claim)
663
            except:
664
                result = {"verdict":"NO_EVIDENCE","explanation":"Could not verify.","correct_fact":"","ai_reasoning":"Verification failed.","confidence":0,"sources":[]}
665
            results_list.append((claim, result))
666
            v = result.get("verdict","NO_EVIDENCE")
667
            if v=="VERIFIED": verified_count+=1
668
            elif v=="INACCURATE": inaccurate_count+=1
669
            elif v=="FALSE": false_count+=1
670
            else: noev_count+=1
671
            progress_bar.progress((i+1)/len(claims))
672
 
673
        render_stepper(4)
674
        status_txt.empty()
675
 
676
        try:
677
            ai_summary = generate_ai_summary(results_list, verified_count, inaccurate_count, false_count, noev_count, len(claims))
678
        except:
679
            ai_summary = f"This document contains {len(claims)} factual claims. {verified_count} verified, {inaccurate_count} inaccurate, {false_count} false."
680
 
681
        trust_score = compute_trust(verified_count, inaccurate_count, false_count, noev_count, len(claims))
682
 
683
        st.session_state.results = {
684
            "filename": uploaded_file.name,
685
            "date": datetime.now().strftime("%b %d, %Y · %H:%M"),
686
            "claims": results_list,
687
            "verified": verified_count, "inaccurate": inaccurate_count,
688
            "false": false_count, "noevidence": noev_count,
689
            "total": len(claims), "trust_score": trust_score,
690
            "ai_summary": ai_summary, "suspicious": suspicious_phrases,
691
        }
692
        st.session_state.history.append({**st.session_state.results, "claims": None})
693
        st.rerun()
694
 
695
    else:
696
        r = st.session_state.results
697
        trust = r.get("trust_score", 70)
698
        risk_label = "Low Risk" if trust >= 70 else "Medium Risk" if trust >= 45 else "High Risk"
699
        risk_cls = "risk-low" if trust >= 70 else "risk-med" if trust >= 45 else "risk-high"
700
 
701
        st.markdown(f'<div class="page-header"><div class="page-title">✅ Fact Check Complete</div><div class="page-subtitle">📄 {r["filename"]} · {r["date"]}</div></div>', unsafe_allow_html=True)
702
 
703
        st.markdown(f'<div class="ai-summary"><div class="ai-summary-label">🤖 AI Summary</div><div class="ai-summary-text">{r.get("ai_summary","")}</div></div>', unsafe_allow_html=True)
704
 
705
        col_trust, col_metrics = st.columns([1, 3])
706
        with col_trust:
707
            st.markdown(f"""<div class="trust-score-card">
708
                <div style="font-size:0.65rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem;">Trust Score</div>
709
                <div class="trust-score-num">{trust}</div>
710
                <div style="font-size:0.65rem;color:#64748b;">/100</div>
711
                <div><span class="risk-badge {risk_cls}">{risk_label}</span></div>
712
            </div>""", unsafe_allow_html=True)
713
        with col_metrics:
714
            st.markdown(f"""<div class="metrics-grid">
715
                <div class="metric-card metric-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
716
                <div class="metric-card metric-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
717
                <div class="metric-card metric-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
718
                <div class="metric-card metric-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
719
            </div>""", unsafe_allow_html=True)
720
 
721
        if r.get("suspicious"):
722
            chips = "".join([f'<span class="suspicious-chip">"{p}"</span>' for p in r["suspicious"]])
723
            st.markdown(f'<div class="glass-card" style="border-color:rgba(249,115,22,.2);margin-bottom:1rem;"><div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#f97316;margin-bottom:.5rem;">🚨 Suspicious Marketing Language Detected</div><div class="suspicious-list">{chips}</div></div>', unsafe_allow_html=True)
724
 
725
        c1, c2, c3 = st.columns(3)
726
        with c1:
727
            if st.button("📊 View Dashboard"):
728
                st.session_state.page = "Dashboard"; st.rerun()
729
        with c2:
730
            if st.button("🔄 Check Another PDF"):
731
                st.session_state.results = None; st.session_state.uploaded_file = None
732
                st.session_state.page = "Upload PDF"; st.rerun()
733
        with c3:
734
            lines = [f"FactChecker AI — {r['filename']}",f"Date: {r['date']}",f"Trust Score: {trust}/100 ({risk_label})",f"Total: {r['total']} | Verified: {r['verified']} | Inaccurate: {r['inaccurate']} | False: {r['false']}","",f"AI Summary: {r.get('ai_summary','')}","","="*60,""]
735
            for i,(claim,res) in enumerate(r["claims"],1):
736
                lines += [f"{i}. [{res.get('verdict','?')}] {claim}",f"   Explanation: {res.get('explanation','')}",f"   Confidence: {res.get('confidence',0)}%"]
737
                if res.get("correct_fact"): lines.append(f"   Correct Fact: {res['correct_fact']}")
738
                if res.get("ai_reasoning"): lines.append(f"   AI Reasoning: {res['ai_reasoning']}")
739
                for s in res.get("sources",[])[:2]:
740
                    if s.get("url"): lines.append(f"   Source: {s['url']}")
741
                lines.append("")
742
            st.download_button("📥 Download Report", data="\n".join(lines), file_name=f"factcheck_{r['filename']}.txt", mime="text/plain")
743
 
744
        st.markdown("<hr>", unsafe_allow_html=True)
745
        st.markdown('<div style="font-family:Bricolage Grotesque,sans-serif;font-size:1.05rem;font-weight:800;color:#f1f5f9;margin-bottom:1rem;">📋 Detailed Results</div>', unsafe_allow_html=True)
746
 
747
        for claim, result in r["claims"]:
748
            verdict = result.get("verdict","NO_EVIDENCE")
749
            c_class = css_class(verdict)
750
            correct = result.get("correct_fact","")
751
            sources = result.get("sources",[])
752
            confidence = result.get("confidence",50)
753
            ai_reason = result.get("ai_reasoning","")
754
 
755
            if correct and verdict in ["FALSE","INACCURATE"]:
756
                extra = f'<div class="before-after"><div class="before-box"><div class="ba-label">❌ Uploaded Claim</div><div class="ba-text">{claim}</div></div><div class="after-box"><div class="ba-label">✅ Correct Fact</div><div class="ba-text">{correct}</div></div></div>'
757
            elif correct:
758
                extra = f'<div class="ai-reasoning"><div class="ai-reasoning-label">📌 Correct Fact</div><div class="ai-reasoning-text">{correct}</div></div>'
759
            else:
760
                extra = ""
761
 
762
            reasoning = f'<div class="ai-reasoning"><div class="ai-reasoning-label">🤖 AI Reasoning</div><div class="ai-reasoning-text">{ai_reason}</div></div>' if ai_reason else ""
763
            src_links = "".join([f'<a class="source-chip" href="{s["url"]}" target="_blank">🔗 {(s["title"] or s["url"])[:38]}...</a>' for s in sources[:3] if s.get("url")])
764
            sources_html = f'<div class="sources-list">{src_links}</div>' if src_links else ""
765
 
766
            st.markdown(f"""<div class="claim-card {c_class}">
767
                <div class="claim-header">
768
                    <div class="claim-text">{claim}</div>
769
                    <div>{verdict_badge(verdict)}</div>
770
                </div>
771
                <div class="claim-explanation">{result.get('explanation','')}</div>
772
                {confidence_html(confidence)}
773
                {extra}{reasoning}{sources_html}
774
            </div>""", unsafe_allow_html=True)
775
 
776
# ═══════════════════════════════════════════════════════
777
# 📊 DASHBOARD
778
# ═══════════════════════════════════════════════════════
779
elif st.session_state.page == "Dashboard":
780
    st.markdown('<div class="page-header"><div class="page-title">📊 Dashboard</div><div class="page-subtitle">Analytics and overview of your last fact check.</div></div>', unsafe_allow_html=True)
781
 
782
    r = st.session_state.results
783
    if r is None:
784
        st.info("No results yet. Upload a PDF to get started.")
785
        if st.button("Go to Upload PDF"):
786
            st.session_state.page = "Upload PDF"; st.rerun()
787
    else:
788
        total = r["total"] or 1
789
        trust = r.get("trust_score",70)
790
        color = "#10b981" if trust>=70 else "#f59e0b" if trust>=45 else "#ef4444"
791
 
792
        st.markdown(f"""<div class="metrics-grid">
793
            <div class="metric-card metric-total"><div class="metric-num">{r['total']}</div><div class="metric-label">Total Claims</div></div>
794
            <div class="metric-card metric-verified"><div class="metric-num">{r['verified']}</div><div class="metric-label">✅ Verified</div></div>
795
            <div class="metric-card metric-inaccurate"><div class="metric-num">{r['inaccurate']}</div><div class="metric-label">⚠️ Inaccurate</div></div>
796
            <div class="metric-card metric-false"><div class="metric-num">{r['false']}</div><div class="metric-label">❌ False</div></div>
797
        </div>""", unsafe_allow_html=True)
798
 
799
        donut = donut_chart(r["verified"],r["inaccurate"],r["false"],r["noevidence"],r["total"])
800
        st.markdown(f"""<div class="charts-row">
801
            <div class="chart-card">
802
                <div class="chart-title">Claim Distribution</div>
803
                {donut}
804
                <div style="margin-top:0.75rem;">
805
                    <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>Verified ({r['verified']})</div>
806
                    <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Inaccurate ({r['inaccurate']})</div>
807
                    <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>False ({r['false']})</div>
808
                    <div class="legend-item"><div class="legend-dot" style="background:#475569"></div>No Evidence ({r['noevidence']})</div>
809
                </div>
810
            </div>
811
            <div class="chart-card">
812
                <div class="chart-title">Verification Breakdown</div>
813
                <div class="bar-row"><div class="bar-label">✅ Verified</div><div class="bar-track"><div style="width:{r['verified']/total*100:.0f}%;background:#10b981;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['verified']/total*100:.0f}%</div></div>
814
                <div class="bar-row"><div class="bar-label">⚠️ Inaccurate</div><div class="bar-track"><div style="width:{r['inaccurate']/total*100:.0f}%;background:#f59e0b;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['inaccurate']/total*100:.0f}%</div></div>
815
                <div class="bar-row"><div class="bar-label">❌ False</div><div class="bar-track"><div style="width:{r['false']/total*100:.0f}%;background:#ef4444;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['false']/total*100:.0f}%</div></div>
816
                <div class="bar-row"><div class="bar-label">❓ No Evidence</div><div class="bar-track"><div style="width:{r['noevidence']/total*100:.0f}%;background:#475569;height:10px;border-radius:100px;"></div></div><div class="bar-val">{r['noevidence']/total*100:.0f}%</div></div>
817
                <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.06);">
818
                    <div style="font-size:0.72rem;color:#64748b;margin-bottom:0.3rem;">Trust Score</div>
819
                    <div style="font-family:'Bricolage Grotesque',sans-serif;font-size:1.8rem;font-weight:800;color:{color};">{trust}/100</div>
820
                </div>
821
            </div>
822
        </div>""", unsafe_allow_html=True)
823
 
824
        if r.get("ai_summary"):
825
            st.markdown(f'<div class="ai-summary"><div class="ai-summary-label">🤖 AI Summary</div><div class="ai-summary-text">{r["ai_summary"]}</div></div>', unsafe_allow_html=True)
826
 
827
        if st.button("📋 View Detailed Results"):
828
            st.session_state.page = "Fact Check"; st.rerun()
829
 
830
# ═══════════════════════════════════════════════════════
831
# 🕐 HISTORY
832
# ═══════════════════════════════════════════════════════
833
elif st.session_state.page == "History":
834
    st.markdown('<div class="page-header"><div class="page-title">🕐 History</div><div class="page-subtitle">All your previously fact-checked documents.</div></div>', unsafe_allow_html=True)
835
 
836
    if not st.session_state.history:
837
        st.markdown('<div style="text-align:center;padding:3rem;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:16px;"><div style="font-size:2.5rem;margin-bottom:1rem;">🕐</div><div style="font-weight:700;color:#e2e8f0;margin-bottom:.5rem;">No history yet</div><div style="font-size:.83rem;color:#4a5568;">Your fact-check results will appear here after analyzing a PDF.</div></div>', unsafe_allow_html=True)
838
    else:
839
        st.markdown('<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:.5rem 1.25rem;font-size:.66rem;font-weight:700;color:#4a5568;text-transform:uppercase;letter-spacing:.08em;"><div>Document</div><div>Total</div><div>✅</div><div>⚠️</div><div>❌</div><div>Date</div></div>', unsafe_allow_html=True)
840
        for h in reversed(st.session_state.history):
841
            trust = h.get("trust_score",70)
842
            tc = "#10b981" if trust>=70 else "#f59e0b" if trust>=45 else "#ef4444"
843
            st.markdown(f'<div style="display:grid;grid-template-columns:2fr .6fr .6fr .6fr .6fr 1fr;gap:1rem;padding:1rem 1.25rem;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;margin-bottom:.5rem;align-items:center;"><div><div style="font-weight:600;color:#e2e8f0;font-size:.87rem;">📄 {h["filename"]}</div><div style="font-size:.68rem;color:#4a5568;margin-top:.15rem;">Trust: <span style="color:{tc};font-weight:700;">{trust}/100</span></div></div><div style="font-weight:700;color:#e2e8f0;">{h["total"]}</div><div style="color:#10b981;font-weight:700;">{h["verified"]}</div><div style="color:#f59e0b;font-weight:700;">{h["inaccurate"]}</div><div style="color:#ef4444;font-weight:700;">{h["false"]}</div><div style="font-size:.76rem;color:#4a5568;">{h["date"]}</div></div>', unsafe_allow_html=True)
