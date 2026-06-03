GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');

:root {
    --bg: #0D0D0D;
    --surface: #141414;
    --surface-2: #1C1C1C;
    --border: #2A2A2A;
    --border-bright: #3A3A3A;
    --amber: #E8A838;
    --amber-dim: #C4892A;
    --chartreuse: #C8F135;
    --red: #FF4545;
    --ice: #38C8E8;
    --text: #F0EDE6;
    --text-muted: #7A7A7A;
    --critical: #FF4545;
    --high: #FF8C42;
    --medium: #E8C838;
    --low: #4FD180;
}

/* ── 1. STREAMLIT CHROME REMOVAL ────────────────────────────────────────── */
#MainMenu, header, footer {
    visibility: hidden !important;
}
.block-container {
    padding-top: 1.5rem !important;
    max-width: 100% !important;
}
body, .stApp {
    background: var(--bg) !important;
}
body, .stApp, .stApp * {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

/* ── 2. SIDEBAR STYLING ────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0A0A0A !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] .stMarkdown h4,
section[data-testid="stSidebar"] .stMarkdown h5,
section[data-testid="stSidebar"] .stMarkdown h6 {
    font-family: 'Space Mono', monospace !important;
    color: var(--amber) !important;
    font-size:14px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}
/* Sidebar radio — left border highlight */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    border-left: 3px solid transparent;
    padding-left: 8px;
    transition: all 0.15s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    border-left: 3px solid var(--amber) !important;
    background: rgba(232,168,56,0.07) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label input {
    display: none;
}

/* ── 3. BUTTON STYLING ─────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--amber) !important;
    color: var(--amber) !important;
    font-family: 'Space Mono', monospace !important;
    font-size:15px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 24px !important;
    border-radius: 2px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: var(--amber) !important;
    color: #0D0D0D !important;
    box-shadow: 0 0 18px rgba(232,168,56,0.35) !important;
}
.stButton > button[kind="primary"],
.stButton > button.primary-btn {
    background: var(--amber) !important;
    color: #0D0D0D !important;
    border-color: var(--amber) !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 24px rgba(232,168,56,0.5) !important;
}

/* ── 4. FILE UPLOADER ──────────────────────────────────────────────────── */
.stFileUploader section {
    border: 2px dashed var(--border-bright) !important;
    background: var(--surface) !important;
    border-radius: 4px !important;
    padding: 32px !important;
    text-align: center !important;
    transition: border-color 0.2s ease !important;
}
.stFileUploader section:hover {
    border-color: var(--amber) !important;
    background: rgba(232,168,56,0.03) !important;
}
.stFileUploader section small,
.stFileUploader section span {
    color: var(--text-muted) !important;
    font-family: 'Space Mono', monospace !important;
}

/* ── 5. METRIC CARDS ───────────────────────────────────────────────────── */
div[data-testid="stMetric"],
div[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    padding: 16px 20px !important;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetricLabel"] {
    font-family: 'Space Mono', monospace !important;
    font-size:13px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size:33px !important;
    color: var(--amber) !important;
    font-weight: 700 !important;
}

/* ── 6. DATAFRAME ──────────────────────────────────────────────────────── */
div[data-testid="stDataFrame"],
.stDataFrame {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
}
.stDataFrame thead th {
    background: var(--surface) !important;
    color: var(--amber) !important;
    font-family: 'Space Mono', monospace !important;
    font-size:13px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
.stDataFrame tbody tr:nth-child(even) {
    background: rgba(255,255,255,0.02) !important;
}
.stDataFrame tbody td {
    font-family: 'JetBrains Mono', monospace !important;
    font-size:15px !important;
    color: var(--text) !important;
}

/* ── 7. PROGRESS BAR ──────────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: var(--amber) !important;
}
.stProgress > div > div {
    background: var(--border) !important;
}

/* ── 8. EXPANDER ───────────────────────────────────────────────────────── */
.streamlit-expanderHeader,
div[data-testid="stExpander"] summary {
    font-family: 'Space Mono', monospace !important;
    font-size:15px !important;
    color: var(--text) !important;
}
div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    background: var(--surface) !important;
}
div[data-testid="stExpander"]:hover {
    border-color: var(--amber) !important;
}

/* ── 9. INFO / WARNING / ERROR / SUCCESS ───────────────────────────────── */
div[data-testid="stAlert"][data-baseweb*="notification"] {
    border-radius: 0 3px 3px 0 !important;
}
.stAlert .st-emotion-cache-icon,
.stAlert svg {
    display: none !important;
}
div[role="alert"].stInfo,
div[data-testid="stNotification"][kind="info"] {
    background: rgba(56,200,232,0.08) !important;
    border-left: 3px solid var(--ice) !important;
    color: var(--text) !important;
}
div[role="alert"].stWarning,
div[data-testid="stNotification"][kind="warning"] {
    background: rgba(232,200,56,0.08) !important;
    border-left: 3px solid var(--medium) !important;
    color: var(--text) !important;
}
div[role="alert"].stError,
div[data-testid="stNotification"][kind="error"] {
    background: rgba(255,69,69,0.08) !important;
    border-left: 3px solid var(--red) !important;
    color: var(--text) !important;
}
div[role="alert"].stSuccess,
div[data-testid="stNotification"][kind="success"] {
    background: rgba(79,209,128,0.08) !important;
    border-left: 3px solid var(--low) !important;
    color: var(--text) !important;
}

/* ── 10. SELECT / MULTISELECT ──────────────────────────────────────────── */
.stSelectbox, .stMultiSelect {
    background: var(--surface) !important;
}
.stSelectbox > div, .stMultiSelect > div {
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
}
.stSelectbox > div:focus-within, .stSelectbox > div:hover,
.stMultiSelect > div:focus-within, .stMultiSelect > div:hover {
    border-color: var(--amber) !important;
}
.stMultiSelect span[data-baseweb="tag"] {
    background: rgba(232,168,56,0.15) !important;
    border: 1px solid var(--amber-dim) !important;
    color: var(--amber) !important;
    font-family: 'Space Mono', monospace !important;
    font-size:13px !important;
    border-radius: 2px !important;
}

/* ── 11. SLIDER ────────────────────────────────────────────────────────── */
.stSlider > div > div > div {
    background: var(--border) !important;
}
.stSlider > div > div > div > div {
    background: var(--amber) !important;
}
.stSlider > div > div > div > div > div {
    background: var(--amber) !important;
    border: 2px solid var(--bg) !important;
    width: 16px !important;
    height: 16px !important;
    border-radius: 50% !important;
}

/* ── 12. TOGGLE ────────────────────────────────────────────────────────── */
div[data-testid="stToggle"] label span[data-testid="stToggleSlider"] {
    background: var(--border-bright) !important;
}
div[data-testid="stToggle"] label input:checked + span[data-testid="stToggleSlider"] {
    background: var(--amber) !important;
}

/* ── 13. FORM ──────────────────────────────────────────────────────────── */
div[data-testid="stForm"] {
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    border-radius: 4px !important;
    padding: 24px !important;
}

/* ── 14. SCANLINE OVERLAY ──────────────────────────────────────────────── */
body::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── 15. CUSTOM SCROLLBAR ──────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: var(--bg);
}
::-webkit-scrollbar-thumb {
    background: var(--border-bright);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--amber);
}

/* ── 16. KEYFRAME ANIMATIONS ──────────────────────────────────────────── */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseAmber {
    0%, 100% { box-shadow: 0 0 0 0 rgba(232,168,56,0); }
    50%      { box-shadow: 0 0 0 8px rgba(232,168,56,0.15); }
}
@keyframes scanLine {
    from { top: 0; }
    to   { top: 100%; }
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0; }
}
@keyframes glitch {
    0%, 100% { clip-path: inset(0 0 98% 0); }
    20%      { clip-path: inset(33% 0 33% 0); }
    40%      { clip-path: inset(66% 0 0 0); }
    60%      { clip-path: inset(10% 0 70% 0); }
    80%      { clip-path: inset(80% 0 5% 0); }
}
@keyframes typewriter {
    from { width: 0; }
    to   { width: 100%; }
}
@keyframes counterUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes ticker {
    from { transform: translateX(0); }
    to   { transform: translateX(-50%); }
}
@keyframes pulseDot {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(79,209,128,0.4); }
    50%      { opacity: 0.7; box-shadow: 0 0 0 6px rgba(79,209,128,0); }
}

/* ── 17. UTILITY CLASSES ──────────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    font-family: 'Space Mono', monospace;
    font-size:13px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 2px;
}
.badge-critical {
    background: rgba(255,69,69,0.15);
    color: var(--red);
    border: 1px solid var(--red);
}
.badge-high {
    background: rgba(255,140,66,0.15);
    color: var(--high);
    border: 1px solid var(--high);
}
.badge-medium {
    background: rgba(232,200,56,0.15);
    color: var(--medium);
    border: 1px solid var(--medium);
}
.badge-low {
    background: rgba(79,209,128,0.15);
    color: var(--low);
    border: 1px solid var(--low);
}
.badge-info {
    background: rgba(56,200,232,0.12);
    color: var(--ice);
    border: 1px solid var(--ice);
}
.mono {
    font-family: 'JetBrains Mono', monospace !important;
}
.caption-label {
    font-family: 'Space Mono', monospace;
    font-size:13px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
}
.animate-fadein {
    animation: fadeSlideUp 0.4s ease both;
}
.animate-fadein-2 {
    animation: fadeSlideUp 0.4s ease 0.1s both;
}
.animate-fadein-3 {
    animation: fadeSlideUp 0.4s ease 0.2s both;
}
.glow-amber {
    box-shadow: 0 0 20px rgba(232,168,56,0.2);
    border-color: var(--amber);
}

/* ── FEATURE CARDS (landing page) ──────────────────────────────────────── */
.feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 24px;
    transition: all 0.2s ease;
    cursor: default;
    height: 100%;
}
.feature-card:hover {
    border-color: var(--amber);
    background: rgba(232,168,56,0.03);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.feature-card .card-icon {
    font-size:23px;
    color: var(--amber);
}
.feature-card .card-title {
    font-family: 'Space Mono', monospace;
    font-size:17px;
    font-weight: 700;
    color: var(--text);
    margin: 12px 0 8px;
    letter-spacing: 0.04em;
}
.feature-card .card-desc {
    font-family: 'DM Sans', sans-serif;
    font-size:16px;
    color: var(--text-muted);
    line-height: 1.6;
    margin: 0 0 14px;
}
.feature-card .card-icon-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.feature-card .card-footer-line {
    padding-top: 12px;
    border-top: 1px solid var(--border);
}

/* ── STATS TICKER ──────────────────────────────────────────────────────── */
.stats-ticker-wrap {
    overflow: hidden;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    padding: 10px 0;
    margin-top: 24px;
}
.stats-ticker {
    display: flex;
    gap: 0;
    white-space: nowrap;
    animation: ticker 25s linear infinite;
}
.ticker-item {
    font-family: 'Space Mono', monospace;
    font-size:13px;
    color: var(--text-muted);
    padding: 0 24px;
    letter-spacing: 0.08em;
}
.ticker-sep {
    color: var(--border-bright);
    padding: 0 8px;
    font-family: 'Space Mono', monospace;
    font-size:13px;
}

/* ── PAGE LINK STYLING ─────────────────────────────────────────────────── */
a[data-testid="stPageLink-NavLink"] {
    font-family: 'Space Mono', monospace !important;
    font-size:15px !important;
    letter-spacing: 0.04em !important;
    color: var(--text-muted) !important;
    border-left: 3px solid transparent;
    padding-left: 10px !important;
    transition: all 0.15s ease;
}
a[data-testid="stPageLink-NavLink"]:hover {
    color: var(--amber) !important;
    border-left-color: var(--amber);
    background: rgba(232,168,56,0.05) !important;
}

/* ── DOWNLOAD BUTTON ───────────────────────────────────────────────────── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--amber) !important;
    color: var(--amber) !important;
    font-family: 'Space Mono', monospace !important;
    font-size:15px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 24px !important;
    border-radius: 2px !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: var(--amber) !important;
    color: #0D0D0D !important;
    box-shadow: 0 0 18px rgba(232,168,56,0.35) !important;
}

/* ── TABS ──────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size:14px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text);
}
.stTabs [aria-selected="true"] {
    color: var(--amber) !important;
    border-bottom-color: var(--amber) !important;
}

/* THEME v2.0 — NOIR AMBER — PDF COMPLIANCE SCANNER */
</style>
"""
