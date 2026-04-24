import streamlit as st
from core import load_classifier, load_ner, RESOURCES

PANEL = "#0D1525"
BORDER = "rgba(255,255,255,0.06)"

def _status_row(label, ok, detail=""):
    dot_color = "#10B981" if ok else "#EF4444"
    dot_label = "Operational" if ok else "Offline"
    return f"""
    <div style="display:flex;align-items:center;gap:12px;padding:10px 0;
         border-bottom:1px solid {BORDER};">
      <div style="width:8px;height:8px;border-radius:50%;background:{dot_color};
           box-shadow:0 0 6px {dot_color};flex-shrink:0;"></div>
      <div style="flex:1;font-size:13px;color:#CBD5E1;">{label}</div>
      <div style="font-size:11px;color:{dot_color};font-weight:600;">{dot_label}</div>
      {"<div style='font-size:10px;color:#475569;margin-left:8px;'>"+detail+"</div>" if detail else ""}
    </div>
    """

def render():
    st.markdown('<div style="padding:20px 24px 0;">', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:20px;">
      <h2 style="color:#F1F5F9;font-size:22px;font-weight:800;margin:0 0 4px;">⚙️ System Settings</h2>
      <p style="color:#64748B;font-size:13px;margin:0;">
        Configure AI models, data refresh, and monitor live system health.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="medium")

    # ── Left: Config ──────────────────────────────────────────────────────────
    with col1:

        # AI Config panel
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
             padding:18px 20px;margin-bottom:16px;">
          <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:14px;">
            🤖 AI Model Configuration
          </div>
        """, unsafe_allow_html=True)

        use_ai = st.toggle("Enable HuggingFace AI (Zero-Shot + NER)", value=True, key="cfg_ai")
        if use_ai:
            st.markdown('<div style="color:#10B981;font-size:12px;margin-top:6px;">✅ AI pipeline active — using valhalla/distilbart-mnli-12-3 + NER</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#F59E0B;font-size:12px;margin-top:6px;">⚠️ AI disabled — keyword fallback mode active</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        model_name = st.selectbox(
            "Zero-Shot Model",
            ["valhalla/distilbart-mnli-12-3 (fast)", "facebook/bart-large-mnli (accurate)"],
            key="cfg_model"
        )
        ner_name = st.selectbox(
            "NER Model",
            ["dslim/bert-base-NER (default)", "Jean-Baptiste/roberta-large-ner-english (accurate)"],
            key="cfg_ner"
        )
        refresh_ttl = st.slider("Sheet Cache TTL (seconds)", 10, 300, 30, step=10, key="cfg_ttl")
        st.markdown("</div>", unsafe_allow_html=True)

        # Data Control panel
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
             padding:18px 20px;margin-bottom:16px;">
          <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:14px;">
            🔄 Data Control
          </div>
        """, unsafe_allow_html=True)

        dc1, dc2 = st.columns(2)
        with dc1:
            if st.button("🗑️ Clear Data Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("Data cache cleared!")
        with dc2:
            if st.button("🔄 Reload Models", use_container_width=True):
                st.cache_resource.clear()
                st.success("Model cache cleared! Models will reload on next use.")

        st.markdown(f"""
        <div style="font-size:11px;color:#475569;margin-top:10px;">
          Current cache TTL: <b style="color:#94A3B8;">{refresh_ttl}s</b> •
          Sheet: <b style="color:#94A3B8;">data</b> (sheet1)
        </div>
        </div>
        """, unsafe_allow_html=True)

        # Resource management
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
             padding:18px 20px;">
          <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:14px;">
            🚑 Simulated Resource Fleet
          </div>
        """, unsafe_allow_html=True)

        res_icons = {"Ambulance":"🚑","Fire Truck":"🚒","Rescue Boat":"⛵",
                     "Helicopter":"🚁","Medical Team":"🏥","Rescue Team":"⛑️"}

        for _, r in RESOURCES.iterrows():
            sc = {"Available":"#10B981","Deployed":"#F59E0B"}.get(r["status"],"#64748B")
            ei = res_icons.get(r["type"],"📍")
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                 border-bottom:1px solid {BORDER};font-size:12px;color:#CBD5E1;">
              <span style="font-size:18px;width:24px;text-align:center;">{ei}</span>
              <span style="flex:1;"><b>{r['id']}</b> — {r['type']}</span>
              <span style="color:#64748B;">{r['zone']}</span>
              <span style="color:{sc};font-weight:600;">{r['status']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Right: System Status ───────────────────────────────────────────────────
    with col2:

        # Check model status
        clf, clf_err = load_classifier()
        ner, ner_err = load_ner()

        try:
            import gspread
            gs_ok = True
        except ImportError:
            gs_ok = False

        try:
            import folium
            folium_ok = True
        except ImportError:
            folium_ok = False

        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
             padding:18px 20px;margin-bottom:16px;">
          <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:4px;">
            📡 System Health
          </div>
          {_status_row("Google Sheets API", gs_ok, "gspread + oauth2client")}
          {_status_row("Zero-Shot Classifier", clf is not None, model_name.split()[0])}
          {_status_row("NER Pipeline", ner is not None, ner_name.split()[0])}
          {_status_row("Folium Map Engine", folium_ok, "folium + streamlit-folium")}
          {_status_row("Streamlit Runtime", True, f"v{st.__version__}")}
          {_status_row("Resource Allocator", True, f"{len(RESOURCES)} units loaded")}
        </div>
        """, unsafe_allow_html=True)

        # About
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
             padding:18px 20px;margin-bottom:16px;">
          <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:12px;">ℹ️ About DisasterIQ</div>
          <div style="font-size:12px;color:#94A3B8;line-height:1.8;">
            <b style="color:#93C5FD;">Problem:</b> Disaster Response Resource Allocator<br>
            <b style="color:#93C5FD;">Domain:</b> AI &amp; Machine Learning<br>
            <b style="color:#93C5FD;">Models:</b> HuggingFace Zero-Shot + NER<br>
            <b style="color:#93C5FD;">Data:</b> Google Sheets (live social feed)<br>
            <b style="color:#93C5FD;">Stack:</b> Streamlit · Folium · Plotly · Transformers<br>
            <b style="color:#93C5FD;">Version:</b> 2.0 — Hackathon Edition
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Emergency contacts
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
             padding:18px 20px;">
          <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:12px;">📞 Emergency Contacts</div>
          <div style="font-size:12px;color:#94A3B8;line-height:2;">
            🚒 Fire: <b style="color:#F1F5F9;">101</b><br>
            🚑 Ambulance: <b style="color:#F1F5F9;">108</b><br>
            🚓 Police: <b style="color:#F1F5F9;">100</b><br>
            🆘 Disaster Mgmt: <b style="color:#F1F5F9;">1077</b><br>
            📞 National Emergency: <b style="color:#F1F5F9;">112</b>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)