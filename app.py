import warnings
warnings.filterwarnings("ignore")

import streamlit as st

st.set_page_config(
    page_title="DisasterIQ — Disaster Response Allocator",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
  }

  /* ── Global background ── */
  .stApp { background: #080E1A !important; }
  .main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
  }

  /* ── Hide default streamlit chrome ── */
  header[data-testid="stHeader"] { display: none !important; }
  [data-testid="stSidebar"] { display: none !important; }
  #MainMenu { display: none !important; }
  footer { display: none !important; }

  /* ── Top navbar ── */
  .navbar {
    position: sticky; top: 0; z-index: 9999;
    background: rgba(8,14,26,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 0 32px;
    display: flex; align-items: center; gap: 0;
    height: 56px;
  }
  .navbar-brand {
    display: flex; align-items: center; gap: 10px;
    margin-right: 40px;
    text-decoration: none;
  }
  .navbar-logo {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, #EF4444, #F97316);
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
  }
  .navbar-title { font-size: 16px; font-weight: 700; color: #F1F5F9; }
  .navbar-sub   { font-size: 10px; color: #475569; font-weight: 400; }
  .nav-link {
    padding: 6px 16px; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-weight: 500; color: #64748B;
    transition: all .18s; white-space: nowrap;
    border: none; background: transparent;
  }
  .nav-link:hover { color: #E2E8F0; background: rgba(255,255,255,0.05); }
  .nav-link.active { color: #F1F5F9; background: rgba(59,130,246,0.18); }
  .nav-spacer { flex: 1; }
  .live-badge {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: #10B981; font-weight: 500;
    padding: 4px 10px; border-radius: 20px;
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.2);
  }
  .live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: pulse 1.6s infinite;
  }
  @keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.5; transform:scale(1.3); }
  }

  /* ── KPI stat cards ── */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    padding: 20px 24px 8px;
  }
  .kpi-card {
    border-radius: 12px;
    padding: 14px 16px;
    position: relative; overflow: hidden;
    transition: transform .18s, box-shadow .18s;
    cursor: default;
  }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.4); }
  .kpi-label  { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; opacity: .78; margin-bottom: 6px; }
  .kpi-value  { font-size: 26px; font-weight: 800; letter-spacing: -.02em; }
  .kpi-delta  { font-size: 10px; margin-top: 4px; opacity: .7; font-weight: 500; }
  .kpi-icon   { position:absolute; right:12px; top:50%; transform:translateY(-50%); font-size:28px; opacity:.15; }

  /* card colour themes */
  .kpi-blue   { background: linear-gradient(135deg,#1d4ed8,#2563eb); color:#fff; }
  .kpi-red    { background: linear-gradient(135deg,#b91c1c,#ef4444); color:#fff; }
  .kpi-green  { background: linear-gradient(135deg,#065f46,#10b981); color:#fff; }
  .kpi-orange { background: linear-gradient(135deg,#92400e,#f59e0b); color:#fff; }
  .kpi-purple { background: linear-gradient(135deg,#5b21b6,#8b5cf6); color:#fff; }
  .kpi-dark   { background: linear-gradient(135deg,#1e293b,#334155); color:#fff; }

  /* ── Panel cards ── */
  .panel {
    background: #0D1525;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    overflow: hidden;
  }
  .panel-header {
    padding: 14px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    display: flex; align-items: center; justify-content: space-between;
    font-size: 13px; font-weight: 600; color: #E2E8F0;
  }
  .panel-body { padding: 14px 18px; }

  /* ── Feed items ── */
  .feed-item {
    display: flex; gap: 12px; align-items: flex-start;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    transition: background .15s;
  }
  .feed-item:last-child { border-bottom: none; }
  .feed-icon {
    width: 34px; height: 34px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
  }
  .feed-text { font-size: 12px; color: #94A3B8; line-height: 1.5; }
  .feed-meta { font-size: 10px; color: #475569; margin-top: 3px; display:flex; gap:8px; align-items:center; }
  .feed-location { color: #38BDF8; font-weight: 500; }

  /* ── Urgency badges ── */
  .badge {
    display: inline-block;
    padding: 2px 9px; border-radius: 20px;
    font-size: 10px; font-weight: 600;
  }
  .badge-high   { background: rgba(239,68,68,.15);  color: #EF4444; }
  .badge-medium { background: rgba(245,158,11,.15); color: #F59E0B; }
  .badge-low    { background: rgba(16,185,129,.15); color: #10B981; }
  .badge-info   { background: rgba(59,130,246,.15); color: #3B82F6; }

  /* ── Resource row ── */
  .resource-row {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 12px; color: #CBD5E1;
  }
  .resource-row:last-child { border-bottom: none; }
  .res-icon { font-size: 20px; width: 28px; text-align:center; }

  /* ── Input overrides ── */
  .stTextArea textarea,
  .stTextInput input,
  .stSelectbox > div > div {
    background: #0D1525 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #E2E8F0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
  }
  .stTextArea textarea:focus,
  .stTextInput input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.15) !important;
  }

  /* ── Buttons ── */
  .stButton button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: #fff !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 13px !important; padding: 9px 22px !important;
    transition: all .18s !important;
  }
  .stButton button:hover {
    background: linear-gradient(135deg,#1e40af,#1d4ed8) !important;
    box-shadow: 0 4px 14px rgba(37,99,235,.4) !important;
    transform: translateY(-1px) !important;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 8px !important; padding: 4px !important; gap: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #64748B !important;
    border-radius: 6px !important; font-size: 13px !important;
    padding: 6px 20px !important; font-weight: 500 !important;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(59,130,246,.2) !important; color: #93C5FD !important;
  }

  /* ── Dataframe ── */
  [data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden; }
  .stDataFrame iframe { background: #0D1525 !important; }

  /* ── Spinner ── */
  .stSpinner > div { border-top-color: #3B82F6 !important; }

  /* ── Section padding ── */
  .section-pad { padding: 0 24px 20px; }

  /* ── Plotly ── */
  .js-plotly-plot .plotly { background: transparent !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: #080E1A; }
  ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 4px; }

  /* ── Alert colors ── */
  .stAlert { border-radius: 8px !important; }
  [data-testid="stAlert"][data-baseweb="notification"] {
    background: #0f2a1a !important; border-color: #10B981 !important; color: #6EE7B7 !important;
  }

  /* ── Expander ── */
  .streamlit-expanderHeader {
    background: #0D1525 !important; color: #CBD5E1 !important;
    border-radius: 8px !important; font-size: 13px !important;
  }
  .streamlit-expanderContent {
    background: #080E1A !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
  }

  /* ── Toggle ── */
  .stCheckbox label, .stRadio label { color: #CBD5E1 !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# ── Top Navigation Bar ────────────────────────────────────────────────────────
pages = ["Overview", "AI Processor", "Resource Map", "Analytics", "Settings"]
page_icons = {"Overview":"🏠","AI Processor":"🤖","Resource Map":"🗺️","Analytics":"📊","Settings":"⚙️"}

cols = st.columns([3, 8, 2])
with cols[0]:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:10px 0;">
      <div style="width:36px;height:36px;border-radius:9px;
           background:linear-gradient(135deg,#EF4444,#F97316);
           display:flex;align-items:center;justify-content:center;font-size:19px;">🚨</div>
      <div>
        <div style="font-size:16px;font-weight:800;color:#F1F5F9;letter-spacing:-.02em;">DisasterIQ</div>
        <div style="font-size:10px;color:#475569;font-weight:400;">Response Allocator v2.0</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    nav_cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        with nav_cols[i]:
            active = "🔵 " if st.session_state.page == p else ""
            label = f"{active}{page_icons[p]} {p}"
            if st.button(label, key=f"nav_{p}", use_container_width=True):
                st.session_state.page = p
                st.rerun()

with cols[2]:
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:flex-end;height:100%;padding-top:8px;">
      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#10B981;
           padding:5px 12px;border-radius:20px;background:rgba(16,185,129,0.1);
           border:1px solid rgba(16,185,129,0.2);">
        <div style="width:7px;height:7px;border-radius:50%;background:#10B981;
             box-shadow:0 0 8px #10B981;animation:pulse 1.6s infinite;"></div>
        LIVE SYSTEM
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr style="margin:0;border-color:rgba(255,255,255,0.06);">', unsafe_allow_html=True)

# ── Page Routing ──────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "Overview":
    from pages.overview import render
    render()
elif page == "AI Processor":
    from pages.ai_processor import render
    render()
elif page == "Resource Map":
    from pages.resource_map import render
    render()
elif page == "Analytics":
    from pages.analytics import render
    render()
elif page == "Settings":
    from pages.settings import render
    render()