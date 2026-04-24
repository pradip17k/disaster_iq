import streamlit as st
import folium
from streamlit_folium import st_folium
from core import (load_sheet_data, LOCATION_COORDS, RESOURCES,
                  allocate_resources, CATEGORY_EMOJIS, URGENCY_COLORS,
                  RESOURCE_EMOJIS, urgency_badge, status_badge)
import pandas as pd

INCIDENT_DEMO = [
    {"post": "Flooding in Whitefield near Main Road",  "category": "Flood",             "urgency": "High",   "location": "Whitefield",   "confidence": 94.2, "method": "AI"},
    {"post": "Fire in Koramangala 5th Block building", "category": "Fire",              "urgency": "High",   "location": "Koramangala",  "confidence": 91.8, "method": "AI"},
    {"post": "Heart attack near Indiranagar 100 ft Rd","category": "Medical Emergency", "urgency": "High",   "location": "Indiranagar",  "confidence": 96.5, "method": "AI"},
    {"post": "Transformer blast in HSR Layout",        "category": "Electricity Failure","urgency":"Medium",  "location": "HSR Layout",   "confidence": 88.1, "method": "AI"},
    {"post": "Missing elderly woman near Hebbal",      "category": "Missing Person",     "urgency": "Medium", "location": "Hebbal",       "confidence": 83.4, "method": "AI"},
    {"post": "Truck collision at Marathahalli bridge", "category": "Road Accident",      "urgency": "High",   "location": "Marathahalli", "confidence": 92.7, "method": "AI"},
    {"post": "Water level rising fast in BTM Layout",  "category": "Flood",             "urgency": "High",   "location": "BTM Layout",   "confidence": 90.3, "method": "AI"},
    {"post": "Person trapped under debris at Jayanagar","category":"Rescue Required",   "urgency": "Medium", "location": "Jayanagar",    "confidence": 87.6, "method": "AI"},
]

def render():
    st.markdown('<div style="padding:20px 24px 0;">', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:20px;">
      <h2 style="color:#F1F5F9;font-size:22px;font-weight:800;margin:0 0 4px;">🗺️ Resource &amp; Incident Map</h2>
      <p style="color:#64748B;font-size:13px;margin:0;">
        Real-time incident locations, emergency resource positions, and allocation status across Bengaluru.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filter controls ────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 4])
    with fc1:
        filter_urgency = st.selectbox("Urgency Filter", ["All","High","Medium","Low"], key="rm_urg")
    with fc2:
        filter_category = st.selectbox("Category Filter",
            ["All","Flood","Fire","Medical Emergency","Road Accident",
             "Rescue Required","Electricity Failure","Missing Person"], key="rm_cat")
    with fc3:
        map_style = st.selectbox("Map Style",
            ["Dark","Street","Satellite (approx)"], key="rm_style")
    with fc4:
        show_resources = st.checkbox("Show Resources", value=True, key="rm_res")

    tiles_map = {
        "Dark": "CartoDB dark_matter",
        "Street": "OpenStreetMap",
        "Satellite (approx)": "CartoDB positron"
    }
    tile = tiles_map.get(map_style, "CartoDB dark_matter")

    # ── Load / build incident data ─────────────────────────────────────────────
    df, err = load_sheet_data()
    if err or df.empty:
        inc_df = pd.DataFrame(INCIDENT_DEMO)
        st.info("📋 Showing demo incidents (Google Sheets unavailable).", icon="ℹ️")
    else:
        inc_df = df.copy()

    inc_df["lat"] = inc_df["location"].map(lambda x: LOCATION_COORDS.get(x,(None,None))[0])
    inc_df["lon"] = inc_df["location"].map(lambda x: LOCATION_COORDS.get(x,(None,None))[1])
    inc_df = inc_df.dropna(subset=["lat","lon"])

    # Apply filters
    if filter_urgency != "All":
        inc_df = inc_df[inc_df["urgency"] == filter_urgency]
    if filter_category != "All":
        inc_df = inc_df[inc_df["category"] == filter_category]

    # Allocate
    allocated, res_state = allocate_resources(inc_df.copy())

    # ── Map ────────────────────────────────────────────────────────────────────
    left_col, right_col = st.columns([7, 3], gap="medium")

    with left_col:
        m = folium.Map(location=[12.97, 77.59], zoom_start=11, tiles=tile)

        # Incident markers
        for _, row in inc_df.iterrows():
            urg   = row.get("urgency","Low")
            cat   = row.get("category","General")
            color = {"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(urg,"#3B82F6")
            radius = {"High":16,"Medium":11,"Low":7}.get(urg,9)
            emoji = CATEGORY_EMOJIS.get(cat,"📢")

            popup_html = f"""
            <div style="font-family:Inter,sans-serif;min-width:180px;">
              <div style="font-weight:700;font-size:14px;margin-bottom:6px;">{emoji} {cat}</div>
              <div style="font-size:12px;color:#64748B;">
                <b>Location:</b> {row.get('location','Unknown')}<br>
                <b>Urgency:</b> <span style="color:{color};font-weight:600;">{urg}</span><br>
                <b>Confidence:</b> {row.get('confidence',0):.1f}%<br>
                <b>Post:</b> {str(row.get('post',''))[:100]}…
              </div>
            </div>
            """
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius,
                color=color, fill=True, fill_color=color,
                fill_opacity=0.8, opacity=1.0,
                popup=folium.Popup(popup_html, max_width=240)
            ).add_to(m)

            if urg == "High":
                folium.Circle(
                    location=[row["lat"], row["lon"]], radius=700,
                    color=color, fill=True, fill_color=color,
                    fill_opacity=0.08, opacity=0.25
                ).add_to(m)

        # Resource markers
        if show_resources:
            res_icons = {
                "Ambulance":"🚑","Fire Truck":"🚒","Rescue Boat":"🚤",
                "Helicopter":"🚁","Medical Team":"🏥","Rescue Team":"⛑️"
            }
            for _, res in res_state.iterrows():
                s_color = {"Available":"#10B981","Deployed":"#F59E0B"}.get(res["status"],"#64748B")
                ri = res_icons.get(res["type"],"📍")
                popup_r = f"""
                <div style="font-family:Inter,sans-serif;">
                  <b>{res['type']}</b><br>
                  ID: {res['id']}<br>
                  Zone: {res['zone']}<br>
                  Status: <span style="color:{s_color};font-weight:700;">{res['status']}</span>
                </div>
                """
                folium.Marker(
                    location=[res["lat"], res["lon"]],
                    popup=folium.Popup(popup_r, max_width=180),
                    icon=folium.DivIcon(
                        html=f'<div style="font-size:20px;filter:drop-shadow(0 2px 6px rgba(0,0,0,.8));">'
                             f'{ri}</div>',
                        icon_size=(28,28), icon_anchor=(14,14)
                    )
                ).add_to(m)

        # Draw allocation lines (incident → resource)
        for _, row in allocated.iterrows():
            if row.get("resource_id","—") == "—":
                continue
            res_row = res_state[res_state["id"] == row["resource_id"]]
            if res_row.empty:
                continue
            rr = res_row.iloc[0]
            urg_color = {"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(row.get("urgency","Low"),"#64748B")
            folium.PolyLine(
                locations=[[row["lat"], row["lon"]], [rr["lat"], rr["lon"]]],
                color=urg_color, weight=2, opacity=0.5, dash_array="6"
            ).add_to(m)

        # Legend
        legend_html = """
        <div style="position:fixed;bottom:20px;right:12px;z-index:9999;
             background:rgba(13,21,37,0.92);border:1px solid rgba(255,255,255,0.12);
             border-radius:10px;padding:12px 16px;font-family:Inter,sans-serif;font-size:11px;color:#CBD5E1;">
          <div style="font-weight:700;margin-bottom:8px;color:#F1F5F9;">Legend</div>
          <div>🔴 High Risk Incident</div>
          <div>🟡 Medium Risk Incident</div>
          <div>🟢 Low Risk Incident</div>
          <div style="margin-top:6px;border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">
            <div>🚑 Ambulance</div>
            <div>🚒 Fire Truck</div>
            <div>⛵ Rescue Boat</div>
            <div>🚁 Helicopter</div>
            <div>🏥 Medical Team</div>
            <div>⛑️ Rescue Team</div>
          </div>
          <div style="margin-top:6px;border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;font-size:10px;color:#475569;">
            --- Allocation route
          </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        st_folium(m, use_container_width=True, height=520, returned_objects=[])

    # ── Right panel: incident list + resource status ────────────────────────────
    with right_col:
        # Summary stats
        high_c   = len(inc_df[inc_df["urgency"]=="High"])
        med_c    = len(inc_df[inc_df["urgency"]=="Medium"])
        avail_r  = len(res_state[res_state["status"]=="Available"])
        deploy_r = len(res_state[res_state["status"]=="Deployed"])

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">
          <div style="background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.25);
               border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#EF4444;">{high_c}</div>
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;">High Priority</div>
          </div>
          <div style="background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.25);
               border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#F59E0B;">{med_c}</div>
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;">Medium</div>
          </div>
          <div style="background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.25);
               border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#10B981;">{avail_r}</div>
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;">Available</div>
          </div>
          <div style="background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.25);
               border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:#F59E0B;">{deploy_r}</div>
            <div style="font-size:10px;color:#94A3B8;text-transform:uppercase;">Deployed</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:12px;font-weight:600;color:#94A3B8;margin-bottom:8px;">ACTIVE INCIDENTS</div>', unsafe_allow_html=True)

        for _, row in allocated.iterrows():
            urg   = row.get("urgency","Low")
            cat   = row.get("category","General")
            loc   = row.get("location","Unknown")
            res   = row.get("assigned_resource","Queued")
            eta   = row.get("eta_min","—")
            color = {"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(urg,"#64748B")
            emoji = CATEGORY_EMOJIS.get(cat,"📢")

            st.markdown(f"""
            <div style="background:#0D1525;border:1px solid {color}33;border-left:3px solid {color};
                 border-radius:8px;padding:10px 12px;margin-bottom:8px;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span style="font-size:14px;">{emoji}</span>
                <span style="font-size:12px;font-weight:600;color:#E2E8F0;">{cat}</span>
                <span style="margin-left:auto;font-size:10px;color:{color};font-weight:600;">{urg}</span>
              </div>
              <div style="font-size:11px;color:#64748B;">📍 {loc}</div>
              <div style="font-size:11px;color:#34D399;margin-top:3px;">→ {res} • ⏱ {eta} min</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)