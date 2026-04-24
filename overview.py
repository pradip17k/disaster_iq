import streamlit as st
import pandas as pd
import random
import folium
from streamlit_folium import st_folium
from core import load_sheet_data, LOCATION_COORDS, RESOURCES, CATEGORY_EMOJIS, URGENCY_COLORS

# ── Simulated SNS feed data ───────────────────────────────────────────────────
SNS_FEEDS = [
    {"platform": "twitter",  "color": "#1DA1F2", "emoji": "🐦",
     "user": "@ravi_kumar94",   "time": "2m ago",   "urgency": "High",
     "location": "Whitefield",
     "text": "🚨 URGENT — Massive flooding on Whitefield Main Rd! Cars submerged, people stranded on rooftops. Need immediate rescue boats!"},
    {"platform": "facebook",  "color": "#1877F2", "emoji": "📘",
     "user": "Priya Sharma",    "time": "5m ago",   "urgency": "High",
     "location": "Koramangala",
     "text": "Fire broke out in Koramangala 5th Block. Smoke visible from 3 buildings. Residents evacuating. Fire brigade not yet arrived."},
    {"platform": "reddit",    "color": "#FF4500", "emoji": "🔶",
     "user": "u/bengaluru_help", "time": "8m ago",  "urgency": "Medium",
     "location": "Indiranagar",
     "text": "r/bengaluru — Power outage across Indiranagar since 2 hours. Transformers damaged near 100 Feet Road junction."},
    {"platform": "instagram", "color": "#E1306C", "emoji": "📸",
     "user": "@help_hsr",       "time": "11m ago",  "urgency": "High",
     "location": "HSR Layout",
     "text": "Elderly man collapsed near HSR Sector 2. He needs ambulance ASAP. We are waiting at BDA complex gate."},
    {"platform": "twitter",   "color": "#1DA1F2", "emoji": "🐦",
     "user": "@flood_watch_blr", "time": "14m ago", "urgency": "Medium",
     "location": "Marathahalli",
     "text": "Outer Ring Road near Marathahalli completely waterlogged. Traffic at standstill. Avoid ORR if possible. 🌊"},
    {"platform": "facebook",  "color": "#1877F2", "emoji": "📘",
     "user": "Rescue Volunteers BLR", "time": "18m ago", "urgency": "Low",
     "location": "Hebbal",
     "text": "Missing person alert: 70-year-old woman with memory issues last seen near Hebbal flyover around 9 AM. Please share."},
]

CITY_STATS = [
    ("Whitefield", "+35.4%"), ("Koramangala", "+2.5%"), ("Indiranagar", "+8.8%"),
    ("HSR Layout",  "+4.6%"), ("Marathahalli", "+1.4%"), ("Hebbal",       "+0.7%"),
]

def _urgency_badge(u):
    cls = {"High":"badge-high","Medium":"badge-medium","Low":"badge-low"}.get(u,"badge-info")
    return f'<span class="badge {cls}">{u}</span>'

def _platform_icon(p):
    return {"twitter":"🐦","facebook":"📘","reddit":"🔶","instagram":"📸"}.get(p,"💬")

def render():
    # ── KPI Cards ─────────────────────────────────────────────────────────────
    df, err = load_sheet_data()

    # Compute stats (use real data if available, else demo)
    if err or df.empty:
        total   = 339259
        active  = 204521
        closed  = 98432
        need    = 31847
        saved   = 128904
        deaths  = 7543
        high_pct = 60
        df_demo  = True
    else:
        total   = len(df)
        active  = len(df[df.get("status","") == "Active"]) if "status" in df.columns else int(total * 0.60)
        closed  = int(total * 0.29)
        need    = int(total * 0.09)
        saved   = int(total * 0.38)
        deaths  = int(total * 0.02)
        high_pct = int(len(df[df.get("urgency","") == "High"]) / max(total,1) * 100) if "urgency" in df.columns else 35
        df_demo  = False

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card kpi-blue">
        <div class="kpi-label">Total Cases</div>
        <div class="kpi-value">{total:,}</div>
        <div class="kpi-delta">↑ 11% this week</div>
        <div class="kpi-icon">📋</div>
      </div>
      <div class="kpi-card kpi-red">
        <div class="kpi-label">Active 60%</div>
        <div class="kpi-value">{active:,}</div>
        <div class="kpi-delta">↑ 8% since yesterday</div>
        <div class="kpi-icon">🔴</div>
      </div>
      <div class="kpi-card kpi-green">
        <div class="kpi-label">Closed 29%</div>
        <div class="kpi-value">{closed:,}</div>
        <div class="kpi-delta">↑ 4% resolved today</div>
        <div class="kpi-icon">✅</div>
      </div>
      <div class="kpi-card kpi-orange">
        <div class="kpi-label">Need Help 9%</div>
        <div class="kpi-value">{need:,}</div>
        <div class="kpi-delta">↓ 2% from peak</div>
        <div class="kpi-icon">🆘</div>
      </div>
      <div class="kpi-card kpi-purple">
        <div class="kpi-label">Saved 38%</div>
        <div class="kpi-value">{saved:,}</div>
        <div class="kpi-delta">↑ 6% today</div>
        <div class="kpi-icon">🛡️</div>
      </div>
      <div class="kpi-card kpi-dark">
        <div class="kpi-label">Deaths 2%+</div>
        <div class="kpi-value">{deaths:,}</div>
        <div class="kpi-delta">Confirmed fatalities</div>
        <div class="kpi-icon">☠️</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Middle Row: SNS Feed + Mini Incident Map ───────────────────────────────
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)
    col_feed, col_map = st.columns([4, 6], gap="medium")

    with col_feed:
        st.markdown("""
        <div class="panel">
          <div class="panel-header">
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="width:9px;height:9px;border-radius:50%;background:#EF4444;
                   box-shadow:0 0 8px #EF4444;animation:pulse 1.6s infinite;"></div>
              SNS FEED
            </div>
            <div style="display:flex;gap:8px;font-size:18px;">🔄 🔗</div>
          </div>
          <div class="panel-body" style="max-height:340px;overflow-y:auto;padding-top:6px;">
        """, unsafe_allow_html=True)

        for feed in SNS_FEEDS:
            badge = _urgency_badge(feed["urgency"])
            plat_icon = _platform_icon(feed["platform"])
            st.markdown(f"""
            <div class="feed-item">
              <div class="feed-icon" style="background:{feed['color']}22;color:{feed['color']};">{plat_icon}</div>
              <div style="flex:1;min-width:0;">
                <div style="font-size:11px;font-weight:600;color:#93C5FD;margin-bottom:3px;">
                  {feed['user']}
                </div>
                <div class="feed-text">{feed['text']}</div>
                <div class="feed-meta">
                  <span class="feed-location">📍 {feed['location']}</span>
                  {badge}
                  <span>{feed['time']}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
          </div>
          <div style="padding:10px 18px;border-top:1px solid rgba(255,255,255,0.06);">
            <div style="font-size:11px;color:#334155;">🔍 Search for topics, hashtags, keywords…</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_map:
        st.markdown("""
        <div class="panel">
          <div class="panel-header">
            Incident Hotspot Map
            <span style="font-size:11px;color:#475569;">Real-time • Bengaluru</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Build mini incident map
        mini_map = folium.Map(
            location=[12.97, 77.59], zoom_start=11,
            tiles="CartoDB dark_matter"
        )

        incident_locations = [
            ("Whitefield",    "Flood",             "High",   12.9698, 77.7500),
            ("Koramangala",   "Fire",               "High",   12.9352, 77.6245),
            ("Indiranagar",   "Electricity Failure","Medium", 12.9784, 77.6408),
            ("HSR Layout",    "Medical Emergency",  "High",   12.9116, 77.6474),
            ("Marathahalli",  "Flood",              "Medium", 12.9591, 77.6974),
            ("Hebbal",        "Missing Person",     "Low",    13.0358, 77.5970),
            ("BTM Layout",    "Road Accident",      "High",   12.9166, 77.6101),
            ("Jayanagar",     "Rescue Required",    "Medium", 12.9250, 77.5938),
        ]

        for loc, cat, urg, lat, lon in incident_locations:
            color = {"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(urg,"#3B82F6")
            radius = {"High":18,"Medium":12,"Low":8}.get(urg,10)
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                color=color, fill=True, fill_color=color,
                fill_opacity=0.7, opacity=0.9,
                popup=folium.Popup(
                    f"<b>{loc}</b><br>{cat}<br>Urgency: {urg}",
                    max_width=180
                )
            ).add_to(mini_map)

            if urg == "High":
                folium.Circle(
                    location=[lat, lon], radius=900,
                    color=color, fill=True, fill_color=color, fill_opacity=0.08,
                    opacity=0.3
                ).add_to(mini_map)

        # Resource markers
        res_icons = {"Ambulance":"🚑","Fire Truck":"🚒","Rescue Boat":"🚤",
                     "Helicopter":"🚁","Medical Team":"🏥","Rescue Team":"⛑️"}
        for _, res in RESOURCES.iterrows():
            if res["status"] == "Available":
                folium.Marker(
                    location=[res["lat"], res["lon"]],
                    popup=f"{res['type']} — {res['id']}",
                    icon=folium.DivIcon(
                        html=f'<div style="font-size:16px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.6));">'
                             f'{res_icons.get(res["type"],"📍")}</div>',
                        icon_size=(24, 24), icon_anchor=(12, 12)
                    )
                ).add_to(mini_map)

        st_folium(mini_map, use_container_width=True, height=340, returned_objects=[])

        # Legend
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:10px;padding:8px 4px;font-size:11px;color:#94A3B8;">
          <span>🔵 Your Place</span>
          <span style="color:#3B82F6;">🔒 Lock Down</span>
          <span style="color:#F59E0B;">🟡 Alert</span>
          <span style="color:#EF4444;">🔴 High Risk</span>
          <span>📍 Available Units</span>
          <span>🏥 Hospital</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── City Emergency Level Map ───────────────────────────────────────────────
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel">
      <div class="panel-header">
        CITY EMERGENCY LEVEL MAP
        <span style="font-size:11px;color:#475569;">3 hours ago</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    city_map = folium.Map(
        location=[12.97, 77.59], zoom_start=10,
        tiles="OpenStreetMap"
    )

    # Heatmap-style circles for zones
    zones = [
        (12.97, 77.59, "Central",    "#EF4444", 0.35, 2500),
        (12.93, 77.62, "South",      "#F59E0B", 0.25, 1800),
        (13.03, 77.60, "North",      "#10B981", 0.20, 1400),
        (12.96, 77.75, "East",       "#EF4444", 0.30, 2000),
        (12.97, 77.52, "West",       "#F59E0B", 0.22, 1600),
        (12.89, 77.64, "South-East", "#10B981", 0.18, 1200),
    ]
    for lat, lon, name, color, opacity, radius in zones:
        folium.Circle(
            location=[lat, lon], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=opacity,
            popup=f"{name} Zone", opacity=0.4
        ).add_to(city_map)

    # All incident markers on city map
    for loc, cat, urg, lat, lon in incident_locations:
        folium.CircleMarker(
            location=[lat, lon], radius=7,
            color={"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(urg,"#3B82F6"),
            fill=True,
            fill_color={"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(urg,"#3B82F6"),
            fill_opacity=0.9,
            popup=f"{loc} — {cat}"
        ).add_to(city_map)

    st_folium(city_map, use_container_width=True, height=340, returned_objects=[])

    # City stats footer — built as one HTML block to avoid Streamlit leaking raw tags
    stats_html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:8px 0 4px;">'
    for i, (name, pct) in enumerate(CITY_STATS):
        color = "#EF4444" if float(pct.replace("+","").replace("%","")) > 5 else "#10B981"
        stats_html += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
             padding:8px 12px;background:rgba(255,255,255,0.04);border-radius:8px;
             border:1px solid rgba(255,255,255,0.05);font-size:12px;">
          <span style="color:#94A3B8;">🔵 {name}</span>
          <span style="color:{color};font-weight:700;">{pct}</span>
        </div>"""
    stats_html += "</div>"
    st.markdown(stats_html, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:10px 0 4px;">
      <button style="width:100%;padding:10px;background:linear-gradient(135deg,#1d4ed8,#2563eb);
              color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;">
        📊 View Full Analytics
      </button>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)