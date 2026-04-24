import streamlit as st
import pandas as pd
import time
from core import (classify_text, extract_location_ner, allocate_resources,
                  load_sheet_data, update_sheet, CATEGORY_EMOJIS, URGENCY_COLORS,
                  urgency_badge, RESOURCE_EMOJIS)

# ── Sample disaster tweets ────────────────────────────────────────────────────
SAMPLE_POSTS = [
    "🚨 Heavy flooding in Whitefield! Roads submerged, cars stuck. Rescue boats needed immediately near Whitefield Main Road junction. People stranded on rooftops!",
    "Fire broke out in Koramangala 5th Block building! Smoke coming from top floors. Fire brigade not here yet. Someone call 101! People trapped inside!",
    "My father had a heart attack near Indiranagar 100 Feet Road. We need an ambulance RIGHT NOW. He is unconscious and not breathing properly!",
    "Transformer blast in HSR Layout Sector 2 — entire sector without power. Sparks flying, very dangerous. Keep children away from Sector 2 junction!",
    "Elderly woman named Kamala (70 yrs) missing since morning from Hebbal flyover area. She has memory issues. Please call 9845XXXXXX if seen.",
    "Major accident at Marathahalli bridge — two trucks collided, one vehicle overturned. Multiple injured. Traffic completely blocked. Need ambulance and police.",
    "Water level rising fast in BTM Layout 2nd Stage! Ground floor houses flooded. Families with kids stuck. No one is responding to calls for help!"
]

def _result_card(result, idx):
    urg   = result.get("urgency", "Low")
    cat   = result.get("category", "General")
    conf  = result.get("confidence", 0)
    loc   = result.get("location", "Unknown")
    meth  = result.get("method", "—")
    res   = result.get("assigned_resource", "—")
    rid   = result.get("resource_id", "—")
    eta   = result.get("eta_min", "—")
    dist  = result.get("distance_km", "—")
    emoji = CATEGORY_EMOJIS.get(cat, "📢")
    color = URGENCY_COLORS.get(urg, "#64748B")
    res_e = RESOURCE_EMOJIS.get(res, "🆘")

    return f"""
    <div style="background:#0D1525;border:1px solid {color}33;border-left:4px solid {color};
         border-radius:12px;padding:16px 18px;margin-bottom:12px;transition:all .2s;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        <span style="font-size:24px;">{emoji}</span>
        <div style="flex:1;">
          <div style="font-size:14px;font-weight:700;color:#F1F5F9;">{cat}</div>
          <div style="font-size:11px;color:#64748B;">Post #{idx+1} • via {meth}</div>
        </div>
        <span style="background:{color}22;color:{color};padding:4px 12px;
              border-radius:20px;font-size:11px;font-weight:700;">{urg}</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:8px;">
        <div style="background:rgba(255,255,255,0.04);padding:8px 10px;border-radius:8px;">
          <div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;">Location</div>
          <div style="font-size:12px;color:#38BDF8;font-weight:600;">📍 {loc}</div>
        </div>
        <div style="background:rgba(255,255,255,0.04);padding:8px 10px;border-radius:8px;">
          <div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;">Confidence</div>
          <div style="font-size:12px;color:#A78BFA;font-weight:600;">🎯 {conf}%</div>
        </div>
        <div style="background:rgba(255,255,255,0.04);padding:8px 10px;border-radius:8px;">
          <div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;">Resource</div>
          <div style="font-size:12px;color:#34D399;font-weight:600;">{res_e} {res} ({rid})</div>
        </div>
        <div style="background:rgba(255,255,255,0.04);padding:8px 10px;border-radius:8px;">
          <div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;">ETA</div>
          <div style="font-size:12px;color:#FBBF24;font-weight:600;">⏱ {eta} min • {dist} km</div>
        </div>
      </div>
    </div>
    """

def render():
    st.markdown('<div style="padding:20px 24px 0;">', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:20px;">
      <h2 style="color:#F1F5F9;font-size:22px;font-weight:800;margin:0 0 4px;">
        🤖 AI Incident Processor
      </h2>
      <p style="color:#64748B;font-size:13px;margin:0;">
        Paste social media posts below. The AI will classify the emergency, extract location via NER,
        and auto-allocate the nearest available resource.
      </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Manual Input", "📊 Batch Process (Google Sheets)", "🔬 Model Info"])

    # ── TAB 1: Manual Input ────────────────────────────────────────────────────
    with tab1:
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown('<p style="font-size:12px;color:#64748B;margin-bottom:6px;">Paste disaster-related social media text:</p>', unsafe_allow_html=True)
            # Apply loaded sample if pending (must set widget key before render)
            if "loaded_post" in st.session_state:
                st.session_state["manual_post"] = st.session_state.pop("loaded_post")
            user_text = st.text_area(
                "Post", height=120, label_visibility="collapsed",
                placeholder="e.g. Heavy flooding in Whitefield! Rescue boats needed urgently. People stuck on rooftops near Main Road junction...",
                key="manual_post"
            )

        with c2:
            st.markdown('<p style="font-size:12px;color:#64748B;margin-bottom:6px;">Or pick a sample post:</p>', unsafe_allow_html=True)
            sample_idx = st.selectbox(
                "Sample", options=range(len(SAMPLE_POSTS)),
                format_func=lambda i: f"Sample {i+1}: {SAMPLE_POSTS[i][:50]}…",
                label_visibility="collapsed"
            )
            if st.button("📋 Load Sample", use_container_width=True):
                st.session_state["loaded_post"] = SAMPLE_POSTS[sample_idx]
                st.rerun()

        use_ai = st.toggle("⚡ Use HuggingFace AI (Zero-Shot + NER)", value=True)

        if st.button("🚀 Analyse & Allocate Resource", use_container_width=False):
            text = user_text
            if not text.strip():
                st.warning("Please enter a post or load a sample.")
            else:
                with st.spinner("Running AI pipeline…"):
                    cls = classify_text(text, use_ai=use_ai)
                    loc = extract_location_ner(text)
                    cls["location"] = loc

                    inc_df = pd.DataFrame([{
                        "post": text,
                        "category": cls["category"],
                        "urgency":  cls["urgency"],
                        "location": loc,
                        "confidence": cls["confidence"],
                        "method": cls["method"]
                    }])

                    allocated, _ = allocate_resources(inc_df)
                    row = allocated.iloc[0].to_dict()

                st.markdown("### ✅ Analysis Result", unsafe_allow_html=False)
                st.markdown(_result_card(row, 0), unsafe_allow_html=True)

                with st.expander("📄 Raw Post Text"):
                    st.code(text, language=None)

    # ── TAB 2: Batch Process ───────────────────────────────────────────────────
    with tab2:
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        df, err = load_sheet_data()

        if err:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
                 border-radius:10px;padding:16px;margin-bottom:16px;">
              <div style="color:#EF4444;font-weight:600;margin-bottom:4px;">⚠️ Google Sheets Error</div>
              <div style="color:#94A3B8;font-size:12px;">{err}</div>
              <div style="color:#64748B;font-size:11px;margin-top:6px;">
                Running in demo mode — sample incidents will be generated.
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Demo data
            df = pd.DataFrame({
                "post": SAMPLE_POSTS,
                "category": ["Flood","Fire","Medical Emergency","Electricity Failure","Missing Person","Road Accident","Flood"],
                "urgency":  ["High","High","High","Medium","Medium","High","High"],
                "location": ["Whitefield","Koramangala","Indiranagar","HSR Layout","Hebbal","Marathahalli","BTM Layout"],
            })
            st.info(f"📋 Loaded {len(df)} demo incidents for demonstration.", icon="ℹ️")
        else:
            st.success(f"✅ Loaded {len(df)} rows from Google Sheets.", icon="✅")

        use_ai_batch = st.toggle("⚡ AI Processing", value=False, key="batch_ai",
                                 help="Disable for faster demo (uses keyword matching)")

        if st.button("🚀 Run Batch AI + Allocate All Resources", use_container_width=False, key="batch_run"):
            progress_bar = st.progress(0, text="Starting AI pipeline…")
            results = []
            total = len(df)

            post_col = next((c for c in df.columns if "post" in c.lower()), df.columns[0])

            for i, row in df.iterrows():
                text = str(row.get(post_col, ""))
                cls  = classify_text(text, use_ai=use_ai_batch)
                loc  = extract_location_ner(text)
                results.append({
                    "post": text[:80] + "…" if len(text) > 80 else text,
                    "category": cls["category"],
                    "urgency":  cls["urgency"],
                    "location": loc,
                    "confidence": cls["confidence"],
                    "method": cls["method"],
                })
                progress_bar.progress(min((i+1)/total, 1.0), text=f"Processing {i+1}/{total}…")
                time.sleep(0.05)

            progress_bar.empty()
            result_df = pd.DataFrame(results)
            allocated, resource_state = allocate_resources(result_df)
            st.session_state["batch_results"] = allocated
            st.session_state["resource_state"] = resource_state
            st.success(f"✅ Processed {len(allocated)} incidents!")

        if "batch_results" in st.session_state:
            allocated = st.session_state["batch_results"]
            resource_state = st.session_state.get("resource_state")

            st.markdown("### 📋 Allocation Results")
            for i, (_, row) in enumerate(allocated.iterrows()):
                st.markdown(_result_card(row.to_dict(), i), unsafe_allow_html=True)

            if resource_state is not None:
                st.markdown("### 🚑 Resource Status After Allocation")
                deployed   = resource_state[resource_state["status"] == "Deployed"]
                available  = resource_state[resource_state["status"] == "Available"]
                dc, ac = st.columns(2)
                with dc:
                    st.markdown(f'<div style="font-size:12px;color:#F59E0B;font-weight:600;margin-bottom:8px;">🔶 Deployed ({len(deployed)})</div>', unsafe_allow_html=True)
                    for _, r in deployed.iterrows():
                        e = RESOURCE_EMOJIS.get(r["type"],"📍")
                        st.markdown(f'<div class="resource-row"><span class="res-icon">{e}</span> <b>{r["id"]}</b> — {r["type"]} <span style="margin-left:auto;color:#F59E0B;">Deployed</span></div>', unsafe_allow_html=True)
                with ac:
                    st.markdown(f'<div style="font-size:12px;color:#10B981;font-weight:600;margin-bottom:8px;">✅ Available ({len(available)})</div>', unsafe_allow_html=True)
                    for _, r in available.iterrows():
                        e = RESOURCE_EMOJIS.get(r["type"],"📍")
                        st.markdown(f'<div class="resource-row"><span class="res-icon">{e}</span> <b>{r["id"]}</b> — {r["type"]} <span style="margin-left:auto;color:#10B981;">Available</span></div>', unsafe_allow_html=True)

    # ── TAB 3: Model Info ──────────────────────────────────────────────────────
    with tab3:
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div style="background:#0D1525;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;">
            <div style="font-size:16px;margin-bottom:12px;">🧠 Zero-Shot Classifier</div>
            <div style="font-size:12px;color:#94A3B8;line-height:1.7;">
              <b style="color:#93C5FD;">Model:</b> valhalla/distilbart-mnli-12-3<br>
              <b style="color:#93C5FD;">Source:</b> Hugging Face (BART-large-MNLI variant)<br>
              <b style="color:#93C5FD;">Task:</b> Zero-shot text classification<br>
              <b style="color:#93C5FD;">Labels:</b> Flood, Fire, Medical Emergency, Road Accident,
              Electricity Failure, Missing Person, Rescue Required, General<br>
              <b style="color:#93C5FD;">Fallback:</b> Keyword-based rule engine (instant, offline)
            </div>
          </div>
          <div style="background:#0D1525;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;">
            <div style="font-size:16px;margin-bottom:12px;">📍 Named Entity Recognition</div>
            <div style="font-size:12px;color:#94A3B8;line-height:1.7;">
              <b style="color:#93C5FD;">Model:</b> dslim/bert-base-NER (default HF pipeline)<br>
              <b style="color:#93C5FD;">Source:</b> Hugging Face (RoBERTa-based NER)<br>
              <b style="color:#93C5FD;">Task:</b> Location extraction (LOC, GPE entities)<br>
              <b style="color:#93C5FD;">Coverage:</b> 24+ Bengaluru localities in fallback DB<br>
              <b style="color:#93C5FD;">Fallback:</b> Keyword matching against known area names
            </div>
          </div>
          <div style="background:#0D1525;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;grid-column:span 2;">
            <div style="font-size:16px;margin-bottom:12px;">⚙️ Allocation Algorithm</div>
            <div style="font-size:12px;color:#94A3B8;line-height:1.7;">
              <b style="color:#93C5FD;">Priority:</b> High → Medium → Low (urgency-ranked queue)<br>
              <b style="color:#93C5FD;">Matching:</b> Category → preferred resource type mapping<br>
              <b style="color:#93C5FD;">Distance:</b> Haversine formula (great-circle distance)<br>
              <b style="color:#93C5FD;">Speed:</b> ~30 km/h urban ETA estimate<br>
              <b style="color:#93C5FD;">Conflict:</b> Once deployed, resource marked unavailable for next incident
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
