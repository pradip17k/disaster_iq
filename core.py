"""
utils/core.py — Shared utilities for DisasterIQ
Handles: GSheets auth, AI classification, NER, resource allocation
"""

import os
import json
import time
import math
import random
import streamlit as st
import pandas as pd

# ── Google Sheets ────────────────────────────────────────────────────────────

def get_gsheet_client():
    """Authenticate with Google Sheets using credentials.json or Streamlit secrets."""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        # Try Streamlit secrets first (for deployment), then local file
        cred_file = None
        try:
            if "gcp_service_account" in st.secrets:
                import tempfile
                cred_dict = dict(st.secrets["gcp_service_account"])
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(cred_dict, f)
                    cred_file = f.name
        except Exception:
            pass  # No secrets.toml — fall through to credentials.json

        if cred_file is None:
            cred_file = os.path.join(os.getcwd(), "credentials.json")

        creds = ServiceAccountCredentials.from_json_keyfile_name(cred_file, scope)
        client = gspread.authorize(creds)
        return client, None

    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=30, show_spinner=False)
def load_sheet_data(sheet_name="data"):
    """Load all records from Google Sheet with 30s cache."""
    client, err = get_gsheet_client()
    if err:
        return pd.DataFrame(), err

    try:
        sheet = client.open(sheet_name).sheet1
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame(), "Sheet is empty"
        df = pd.DataFrame(records)
        df.columns = df.columns.str.lower().str.strip()
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def update_sheet(df_rows, sheet_name="data"):
    """Bulk-update category/location/urgency columns back to sheet."""
    client, err = get_gsheet_client()
    if err:
        return False, err
    try:
        sheet = client.open(sheet_name).sheet1
        n = len(df_rows)
        categories = [[r] for r in df_rows["category"]]
        locations  = [[r] for r in df_rows["location"]]
        urgencies  = [[r] for r in df_rows["urgency"]]
        sheet.update(f"C2:C{n+1}", categories)
        sheet.update(f"D2:D{n+1}", locations)
        sheet.update(f"E2:E{n+1}", urgencies)
        return True, None
    except Exception as e:
        return False, str(e)


# ── AI Models ────────────────────────────────────────────────────────────────

EMERGENCY_LABELS = [
    "Flood", "Fire", "Medical Emergency",
    "Road Accident", "Electricity Failure",
    "Missing Person", "Rescue Required", "General"
]

URGENCY_MAP = {
    "Flood": "High", "Fire": "High",
    "Medical Emergency": "High", "Road Accident": "High",
    "Rescue Required": "High",
    "Electricity Failure": "Medium", "Missing Person": "Medium",
    "General": "Low"
}


@st.cache_resource(show_spinner=False)
def load_classifier():
    """Load zero-shot classification pipeline (cached across sessions)."""
    try:
        from transformers import pipeline
        clf = pipeline(
            "zero-shot-classification",
            model="valhalla/distilbart-mnli-12-3"
        )
        return clf, None
    except Exception as e:
        return None, str(e)


@st.cache_resource(show_spinner=False)
def load_ner():
    """Load NER pipeline (cached across sessions)."""
    try:
        from transformers import pipeline
        ner = pipeline("ner", grouped_entities=True)
        return ner, None
    except Exception as e:
        return None, str(e)


def classify_text(text: str, use_ai: bool = True) -> dict:
    """
    Classify a social media post.
    Returns: { category, urgency, confidence, method }
    Falls back to keyword logic if AI unavailable.
    """
    if use_ai:
        clf, err = load_classifier()
        if clf and not err:
            try:
                result = clf(text, EMERGENCY_LABELS)
                category = result["labels"][0]
                confidence = round(result["scores"][0] * 100, 1)
                urgency = URGENCY_MAP.get(category, "Low")
                return {
                    "category": category,
                    "urgency": urgency,
                    "confidence": confidence,
                    "method": "AI (Zero-Shot)"
                }
            except Exception:
                pass  # fall through to keyword

    # Keyword fallback
    return _keyword_classify(text)


def _keyword_classify(text: str) -> dict:
    text_l = text.lower()
    rules = [
        (["flood", "water rising", "submerged", "drowning"], "Flood", "High"),
        (["fire", "smoke", "burning", "flames"], "Fire", "High"),
        (["ambulance", "injured", "bleeding", "unconscious", "breathing"], "Medical Emergency", "High"),
        (["accident", "crash", "collision", "hit by"], "Road Accident", "High"),
        (["rescue", "trapped", "stuck", "help"], "Rescue Required", "High"),
        (["power", "transformer", "electric", "blackout"], "Electricity Failure", "Medium"),
        (["missing", "lost", "not found"], "Missing Person", "Medium"),
    ]
    for keywords, category, urgency in rules:
        if any(k in text_l for k in keywords):
            return {"category": category, "urgency": urgency, "confidence": 85.0, "method": "Keyword"}
    return {"category": "General", "urgency": "Low", "confidence": 60.0, "method": "Keyword"}


def extract_location_ner(text: str) -> str:
    """Extract location from text via NER, fallback to keyword matching."""
    ner_pipe, err = load_ner()
    if ner_pipe and not err:
        try:
            entities = ner_pipe(text)
            for ent in entities:
                if "LOC" in ent.get("entity_group", "") or "GPE" in ent.get("entity_group", ""):
                    return ent["word"].strip()
        except Exception:
            pass

    # Keyword fallback for Bengaluru areas
    known = [
        "Whitefield", "Indiranagar", "Marathahalli", "Koramangala", "HSR Layout",
        "Electronic City", "BTM Layout", "Jayanagar", "Hebbal", "Yelahanka",
        "KR Puram", "Rajajinagar", "Malleshwaram", "Peenya", "Shivajinagar",
        "JP Nagar", "Vijayanagar", "Cubbon Park", "Domlur", "Banashankari",
        "Sarjapur Road", "Bellandur", "Kadugodi", "Mahadevapura", "Bommanahalli",
    ]
    for loc in known:
        if loc.lower() in text.lower():
            return loc
    return "Unknown"


def process_dataframe(df: pd.DataFrame, use_ai: bool = True, progress_cb=None) -> pd.DataFrame:
    """Run AI classification + NER on entire dataframe."""
    results = []
    post_col = next((c for c in df.columns if "post" in c.lower()), df.columns[0])

    for i, row in df.iterrows():
        text = str(row.get(post_col, ""))
        cls = classify_text(text, use_ai=use_ai)
        loc = extract_location_ner(text)

        results.append({
            "post": text,
            "category": cls["category"],
            "urgency": cls["urgency"],
            "location": loc,
            "confidence": cls["confidence"],
            "method": cls["method"],
        })

        if progress_cb:
            progress_cb(i + 1, len(df))

    return pd.DataFrame(results)


# ── Resource Database ─────────────────────────────────────────────────────────

RESOURCES = pd.DataFrame([
    {"id": "AMB-01", "type": "Ambulance",   "status": "Available", "lat": 12.9784, "lon": 77.6408, "zone": "Central"},
    {"id": "AMB-02", "type": "Ambulance",   "status": "Available", "lat": 12.9352, "lon": 77.6245, "zone": "South"},
    {"id": "AMB-03", "type": "Ambulance",   "status": "Deployed",  "lat": 13.0358, "lon": 77.5970, "zone": "North"},
    {"id": "FTK-01", "type": "Fire Truck",  "status": "Available", "lat": 12.9698, "lon": 77.7500, "zone": "East"},
    {"id": "FTK-02", "type": "Fire Truck",  "status": "Available", "lat": 13.0285, "lon": 77.5190, "zone": "West"},
    {"id": "FTK-03", "type": "Fire Truck",  "status": "Deployed",  "lat": 12.9166, "lon": 77.6101, "zone": "South"},
    {"id": "RBT-01", "type": "Rescue Boat", "status": "Available", "lat": 12.9290, "lon": 77.6840, "zone": "Bellandur Lake"},
    {"id": "RBT-02", "type": "Rescue Boat", "status": "Available", "lat": 12.9780, "lon": 77.6220, "zone": "Ulsoor Lake"},
    {"id": "HLC-01", "type": "Helicopter",  "status": "Available", "lat": 13.1005, "lon": 77.5963, "zone": "North"},
    {"id": "MED-01", "type": "Medical Team","status": "Available", "lat": 12.9833, "lon": 77.6033, "zone": "Central"},
    {"id": "MED-02", "type": "Medical Team","status": "Available", "lat": 12.9255, "lon": 77.5468, "zone": "South-West"},
    {"id": "RSC-01", "type": "Rescue Team", "status": "Available", "lat": 12.9116, "lon": 77.6474, "zone": "South"},
])

RESOURCE_FOR_CATEGORY = {
    "Flood":             ["Rescue Boat", "Helicopter", "Rescue Team"],
    "Fire":              ["Fire Truck", "Ambulance"],
    "Medical Emergency": ["Ambulance", "Medical Team"],
    "Road Accident":     ["Ambulance", "Fire Truck"],
    "Rescue Required":   ["Rescue Team", "Helicopter"],
    "Electricity Failure":["Rescue Team"],
    "Missing Person":    ["Rescue Team"],
    "General":           ["Medical Team"],
}

LOCATION_COORDS = {
    "Whitefield":    (12.9698, 77.7500), "Indiranagar":   (12.9784, 77.6408),
    "Marathahalli":  (12.9591, 77.6974), "Koramangala":   (12.9352, 77.6245),
    "HSR Layout":    (12.9116, 77.6474), "Electronic City":(12.8399, 77.6770),
    "BTM Layout":    (12.9166, 77.6101), "Jayanagar":     (12.9250, 77.5938),
    "Hebbal":        (13.0358, 77.5970), "Yelahanka":     (13.1005, 77.5963),
    "KR Puram":      (13.0080, 77.6950), "Rajajinagar":   (12.9916, 77.5544),
    "Malleshwaram":  (13.0035, 77.5700), "Peenya":        (13.0285, 77.5190),
    "Shivajinagar":  (12.9833, 77.6033), "JP Nagar":      (12.9081, 77.5850),
    "Vijayanagar":   (12.9719, 77.5352), "Cubbon Park":   (12.9763, 77.5929),
    "Domlur":        (12.9600, 77.6387), "Banashankari":  (12.9255, 77.5468),
    "Sarjapur Road": (12.9000, 77.7000), "Bellandur":     (12.9290, 77.6840),
    "Kadugodi":      (12.9925, 77.7600), "Bommanahalli":  (12.8895, 77.6440),
}


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two lat/lon points."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def allocate_resources(incidents: pd.DataFrame) -> pd.DataFrame:
    """
    Priority-based resource allocation.
    Sorts by urgency, then assigns nearest available resource of the right type.
    Returns incidents with assigned_resource, resource_id, distance_km columns.
    """
    urgency_order = {"High": 0, "Medium": 1, "Low": 2}
    df = incidents.copy()
    df["urgency_rank"] = df["urgency"].map(urgency_order).fillna(3)
    df = df.sort_values("urgency_rank")

    resources = RESOURCES.copy()
    assignments = []

    for _, inc in df.iterrows():
        category = inc.get("category", "General")
        location = inc.get("location", "Unknown")
        preferred = RESOURCE_FOR_CATEGORY.get(category, ["Medical Team"])

        coords = LOCATION_COORDS.get(location)
        inc_lat = coords[0] if coords else 12.9716
        inc_lon = coords[1] if coords else 77.5946

        # Find nearest available preferred resource
        best = None
        best_dist = float("inf")

        for _, res in resources.iterrows():
            if res["status"] != "Available":
                continue
            if res["type"] not in preferred:
                continue
            dist = haversine(inc_lat, inc_lon, res["lat"], res["lon"])
            if dist < best_dist:
                best_dist = dist
                best = res

        if best is not None:
            resources.loc[resources["id"] == best["id"], "status"] = "Deployed"
            assignments.append({
                "assigned_resource": best["type"],
                "resource_id": best["id"],
                "distance_km": round(best_dist, 2),
                "eta_min": int(best_dist / 0.5),  # ~30 km/h urban speed
            })
        else:
            assignments.append({
                "assigned_resource": "Queued",
                "resource_id": "—",
                "distance_km": None,
                "eta_min": None,
            })

    assign_df = pd.DataFrame(assignments, index=df.index)
    result = df.join(assign_df).drop(columns=["urgency_rank"])
    return result, resources


# ── Styling helpers ───────────────────────────────────────────────────────────

URGENCY_COLORS  = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}
CATEGORY_EMOJIS = {
    "Flood": "🌊", "Fire": "🔥", "Medical Emergency": "🏥",
    "Road Accident": "🚗", "Rescue Required": "⛑️",
    "Electricity Failure": "⚡", "Missing Person": "🔍", "General": "📢"
}
RESOURCE_EMOJIS = {
    "Ambulance": "🚑", "Fire Truck": "🚒", "Rescue Boat": "🚤",
    "Helicopter": "🚁", "Medical Team": "🏥", "Rescue Team": "⛑️"
}


def urgency_badge(urgency: str) -> str:
    color = URGENCY_COLORS.get(urgency, "#94A3B8")
    return f'<span style="background:{color}22;color:{color};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;">{urgency}</span>'


def status_badge(status: str) -> str:
    c = {"Available": "#10B981", "Deployed": "#F59E0B", "Queued": "#EF4444"}.get(status, "#64748B")
    return f'<span style="background:{c}22;color:{c};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;">{status}</span>'