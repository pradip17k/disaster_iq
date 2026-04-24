import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core import load_sheet_data, URGENCY_COLORS, CATEGORY_EMOJIS

DEMO_DATA = {
    "category": ["Flood","Fire","Medical Emergency","Road Accident","Rescue Required",
                  "Electricity Failure","Missing Person","Flood","Fire","Medical Emergency",
                  "Rescue Required","Flood","General","Medical Emergency","Road Accident"],
    "urgency":  ["High","High","High","High","Medium","Medium","Medium",
                  "High","High","Medium","High","Medium","Low","High","High"],
    "location": ["Whitefield","Koramangala","Indiranagar","Marathahalli","Jayanagar",
                  "HSR Layout","Hebbal","BTM Layout","Peenya","Malleshwaram",
                  "Yelahanka","KR Puram","Domlur","Rajajinagar","Bellandur"],
    "confidence": [94.2,91.8,96.5,92.7,87.6,88.1,83.4,90.3,85.0,93.1,
                   88.8,82.5,72.3,95.0,91.2],
}

DARK = "#080E1A"
PANEL = "#0D1525"
BORDER = "rgba(255,255,255,0.06)"
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
)


def _chart_panel(title, fig, height=320):
    st.markdown(f"""
    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
         padding:16px 18px 10px;margin-bottom:16px;">
      <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:12px;">{title}</div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def render():
    st.markdown('<div style="padding:20px 24px 0;">', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:20px;">
      <h2 style="color:#F1F5F9;font-size:22px;font-weight:800;margin:0 0 4px;">📊 Disaster Analytics</h2>
      <p style="color:#64748B;font-size:13px;margin:0;">
        Visual breakdown of incident categories, urgency levels, location hotspots, and resource efficiency.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    df, err = load_sheet_data()
    if err or df.empty:
        df = pd.DataFrame(DEMO_DATA)
        st.info("📋 Showing demo analytics data (Google Sheets unavailable).", icon="ℹ️")
    else:
        st.success(f"✅ Analysing {len(df)} live incidents from Google Sheets.", icon="✅")

    # ── KPI summary row ────────────────────────────────────────────────────────
    total  = len(df)
    high_n = len(df[df["urgency"] == "High"])   if "urgency"  in df.columns else 0
    cats   = df["category"].nunique()             if "category" in df.columns else 0
    locs   = df["location"].nunique()             if "location" in df.columns else 0
    avg_c  = round(df["confidence"].mean(), 1)   if "confidence" in df.columns else 0

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
      <div style="background:linear-gradient(135deg,#1d4ed8,#2563eb);border-radius:12px;padding:16px;">
        <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:.07em;">Total Incidents</div>
        <div style="font-size:28px;font-weight:800;color:#fff;">{total}</div>
      </div>
      <div style="background:linear-gradient(135deg,#b91c1c,#ef4444);border-radius:12px;padding:16px;">
        <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:.07em;">High Priority</div>
        <div style="font-size:28px;font-weight:800;color:#fff;">{high_n}</div>
      </div>
      <div style="background:linear-gradient(135deg,#065f46,#10b981);border-radius:12px;padding:16px;">
        <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:.07em;">Avg AI Confidence</div>
        <div style="font-size:28px;font-weight:800;color:#fff;">{avg_c}%</div>
      </div>
      <div style="background:linear-gradient(135deg,#5b21b6,#8b5cf6);border-radius:12px;padding:16px;">
        <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:.07em;">Unique Locations</div>
        <div style="font-size:28px;font-weight:800;color:#fff;">{locs}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Row 1: Category distribution + Urgency donut ──────────────────────────
    r1c1, r1c2 = st.columns([3, 2], gap="medium")

    with r1c1:
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        colors = ["#3B82F6","#EF4444","#10B981","#F59E0B","#8B5CF6","#EC4899","#14B8A6","#F97316"]
        fig_cat = px.bar(
            cat_counts, x="Count", y="Category", orientation="h",
            color="Category", color_discrete_sequence=colors,
            title=""
        )
        fig_cat.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=280)
        fig_cat.update_traces(marker_line_width=0)
        fig_cat.update_xaxes(gridcolor="rgba(255,255,255,0.04)")
        fig_cat.update_yaxes(gridcolor="rgba(0,0,0,0)")
        _chart_panel("📊 Incidents by Category", fig_cat, 280)

    with r1c2:
        urg_counts = df["urgency"].value_counts().reset_index()
        urg_counts.columns = ["Urgency", "Count"]
        urg_color_seq = [URGENCY_COLORS.get(u,"#64748B") for u in urg_counts["Urgency"]]
        fig_urg = go.Figure(go.Pie(
            labels=urg_counts["Urgency"], values=urg_counts["Count"],
            hole=0.6,
            marker=dict(colors=urg_color_seq, line=dict(color=DARK, width=3)),
            textfont=dict(color="#CBD5E1", size=12),
        ))
        fig_urg.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=True,
                              annotations=[dict(text=f"<b>{total}</b><br>Total",
                                               x=0.5, y=0.5, showarrow=False,
                                               font=dict(size=14, color="#F1F5F9"))])
        _chart_panel("🚨 Urgency Breakdown", fig_urg, 280)

    # ── Row 2: Location hotspot bar + Confidence distribution ─────────────────
    r2c1, r2c2 = st.columns([3, 2], gap="medium")

    with r2c1:
        if "location" in df.columns:
            loc_counts = df["location"].value_counts().head(10).reset_index()
            loc_counts.columns = ["Location", "Incidents"]
            fig_loc = px.bar(
                loc_counts, x="Location", y="Incidents",
                color="Incidents", color_continuous_scale=["#1d4ed8","#EF4444"],
            )
            fig_loc.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=280,
                                  coloraxis_showscale=False)
            fig_loc.update_traces(marker_line_width=0)
            fig_loc.update_xaxes(gridcolor="rgba(255,255,255,0.04)", tickangle=-30)
            fig_loc.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
            _chart_panel("📍 Top Incident Hotspots", fig_loc, 280)

    with r2c2:
        if "confidence" in df.columns:
            fig_hist = px.histogram(
                df, x="confidence", nbins=10,
                color_discrete_sequence=["#3B82F6"],
            )
            fig_hist.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=280)
            fig_hist.update_traces(marker_line_width=0)
            fig_hist.update_xaxes(gridcolor="rgba(255,255,255,0.04)", title="Confidence %")
            fig_hist.update_yaxes(gridcolor="rgba(255,255,255,0.04)", title="Count")
            _chart_panel("🎯 AI Confidence Distribution", fig_hist, 280)

    # ── Row 3: Urgency × Category heatmap ────────────────────────────────────
    if "category" in df.columns and "urgency" in df.columns:
        pivot = pd.crosstab(df["category"], df["urgency"]).fillna(0)
        fig_heat = px.imshow(
            pivot, color_continuous_scale=["#0D1525","#1d4ed8","#EF4444"],
            text_auto=True, aspect="auto"
        )
        fig_heat.update_layout(**PLOTLY_LAYOUT, height=300,
                               coloraxis_showscale=False,
                               xaxis_title="Urgency", yaxis_title="Category")
        fig_heat.update_traces(textfont=dict(color="#F1F5F9", size=13))
        _chart_panel("🔥 Urgency × Category Heatmap", fig_heat, 300)

    # ── High Priority Table ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:12px;
         padding:16px 18px;margin-bottom:16px;">
      <div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:12px;">🔥 High Priority Incidents</div>
    """, unsafe_allow_html=True)

    high_df = df[df["urgency"] == "High"].copy() if "urgency" in df.columns else df.copy()
    if not high_df.empty:
        display_cols = [c for c in ["post","category","location","urgency","confidence"] if c in high_df.columns]
        st.dataframe(
            high_df[display_cols].head(10),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No high priority incidents found.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)