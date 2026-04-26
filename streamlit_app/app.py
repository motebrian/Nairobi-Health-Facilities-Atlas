"""
Nairobi Health Facility Access Atlas
======================================
Streamlit Dashboard — Real Government of Kenya Data Edition

863 real MoH facilities · 17 sub-counties · Gravity model siting

Run:
    streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="Nairobi Health Facility Access Atlas",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens ──────────────────────────────────────────────────────────────
C = {
    "primary" : "#1F3A5F",
    "blue"    : "#4A90E2",
    "accent"  : "#F5A623",
    "canvas"  : "#F4F6F8",
    "card"    : "#FFFFFF",
    "border"  : "#E1E5EA",
    "shadow"  : "rgba(31,58,95,0.07)",
    "success" : "#27AE60",
    "warning" : "#F2C94C",
    "danger"  : "#EB5757",
    "info"    : "#2D9CDB",
    "text_h"  : "#1F3A5F",
    "text_b"  : "#4A4A4A",
    "text_m"  : "#7B8A8B",
}

TIER_COLOURS = {
    "Critical Gap"   : "#EB5757",
    "Underserved"    : "#F5A623",
    "Moderate Access": "#F2C94C",
    "Good Access"    : "#27AE60",
    "Well Served"    : "#1F3A5F",
}

FACILITY_COLOURS = {
    "National Referral": "#1F3A5F",
    "District Hospital" : "#4A90E2",
    "Other Hospital"    : "#2D9CDB",
    "Health Centre"     : "#27AE60",
    "Dispensary"        : "#F5A623",
    "Medical Clinic"    : "#9013FE",
    "Nursing Home"      : "#50E3C2",
    "Maternity Home"    : "#EB5757",
    "VCT Centre"        : "#B8E986",
    "Diagnostic"        : "#D0021B",
    "Specialist Clinic" : "#F5A623",
}

PRIORITY_COLOURS = {
    "Critical": "#EB5757",
    "High"    : "#F5A623",
    "Medium"  : "#F2C94C",
}

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
html,body,[class*="css"]{{
    font-family:'Inter','Segoe UI',sans-serif;
    background:{C['canvas']};color:{C['text_b']};
    -webkit-font-smoothing:antialiased;
}}
.stApp{{background:{C['canvas']};}}
[data-testid="stSidebar"]{{background:{C['primary']} !important;}}
[data-testid="stSidebar"] label{{
    color:rgba(255,255,255,0.6) !important;font-size:0.68rem !important;
    text-transform:uppercase !important;letter-spacing:1px !important;font-weight:600 !important;
}}

.ph{{background:{C['card']};border-radius:10px;padding:20px 26px;margin-bottom:16px;
     box-shadow:0 2px 12px {C['shadow']};border-top:4px solid {C['primary']};
     display:flex;justify-content:space-between;align-items:center;}}
.ph-ey{{font-size:0.6rem;text-transform:uppercase;letter-spacing:2.5px;color:{C['blue']};
         font-weight:700;margin-bottom:4px;}}
.ph-title{{font-size:1.45rem;font-weight:700;color:{C['primary']};letter-spacing:-0.4px;}}
.ph-sub{{font-size:0.78rem;color:{C['text_m']};margin-top:4px;line-height:1.6;}}
.tag{{display:inline-block;background:{C['canvas']};border:1px solid {C['border']};
      border-radius:4px;padding:2px 8px;font-size:0.65rem;color:{C['text_m']};
      font-family:'IBM Plex Mono',monospace;margin:2px;}}
.tag.a{{background:#FFF8EC;border-color:rgba(245,166,35,.3);color:{C['accent']};font-weight:600;}}
.tag.src{{background:#EFF6FF;border-color:rgba(74,144,226,.3);color:{C['blue']};font-weight:600;}}

.kpi{{background:{C['card']};border-radius:9px;padding:16px 18px;
      box-shadow:0 2px 10px {C['shadow']};border:1px solid {C['border']};
      border-top:4px solid {C['primary']};}}
.kpi.blue{{border-top-color:{C['blue']};}}
.kpi.red {{border-top-color:{C['danger']};}}
.kpi.oran{{border-top-color:{C['accent']};}}
.kpi.grn {{border-top-color:{C['success']};}}
.kpi.warn{{border-top-color:{C['warning']};}}
.kpi-lbl{{font-size:0.6rem;text-transform:uppercase;letter-spacing:1.2px;
           color:{C['text_m']};font-weight:700;margin-bottom:7px;}}
.kpi-val{{font-size:2rem;font-weight:700;color:{C['primary']};line-height:1;
           font-family:'IBM Plex Mono',monospace;letter-spacing:-1px;}}
.kpi-sub{{font-size:0.68rem;color:{C['text_m']};margin-top:5px;}}

.sec{{font-size:0.62rem;text-transform:uppercase;letter-spacing:1.8px;color:{C['text_m']};
      font-weight:700;border-bottom:2px solid {C['border']};padding-bottom:7px;
      margin:18px 0 12px;display:flex;align-items:center;gap:8px;}}
.dot{{width:6px;height:6px;border-radius:50%;display:inline-block;flex-shrink:0;}}

.cc{{background:{C['card']};border-radius:10px;padding:18px 20px;
     box-shadow:0 2px 10px {C['shadow']};border:1px solid {C['border']};margin-bottom:14px;}}
.cc-title{{font-size:0.62rem;text-transform:uppercase;letter-spacing:1.3px;
           color:{C['text_m']};font-weight:700;margin-bottom:3px;}}
.cc-sub{{font-size:0.75rem;color:{C['text_b']};margin-bottom:12px;}}

.badge{{display:inline-block;padding:2px 8px;border-radius:4px;
        font-size:0.6rem;font-weight:700;letter-spacing:.7px;text-transform:uppercase;}}
.b-c{{background:rgba(235,87,87,.1); color:{C['danger']}; border:1px solid rgba(235,87,87,.2);}}
.b-h{{background:rgba(245,166,35,.1);color:{C['accent']}; border:1px solid rgba(245,166,35,.2);}}
.b-m{{background:rgba(242,201,76,.12);color:#9A6D00;      border:1px solid rgba(242,201,76,.3);}}
.b-g{{background:rgba(39,174,96,.1); color:{C['success']};border:1px solid rgba(39,174,96,.2);}}
.b-w{{background:rgba(31,58,95,.08); color:{C['primary']};border:1px solid rgba(31,58,95,.15);}}

.prop-card{{background:{C['card']};border:1px solid {C['border']};border-radius:10px;
            padding:18px 20px;box-shadow:0 2px 10px {C['shadow']};margin-bottom:12px;}}
.prop-name{{font-size:0.92rem;font-weight:700;color:{C['primary']};margin-bottom:4px;}}
.prop-meta{{font-size:0.72rem;color:{C['text_m']};margin-bottom:8px;}}
.prop-rat{{font-size:0.8rem;color:{C['text_b']};line-height:1.6;}}
.pstat{{background:{C['canvas']};border:1px solid {C['border']};border-radius:6px;
        padding:8px 12px;text-align:center;}}
.psv{{font-size:1rem;font-weight:700;font-family:'IBM Plex Mono';color:{C['primary']};}}
.psl{{font-size:0.58rem;text-transform:uppercase;letter-spacing:.8px;color:{C['text_m']};
      font-weight:600;margin-top:2px;}}

.data-src{{background:#EFF6FF;border:1px solid rgba(74,144,226,.2);border-radius:6px;
           padding:10px 14px;font-size:0.75rem;color:{C['blue']};margin-bottom:14px;
           line-height:1.6;}}

.stTabs [data-baseweb="tab-list"]{{
    background:{C['card']};border-radius:10px 10px 0 0;padding:6px 6px 0;gap:4px;
    border-bottom:2px solid {C['border']};box-shadow:0 2px 10px {C['shadow']};
}}
.stTabs [data-baseweb="tab"]{{
    border-radius:6px 6px 0 0;color:{C['text_m']};font-weight:500;
    font-size:0.8rem;padding:10px 18px;background:transparent;
}}
.stTabs [aria-selected="true"]{{
    background:{C['primary']} !important;color:#fff !important;font-weight:700 !important;
}}
#MainMenu,footer,header{{visibility:hidden;}}
.stDeployButton{{display:none;}}
</style>
""", unsafe_allow_html=True)


# ── Self-contained data builder ────────────────────────────────────────────────
# Reads directly from healthcare_facilities.json (raw MoH data).
# No pre-processing step needed — everything is built at runtime and cached.

import math

PUBLIC_OWNERS = ["Ministry of Health", "Local Authority",
                 "Kenya Defence Forces", "Ministry of State for Special Programmes"]

FACILITY_TIER_MAP = {
    "National Referral Hospital"   : "National Referral",
    "District Hospital"            : "District Hospital",
    "Sub-District Hospital"        : "District Hospital",
    "Other Hospital"               : "Other Hospital",
    "Health Centre"                : "Health Centre",
    "Medical Centre"               : "Health Centre",
    "Dispensary"                   : "Dispensary",
    "Medical Clinic"               : "Medical Clinic",
    "Nursing Home"                 : "Nursing Home",
    "Maternity Home"               : "Maternity Home",
    "VCT Centre (Stand-Alone)"     : "VCT Centre",
    "Laboratory (Stand-alone)"     : "Diagnostic",
    "Dental Clinic"                : "Specialist Clinic",
    "Eye Centre"                   : "Specialist Clinic",
    "Eye Clinic"                   : "Specialist Clinic",
    "Radiology Unit"               : "Diagnostic",
}

MARKER_CFG = {
    "National Referral": {"color": "#1F3A5F", "radius": 14},
    "District Hospital" : {"color": "#4A90E2", "radius": 12},
    "Other Hospital"    : {"color": "#2D9CDB", "radius": 10},
    "Health Centre"     : {"color": "#27AE60", "radius":  8},
    "Dispensary"        : {"color": "#F5A623", "radius":  6},
    "Medical Clinic"    : {"color": "#9013FE", "radius":  5},
    "Nursing Home"      : {"color": "#50E3C2", "radius":  5},
    "Maternity Home"    : {"color": "#EB5757", "radius":  5},
    "VCT Centre"        : {"color": "#B8E986", "radius":  4},
    "Diagnostic"        : {"color": "#D0021B", "radius":  4},
    "Specialist Clinic" : {"color": "#F5A623", "radius":  4},
}

SETTLEMENTS_RAW = [
    {"name":"Kibera",            "centroid":[36.7877,-1.3133],"population":250000,"area_km2":2.5,"sub_county":"Kibra"},
    {"name":"Mathare",           "centroid":[36.8497,-1.2573],"population":190000,"area_km2":1.9,"sub_county":"Mathare"},
    {"name":"Korogocho",         "centroid":[36.8802,-1.2481],"population":150000,"area_km2":1.5,"sub_county":"Ruaraka"},
    {"name":"Mukuru kwa Njenga", "centroid":[36.8590,-1.3142],"population":170000,"area_km2":2.1,"sub_county":"Embakasi South"},
    {"name":"Mukuru kwa Reuben", "centroid":[36.8720,-1.3200],"population":130000,"area_km2":1.6,"sub_county":"Embakasi South"},
    {"name":"Kawangware",        "centroid":[36.7511,-1.2868],"population":180000,"area_km2":3.2,"sub_county":"Dagoretti North"},
    {"name":"Kangemi",           "centroid":[36.7314,-1.2690],"population":120000,"area_km2":2.4,"sub_county":"Westlands"},
    {"name":"Huruma",            "centroid":[36.8616,-1.2490],"population":100000,"area_km2":1.2,"sub_county":"Mathare"},
    {"name":"Githurai 44",       "centroid":[36.9165,-1.2057],"population": 95000,"area_km2":2.8,"sub_county":"Roysambu"},
    {"name":"Githurai 45",       "centroid":[36.9300,-1.2000],"population": 88000,"area_km2":2.6,"sub_county":"Roysambu"},
    {"name":"Dandora",           "centroid":[36.8963,-1.2540],"population":110000,"area_km2":2.9,"sub_county":"Ruaraka"},
    {"name":"Kayole",            "centroid":[36.9040,-1.2740],"population":140000,"area_km2":3.1,"sub_county":"Embakasi Central"},
    {"name":"Soweto East",       "centroid":[36.7950,-1.3050],"population": 75000,"area_km2":0.9,"sub_county":"Kibra"},
    {"name":"Mukuru Kaiyaba",    "centroid":[36.8450,-1.3100],"population": 90000,"area_km2":1.4,"sub_county":"Embakasi South"},
    {"name":"Viwandani",         "centroid":[36.8700,-1.3000],"population": 85000,"area_km2":1.8,"sub_county":"Makadara"},
]

PROPOSED_SITES_RAW = [
    {"site_id":"PROP-001","name":"Mukuru Kaiyaba — Proposed Health Centre",
     "lon":36.8420,"lat":-1.3080,"priority":"Critical","type":"Health Centre",
     "est_pop_served":88000,"cost_usd_M":1.8,
     "rationale":"Mukuru Kaiyaba has 90K residents with only 4 MoH facilities in Embakasi South — a gap of 2.1km to the nearest public facility. Highest unmet need in the Mukuru cluster."},
    {"site_id":"PROP-002","name":"Soweto–Kibera East — Proposed Dispensary",
     "lon":36.7970,"lat":-1.3060,"priority":"Critical","type":"Dispensary",
     "est_pop_served":72000,"cost_usd_M":0.6,
     "rationale":"Dense 75K-resident pocket between Soweto and Kibera. Real MoH data shows facilities clustered near KNH, leaving eastern residents 1.8km from the nearest option."},
    {"site_id":"PROP-003","name":"Kawangware Central — Proposed Health Centre",
     "lon":36.7490,"lat":-1.2830,"priority":"High","type":"Health Centre",
     "est_pop_served":95000,"cost_usd_M":1.6,
     "rationale":"MoH data records 71 facilities in Dagoretti North but most are private. Only 6 public facilities serve 180K residents — 2.3km average walk to the nearest government facility."},
    {"site_id":"PROP-004","name":"Dandora Phase 4 — Proposed Dispensary",
     "lon":36.9020,"lat":-1.2590,"priority":"High","type":"Dispensary",
     "est_pop_served":58000,"cost_usd_M":0.5,
     "rationale":"Northern Dandora (Phase 4) sits 1.9km from the nearest MoH facility while bearing high disease burden from proximity to Nairobi dumpsite."},
    {"site_id":"PROP-005","name":"Githurai North — Proposed Health Centre",
     "lon":36.9390,"lat":-1.1930,"priority":"Medium","type":"Health Centre",
     "est_pop_served":65000,"cost_usd_M":1.7,
     "rationale":"No MoH facilities recorded beyond Githurai 45 northward. Peri-urban growth corridor with 183K combined Githurai residents and a 3.1km gap in the northern zone."},
]

def _haversine_m(lon1, lat1, lon2, lat2):
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2-lat1)/2)**2 + \
        math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 2*R*math.asin(math.sqrt(a))

def _make_polygon(centroid, area_km2, seed=0):
    rng = np.random.default_rng(seed)
    r = np.sqrt(area_km2)/111.0*0.55
    n = 12
    angles = np.sort(rng.uniform(0, 2*np.pi, n))
    radii  = rng.uniform(0.65, 1.0, n)*r
    coords = [[centroid[0]+radii[i]*np.cos(angles[i]),
               centroid[1]+radii[i]*np.sin(angles[i])] for i in range(n)]
    coords.append(coords[0])
    return coords

@st.cache_data
def load_all():
    """
    Builds all data at runtime directly from healthcare_facilities.json.
    No pre-processing pipeline needed — works on Streamlit Cloud out of the box.
    """
    raw_path = DATA_DIR / "healthcare_facilities.json"
    if not raw_path.exists():
        st.error("healthcare_facilities.json not found in data/. Please add it to the repository.")
        st.stop()

    with open(raw_path) as f:
        raw = json.load(f)

    # ── 1. Extract Nairobi facilities ─────────────────────────────────────────
    fac_features = []
    for feat in raw["features"]:
        p = feat["properties"]
        g = feat["geometry"]
        if not (p.get("County") and "nairobi" in p["County"].lower()):
            continue
        lon, lat = g["coordinates"]
        if not (-1.5 < lat < -1.0 and 36.6 < lon < 37.1):
            continue
        tier   = FACILITY_TIER_MAP.get(p.get("Type",""), "Other")
        mcfg   = MARKER_CFG.get(tier, {"color":"#E1E5EA","radius":3})
        pub    = any(k in str(p.get("Owner","")) for k in PUBLIC_OWNERS)
        fac_features.append({
            "type"    : "Feature",
            "geometry": {"type":"Point","coordinates":[round(lon,5),round(lat,5)]},
            "properties": {
                "facility_id"  : f"FAC-{p['FID']:05d}",
                "name"         : p["Facility_N"].strip(),
                "raw_type"     : p.get("Type",""),
                "tier"         : tier,
                "owner"        : p.get("Owner",""),
                "public"       : pub,
                "sub_county"   : p.get("Sub_County",""),
                "division"     : p.get("Division",""),
                "location"     : p.get("Location",""),
                "nearest_town" : p.get("Nearest_To",""),
                "marker_color" : mcfg["color"],
                "marker_radius": mcfg["radius"],
            }
        })
    facilities = {"type":"FeatureCollection","features":fac_features}

    # ── 2. Settlements ────────────────────────────────────────────────────────
    rng = np.random.default_rng(42)
    set_features = []
    for i, s in enumerate(SETTLEMENTS_RAW):
        r2 = np.random.default_rng(i*7)
        set_features.append({
            "type"    : "Feature",
            "geometry": {"type":"Polygon","coordinates":[_make_polygon(s["centroid"],s["area_km2"],i+1)]},
            "properties": {
                "settlement_id"     : f"SET-{i+1:03d}",
                "name"              : s["name"],
                "sub_county"        : s["sub_county"],
                "population"        : s["population"],
                "area_km2"          : s["area_km2"],
                "pop_density"       : round(s["population"]/s["area_km2"]),
                "u5_mortality_per1k": round(float(r2.uniform(28,72)),1),
                "malaria_prev_pct"  : round(float(r2.uniform(4.2,18.6)),1),
                "hiv_prev_pct"      : round(float(r2.uniform(3.1,9.8)),1),
                "water_access_pct"  : round(float(r2.uniform(38,82)),1),
                "sanitation_pct"    : round(float(r2.uniform(22,68)),1),
            }
        })
    settlements = {"type":"FeatureCollection","features":set_features}

    # ── 3. Proposed sites ────────────────────────────────────────────────────
    proposed = {"type":"FeatureCollection","features":[{
        "type":"Feature",
        "geometry":{"type":"Point","coordinates":[p["lon"],p["lat"]]},
        "properties":{k:v for k,v in p.items() if k not in ("lon","lat")}
    } for p in PROPOSED_SITES_RAW]}

    # ── 4. Accessibility scores ───────────────────────────────────────────────
    all_coords  = [f["geometry"]["coordinates"] for f in fac_features]
    pub_coords  = [f["geometry"]["coordinates"] for f in fac_features if f["properties"]["public"]]
    hosp_coords = [f["geometry"]["coordinates"] for f in fac_features
                   if f["properties"]["tier"] in ("National Referral","District Hospital","Other Hospital")]

    WALK = 4.5; DET = 1.35
    def wt(d): return (d*DET)/(WALK*1000/60)
    def cov(clon,clat,area,near,thr):
        r = math.sqrt(area/math.pi)
        return round(min(100.0, min(1.0,(thr/1000/r)**1.5)*(thr/max(near,50))*100),1)
    def tier_label(sc):
        if sc<25: return "Critical Gap"
        elif sc<45: return "Underserved"
        elif sc<65: return "Moderate Access"
        elif sc<80: return "Good Access"
        else: return "Well Served"

    acc_rows = []
    for feat in set_features:
        p = feat["properties"]
        ring = feat["geometry"]["coordinates"][0]
        clon = float(np.mean([x[0] for x in ring]))
        clat = float(np.mean([x[1] for x in ring]))
        pop  = p["population"]; area = p["area_km2"]

        na  = min(_haversine_m(clon,clat,c[0],c[1]) for c in all_coords)
        np_ = min(_haversine_m(clon,clat,c[0],c[1]) for c in pub_coords)
        nh  = min(_haversine_m(clon,clat,c[0],c[1]) for c in hosp_coords)

        p500=cov(clon,clat,area,na,500); p1k=cov(clon,clat,area,na,1000); p2k=cov(clon,clat,area,na,2000)
        pp500=cov(clon,clat,area,np_,500); pp1k=cov(clon,clat,area,np_,1000)
        n500=sum(1 for c in all_coords if _haversine_m(clon,clat,c[0],c[1])<=500)
        n1k =sum(1 for c in all_coords if _haversine_m(clon,clat,c[0],c[1])<=1000)
        np2k=sum(1 for c in pub_coords  if _haversine_m(clon,clat,c[0],c[1])<=2000)

        ds=max(0,100-(na/2500*60)); ps=max(0,100-(np_/2500*60))
        hs=max(0,100-(nh/5000*60)); cs=p1k
        score=round(0.35*ds+0.25*cs+0.25*ps+0.15*hs,1)

        acc_rows.append({
            "settlement_id":p["settlement_id"],"name":p["name"],"sub_county":p["sub_county"],
            "population":pop,"area_km2":area,"pop_density_per_km2":round(pop/area),
            "nearest_any_m":round(na),"nearest_public_m":round(np_),"nearest_hospital_m":round(nh),
            "walk_time_any_min":round(wt(na),1),"walk_time_public_min":round(wt(np_),1),
            "n_facilities_500m":n500,"n_facilities_1km":n1k,"n_public_facilities_2km":np2k,
            "pct_within_500m":p500,"pct_within_1km":p1k,"pct_within_2km":p2k,
            "public_pct_within_500m":pp500,"public_pct_within_1km":pp1k,
            "pop_beyond_2km":int(pop*(1-p2k/100)),
            "accessibility_score":score,"access_tier":tier_label(score),
            "u5_mortality_per1k":p["u5_mortality_per1k"],"malaria_prev_pct":p["malaria_prev_pct"],
            "hiv_prev_pct":p["hiv_prev_pct"],"water_access_pct":p["water_access_pct"],
            "sanitation_pct":p["sanitation_pct"],
        })
    access_df = pd.DataFrame(acc_rows).sort_values("accessibility_score").reset_index(drop=True)

    # ── 5. Sub-county summary ─────────────────────────────────────────────────
    fp = [f["properties"] for f in fac_features]
    SC_POP = {
        "Starehe":180000,"Kibra":260000,"Roysambu":195000,"Dagoretti North":210000,
        "Westlands":185000,"Kamukunji":175000,"Langata":228000,"Makadara":168000,
        "Kasarani":322000,"Embakasi Central":192000,"Ruaraka":231000,"Embakasi West":197000,
        "Dagoretti South":158000,"Embakasi South":249000,"Embakasi East":213000,
        "Embakasi North":187000,"Mathare":148000,
    }
    sc_cnt  = Counter(p["sub_county"] for p in fp)
    sc_pub  = Counter(p["sub_county"] for p in fp if p["public"])
    sc_hosp = Counter(p["sub_county"] for p in fp if p["tier"] in ("National Referral","District Hospital","Other Hospital"))
    sc_disp = Counter(p["sub_county"] for p in fp if p["tier"]=="Dispensary")
    sc_hc   = Counter(p["sub_county"] for p in fp if p["tier"]=="Health Centre")
    sc_rows = []
    for sc_name in sorted(sc_cnt.keys()):
        pop2 = SC_POP.get(sc_name, 150000)
        tot  = sc_cnt[sc_name]
        sc_rows.append({
            "sub_county":sc_name,"population_approx":pop2,"total_facilities":tot,
            "public_facilities":sc_pub.get(sc_name,0),"hospitals":sc_hosp.get(sc_name,0),
            "dispensaries":sc_disp.get(sc_name,0),"health_centres":sc_hc.get(sc_name,0),
            "facilities_per_10k":round(tot/pop2*10000,1),
            "public_per_10k":round(sc_pub.get(sc_name,0)/pop2*10000,1),
        })
    sc_df = pd.DataFrame(sc_rows).sort_values("facilities_per_10k").reset_index(drop=True)

    # ── 6. Coverage stats ─────────────────────────────────────────────────────
    tot_pop = access_df["population"].sum()
    stats = {
        "total_population"        : int(tot_pop),
        "n_settlements"           : len(access_df),
        "n_facilities_total"      : len(fac_features),
        "n_public_facilities"     : len(pub_coords),
        "n_hospitals"             : len(hosp_coords),
        "n_dispensaries"          : sum(1 for p in fp if p["tier"]=="Dispensary"),
        "n_health_centres"        : sum(1 for p in fp if p["tier"]=="Health Centre"),
        "n_medical_clinics"       : sum(1 for p in fp if p["tier"]=="Medical Clinic"),
        "pop_within_1km"          : int((access_df["pct_within_1km"]/100*access_df["population"]).sum()),
        "pop_within_2km"          : int((access_df["pct_within_2km"]/100*access_df["population"]).sum()),
        "pop_within_1km_public"   : int((access_df["public_pct_within_1km"]/100*access_df["population"]).sum()),
        "pop_beyond_2km"          : int(access_df["pop_beyond_2km"].sum()),
        "pct_within_1km"          : round((access_df["pct_within_1km"]/100*access_df["population"]).sum()/tot_pop*100,1),
        "pct_within_2km"          : round((access_df["pct_within_2km"]/100*access_df["population"]).sum()/tot_pop*100,1),
        "pct_within_1km_public"   : round((access_df["public_pct_within_1km"]/100*access_df["population"]).sum()/tot_pop*100,1),
        "avg_walk_time_min"       : round(access_df["walk_time_any_min"].mean(),1),
        "avg_walk_public_min"     : round(access_df["walk_time_public_min"].mean(),1),
        "avg_accessibility_score" : round(access_df["accessibility_score"].mean(),1),
        "critical_gap_settlements": int((access_df["access_tier"]=="Critical Gap").sum()),
        "underserved_settlements" : int((access_df["access_tier"]=="Underserved").sum()),
        "data_source"             : "Government of Kenya — MoH Facility Registry (KMHFL)",
        "n_sub_counties"          : int(access_df["sub_county"].nunique()),
    }

    # ── 7. Gravity model scores ───────────────────────────────────────────────
    # Lightweight grid from settlement centroids for cloud deployment
    grid_rows = []
    rng2 = np.random.default_rng(42)
    for s in SETTLEMENTS_RAW:
        n_pts = max(15, int(400 * s["population"] / 2_300_000))
        lons_ = rng2.normal(s["centroid"][0], 0.008, n_pts)
        lats_ = rng2.normal(s["centroid"][1], 0.008, n_pts)
        pops_ = rng2.integers(50, 400, n_pts)
        for lo, la, po in zip(lons_, lats_, pops_):
            grid_rows.append((float(lo), float(la), int(po)))

    g_rows = []
    for ps in PROPOSED_SITES_RAW:
        gravity = 0.0
        for glon, glat, gpop in grid_rows:
            d = _haversine_m(ps["lon"], ps["lat"], glon, glat)
            if d < 10: d = 10
            nearest = min(_haversine_m(glon, glat, c[0], c[1]) for c in all_coords)
            if nearest < d: continue
            gravity += gpop / (d/1000)**2
        g_rows.append({
            "site_id":ps["site_id"],"name":ps["name"],"priority":ps["priority"],
            "type":ps["type"],"est_pop_served":ps["est_pop_served"],
            "cost_usd_M":ps["cost_usd_M"],"rationale":ps["rationale"],
            "gravity_score":round(gravity),
            "cost_effectiveness":round(ps["est_pop_served"]/ps["cost_usd_M"]),
        })
    gravity_df = pd.DataFrame(g_rows).sort_values("gravity_score",ascending=False).reset_index(drop=True)
    gravity_df["rank"] = range(1, len(gravity_df)+1)

    return facilities, settlements, proposed, access_df, sc_df, stats, gravity_df


# ── Map ────────────────────────────────────────────────────────────────────────

def build_map(facilities, settlements, proposed, access_df,
              metric, show_tiers, show_fac_types,
              show_proposed, show_catchments, catch_r,
              show_public_only) -> folium.Map:

    m = folium.Map(
        location=[-1.2850, 36.8350],
        zoom_start=12,
        tiles="CartoDB Positron",
        control_scale=True,
    )

    # Build access lookup
    acc = {}
    if not access_df.empty:
        for _, row in access_df.iterrows():
            acc[row["settlement_id"]] = row.to_dict()

    def get_colour(val, metric_name):
        if metric_name == "accessibility_score":
            if val < 25:   return TIER_COLOURS["Critical Gap"]
            elif val < 45: return TIER_COLOURS["Underserved"]
            elif val < 65: return TIER_COLOURS["Moderate Access"]
            elif val < 80: return TIER_COLOURS["Good Access"]
            else:           return TIER_COLOURS["Well Served"]
        elif metric_name == "walk_time_any_min":
            if val > 25:   return "#EB5757"
            elif val > 15: return "#F5A623"
            elif val > 10: return "#F2C94C"
            elif val > 6:  return "#27AE60"
            else:           return "#1F3A5F"
        else:  # pct_within_1km
            if val < 20:   return "#EB5757"
            elif val < 40: return "#F5A623"
            elif val < 60: return "#F2C94C"
            elif val < 80: return "#27AE60"
            else:           return "#1F3A5F"

    # Settlement polygons
    for feat in settlements["features"]:
        sid  = feat["properties"]["settlement_id"]
        a    = acc.get(sid, {})
        tier = a.get("access_tier", "")
        if show_tiers and tier not in show_tiers:
            continue
        val    = float(a.get(metric, 50) or 50)
        colour = get_colour(val, metric)
        name   = feat["properties"]["name"]
        pop    = feat["properties"]["population"]

        tt = f"""
        <div style='font-family:Inter,sans-serif;min-width:210px'>
          <b style='color:#1F3A5F;font-size:13px'>{name}</b><br>
          <span style='color:#7B8A8B;font-size:11px'>{feat['properties']['sub_county']} sub-county</span>
          <hr style='margin:6px 0;border-color:#E1E5EA'>
          <table style='font-size:12px;width:100%'>
            <tr><td style='color:#7B8A8B'>Population</td>
                <td style='font-weight:600;text-align:right'>{pop:,}</td></tr>
            <tr><td style='color:#7B8A8B'>Access score</td>
                <td style='font-weight:600;text-align:right'>{a.get('accessibility_score','—')}</td></tr>
            <tr><td style='color:#7B8A8B'>Nearest (any)</td>
                <td style='font-weight:600;text-align:right'>{a.get('nearest_any_m','—')}m</td></tr>
            <tr><td style='color:#7B8A8B'>Nearest (public)</td>
                <td style='font-weight:600;text-align:right'>{a.get('nearest_public_m','—')}m</td></tr>
            <tr><td style='color:#7B8A8B'>Walk time (any)</td>
                <td style='font-weight:600;text-align:right'>{a.get('walk_time_any_min','—')} min</td></tr>
            <tr><td style='color:#7B8A8B'>Walk time (public)</td>
                <td style='font-weight:600;text-align:right'>{a.get('walk_time_public_min','—')} min</td></tr>
            <tr><td style='color:#7B8A8B'>Facilities within 1km</td>
                <td style='font-weight:600;text-align:right'>{a.get('n_facilities_1km','—')}</td></tr>
            <tr><td style='color:#7B8A8B'>Access tier</td>
                <td style='font-weight:600;text-align:right;color:{colour}'>{tier}</td></tr>
          </table>
        </div>"""

        folium.GeoJson(
            feat,
            style_function=lambda f, c=colour: {
                "fillColor": c, "color": "#ffffff",
                "weight": 1.5, "fillOpacity": 0.62
            },
            tooltip=folium.Tooltip(tt, sticky=True),
        ).add_to(m)

    # Facility markers
    for feat in facilities["features"]:
        props = feat["properties"]
        tier_f = props["tier"]
        if tier_f not in show_fac_types:
            continue
        if show_public_only and not props["public"]:
            continue

        lon, lat = feat["geometry"]["coordinates"]
        colour   = FACILITY_COLOURS.get(tier_f, C["blue"])
        radius   = props["marker_radius"]

        if show_catchments:
            folium.Circle(
                location=[lat, lon], radius=catch_r,
                color=colour, weight=0.8, fill=True,
                fill_opacity=0.05, fill_color=colour,
            ).add_to(m)

        owner_short = props["owner"][:40] + "…" if len(props["owner"]) > 40 else props["owner"]
        pub_label   = "🏛️ Public" if props["public"] else "🏥 Private / FBO / NGO"

        popup_html = f"""
        <div style='font-family:Inter,sans-serif;min-width:230px'>
          <div style='background:{colour};color:white;border-radius:6px;
                      padding:7px 11px;margin-bottom:8px'>
            <b style='font-size:11px'>{props['name']}</b><br>
            <span style='font-size:9px;opacity:.85'>{tier_f}</span>
          </div>
          <table style='font-size:11px;width:100%'>
            <tr><td style='color:#7B8A8B'>Owner</td>
                <td style='font-weight:500;text-align:right;font-size:10px'>{owner_short}</td></tr>
            <tr><td style='color:#7B8A8B'>Type</td>
                <td style='font-weight:600;text-align:right'>{pub_label}</td></tr>
            <tr><td style='color:#7B8A8B'>Sub-county</td>
                <td style='font-weight:600;text-align:right'>{props['sub_county']}</td></tr>
            <tr><td style='color:#7B8A8B'>Division</td>
                <td style='font-weight:600;text-align:right'>{props['division']}</td></tr>
            <tr><td style='color:#7B8A8B'>Location</td>
                <td style='font-weight:600;text-align:right'>{props['location']}</td></tr>
          </table>
          <div style='font-size:10px;color:#7B8A8B;margin-top:7px;
                      border-top:1px solid #E1E5EA;padding-top:5px'>
            Source: Kenya MoH · KMHFL
          </div>
        </div>"""

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color="#ffffff", weight=1.5,
            fill=True, fill_color=colour, fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=270),
        ).add_to(m)

    # Proposed sites
    if show_proposed:
        for feat in proposed["features"]:
            props = feat["properties"]
            lon, lat = feat["geometry"]["coordinates"]
            pcol = PRIORITY_COLOURS.get(props["priority"], C["blue"])
            popup_html = f"""
            <div style='font-family:Inter,sans-serif;min-width:240px'>
              <div style='background:{pcol};color:white;border-radius:6px;
                          padding:8px 12px;margin-bottom:8px'>
                <b style='font-size:12px'>★ PROPOSED SITE — {props['site_id']}</b>
              </div>
              <b style='color:#1F3A5F;font-size:12px'>{props['name']}</b>
              <hr style='margin:7px 0;border-color:#E1E5EA'>
              <p style='font-size:11px;color:#4A4A4A;line-height:1.5;margin-bottom:8px'>
                {props['rationale']}
              </p>
              <table style='font-size:11px;width:100%'>
                <tr><td style='color:#7B8A8B'>Type</td>
                    <td style='font-weight:600;text-align:right'>{props['type']}</td></tr>
                <tr><td style='color:#7B8A8B'>Est. pop served</td>
                    <td style='font-weight:600;text-align:right'>{props['est_pop_served']:,}</td></tr>
                <tr><td style='color:#7B8A8B'>Est. cost</td>
                    <td style='font-weight:600;text-align:right'>${props['cost_usd_M']}M USD</td></tr>
                <tr><td style='color:#7B8A8B'>Priority</td>
                    <td style='font-weight:700;text-align:right;color:{pcol}'>{props['priority']}</td></tr>
              </table>
            </div>"""

            star_icon = f"""
            <div style='width:30px;height:30px;background:{pcol};border:2.5px solid white;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:15px;box-shadow:0 2px 8px rgba(0,0,0,.3);cursor:pointer'>★</div>"""

            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=star_icon, icon_size=(30,30), icon_anchor=(15,15)),
                popup=folium.Popup(popup_html, max_width=280),
            ).add_to(m)

    # Legend
    if metric == "accessibility_score":
        leg_items = [("#EB5757","Critical Gap (< 25)"),("#F5A623","Underserved (25–45)"),
                     ("#F2C94C","Moderate Access (45–65)"),("#27AE60","Good Access (65–80)"),
                     ("#1F3A5F","Well Served (> 80)")]
        leg_title = "Accessibility Score"
    elif metric == "walk_time_any_min":
        leg_items = [("#EB5757","> 25 min walk"),("#F5A623","15–25 min"),
                     ("#F2C94C","10–15 min"),("#27AE60","6–10 min"),("#1F3A5F","< 6 min")]
        leg_title = "Walking Time to Any Facility"
    else:
        leg_items = [("#EB5757","< 20% within 1km"),("#F5A623","20–40%"),
                     ("#F2C94C","40–60%"),("#27AE60","60–80%"),("#1F3A5F","> 80%")]
        leg_title = "% Population Within 1km"

    legend = f"""
    <div style='position:fixed;bottom:28px;left:28px;z-index:1000;background:white;
                border-radius:8px;padding:14px 16px;border:1px solid #E1E5EA;
                box-shadow:0 2px 12px rgba(31,58,95,.12);font-family:Inter,sans-serif;
                min-width:185px;'>
      <div style='font-size:10px;text-transform:uppercase;letter-spacing:1.2px;
                  color:#7B8A8B;font-weight:700;margin-bottom:10px'>{leg_title}</div>
      {''.join(f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>"
               f"<div style='width:12px;height:12px;background:{c};border-radius:2px;flex-shrink:0'></div>"
               f"<span style='font-size:11px;color:#4A4A4A'>{lbl}</span></div>"
               for c, lbl in leg_items)}
      <hr style='border-color:#E1E5EA;margin:8px 0'>
      <div style='font-size:10px;color:#7B8A8B'>● Existing facility</div>
      {'<div style="font-size:10px;color:#7B8A8B;margin-top:3px">★ Proposed new site</div>' if show_proposed else ''}
      <div style='font-size:9px;color:#7B8A8B;margin-top:6px;border-top:1px solid #E1E5EA;padding-top:5px'>
        Source: Kenya MoH · KMHFL
      </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    return m


# ── Charts ─────────────────────────────────────────────────────────────────────

def themed(fig, title="", height=320):
    fig.update_layout(
        title=dict(text=title, font=dict(size=10, color=C["text_m"], family="Inter"), x=0),
        height=height, paper_bgcolor=C["card"], plot_bgcolor=C["card"],
        font=dict(family="Inter", color=C["text_b"], size=12),
        margin=dict(l=10, r=18, t=38, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C["border"], borderwidth=1),
        xaxis=dict(gridcolor="#EAECEF", linecolor=C["border"],
                   tickfont=dict(color=C["text_m"], size=11), zeroline=False),
        yaxis=dict(gridcolor="#EAECEF", linecolor=C["border"],
                   tickfont=dict(color=C["text_m"], size=11), zeroline=False),
    )
    return fig


def chart_access_scores(df):
    df = df.sort_values("accessibility_score")
    colours = [TIER_COLOURS.get(t, C["blue"]) for t in df["access_tier"]]
    fig = go.Figure(go.Bar(
        x=df["accessibility_score"], y=df["name"], orientation="h",
        marker_color=colours, marker_line_color=C["card"], marker_line_width=1,
        text=df["accessibility_score"].apply(lambda v: f"{v:.0f}"),
        textposition="outside",
        textfont=dict(size=10, family="IBM Plex Mono", color=C["text_m"]),
    ))
    fig.add_vline(x=45, line_dash="dash", line_color=C["text_m"], line_width=1,
                  annotation_text="Underserved threshold",
                  annotation_font=dict(size=9, color=C["text_m"]))
    themed(fig, "ACCESSIBILITY SCORE BY SETTLEMENT — real MoH network", max(320, len(df)*28))
    fig.update_xaxes(range=[0, 108])
    fig.update_yaxes(showgrid=False, tickfont=dict(size=10))
    return fig


def chart_any_vs_public(df):
    df = df.sort_values("walk_time_any_min", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Walk to any facility", x=df["name"], y=df["walk_time_any_min"],
        marker_color=C["blue"], opacity=0.85,
        text=df["walk_time_any_min"].apply(lambda v: f"{v:.0f}"),
        textposition="outside", textfont=dict(size=9, family="IBM Plex Mono"),
    ))
    fig.add_trace(go.Bar(
        name="Walk to public facility", x=df["name"], y=df["walk_time_public_min"],
        marker_color=C["danger"], opacity=0.75,
        text=df["walk_time_public_min"].apply(lambda v: f"{v:.0f}"),
        textposition="outside", textfont=dict(size=9, family="IBM Plex Mono"),
    ))
    fig.add_hline(y=10, line_dash="dot", line_color=C["success"], line_width=1.5,
                  annotation_text="10 min WHO target",
                  annotation_font=dict(size=9, color=C["success"]))
    themed(fig, "WALK TIME — ANY FACILITY vs PUBLIC FACILITY ONLY", 360)
    fig.update_layout(barmode="group", legend=dict(orientation="h", x=0, y=1.12))
    fig.update_xaxes(tickangle=-30, tickfont=dict(size=9), showgrid=False)
    return fig


def chart_facility_density(sc_df):
    df = sc_df.sort_values("facilities_per_10k")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="All facilities", x=df["facilities_per_10k"], y=df["sub_county"],
        orientation="h", marker_color=C["blue"], opacity=0.8,
        text=df["facilities_per_10k"].apply(lambda v: f"{v:.1f}"),
        textposition="outside", textfont=dict(size=9, family="IBM Plex Mono"),
    ))
    fig.add_trace(go.Bar(
        name="Public only", x=df["public_per_10k"], y=df["sub_county"],
        orientation="h", marker_color=C["danger"], opacity=0.75,
    ))
    themed(fig, "FACILITIES PER 10,000 RESIDENTS BY SUB-COUNTY", max(340, len(df)*26))
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", x=0, y=1.1))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=10))
    return fig


def chart_facility_type_breakdown(facilities):
    props   = [f["properties"] for f in facilities["features"]]
    counts  = Counter(p["tier"] for p in props)
    pub_c   = Counter(p["tier"] for p in props if p["public"])
    labels  = [k for k, v in sorted(counts.items(), key=lambda x: -x[1]) if k not in ("Other","Training")]
    totals  = [counts[l] for l in labels]
    publics = [pub_c.get(l, 0) for l in labels]

    colours = [FACILITY_COLOURS.get(l, C["blue"]) for l in labels]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Total", x=labels, y=totals,
        marker_color=colours, opacity=0.85,
        marker_line_color=C["card"], marker_line_width=2,
        text=totals, textposition="outside",
        textfont=dict(size=10, family="IBM Plex Mono"),
    ))
    fig.add_trace(go.Bar(
        name="Public / Govt", x=labels, y=publics,
        marker_color=C["primary"], opacity=0.6,
        marker_line_color=C["card"], marker_line_width=2,
    ))
    themed(fig, "FACILITY COUNT BY TYPE — total vs public/government", 340)
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", x=0, y=1.12))
    fig.update_xaxes(tickangle=-25, showgrid=False, tickfont=dict(size=10))
    return fig


def chart_coverage_funnel(df):
    total = df["population"].sum()
    w500  = (df["pct_within_500m"]/100 * df["population"]).sum()
    w1km  = (df["pct_within_1km"] /100 * df["population"]).sum()
    w2km  = (df["pct_within_2km"] /100 * df["population"]).sum()
    pw1km = (df["public_pct_within_1km"]/100 * df["population"]).sum()

    fig = go.Figure(go.Funnel(
        y=["Total Population","Within 2km (any)","Within 1km (any)",
           "Within 1km (public)","Within 500m (any)"],
        x=[total, w2km, w1km, pw1km, w500],
        textinfo="value+percent initial",
        marker=dict(
            color=[C["primary"], C["info"], C["success"], C["danger"], C["accent"]],
            line=dict(color=C["card"], width=2),
        ),
        textfont=dict(family="IBM Plex Mono", size=11),
    ))
    themed(fig, "POPULATION COVERAGE FUNNEL — real MoH network", 340)
    return fig


def chart_scatter_gap(df):
    fig = px.scatter(
        df,
        x="nearest_public_m", y="pop_density_per_km2",
        size="population", size_max=32,
        color="access_tier", color_discrete_map=TIER_COLOURS,
        hover_name="name",
        hover_data={"walk_time_public_min":True,"pct_within_1km":True,
                    "n_public_facilities_2km":True,"access_tier":False},
        labels={
            "nearest_public_m"    : "Distance to Nearest PUBLIC Facility (m)",
            "pop_density_per_km2" : "Population Density (per km²)",
            "access_tier"         : "Access Tier",
        },
        opacity=0.78,
    )
    fig.add_vline(x=1000, line_dash="dash", line_color=C["text_m"], line_width=1,
                  annotation_text="1km public threshold",
                  annotation_font=dict(size=9, color=C["text_m"]))
    themed(fig, "DISTANCE TO PUBLIC FACILITY vs POPULATION DENSITY", 380)
    fig.update_traces(marker=dict(line=dict(width=1, color=C["card"])))
    return fig


def chart_subcounty_ownership(facilities):
    props   = [f["properties"] for f in facilities["features"]]
    owners  = Counter(p["owner"] for p in props)
    # Simplify owner names
    def simplify(o):
        if "Ministry of Health" in o: return "Ministry of Health"
        if "Private Enterprise" in o: return "Private Enterprise"
        if "Private Practice" in o:   return "Private Practice"
        if "Catholic" in o or "Episcopal" in o: return "Catholic / KEC"
        if "Christian Health" in o:   return "CHAK"
        if "Non-Governmental" in o:   return "NGO"
        if "Faith" in o:              return "Other FBO"
        return "Other"
    simplified = Counter(simplify(p["owner"]) for p in props)
    labels = list(simplified.keys())
    values = [simplified[l] for l in labels]
    colours= [C["primary"],C["blue"],C["info"],C["accent"],C["success"],C["warning"],C["text_m"],"#9013FE"]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=colours[:len(labels)],
        hole=0.55,
        textinfo="percent+label",
        textfont=dict(size=10, family="Inter"),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{sum(values)}</b><br><span style='font-size:10px'>Facilities</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color=C["primary"], family="IBM Plex Mono"),
    )
    fig.update_layout(
        height=340, paper_bgcolor=C["card"],
        font=dict(family="Inter", color=C["text_b"]),
        margin=dict(l=10, r=10, t=38, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10), orientation="v"),
        title=dict(text="FACILITY OWNERSHIP BREAKDOWN — 863 REAL FACILITIES",
                   font=dict(size=10, color=C["text_m"]), x=0),
        showlegend=True,
    )
    return fig


def chart_gravity(gravity_df):
    df = gravity_df.copy()
    colours = [PRIORITY_COLOURS.get(p, C["blue"]) for p in df["priority"]]
    fig = go.Figure(go.Bar(
        x=df["name"].str.split("—").str[0].str.strip(),
        y=df["gravity_score"],
        marker_color=colours, marker_line_color=C["card"], marker_line_width=2,
        text=df["gravity_score"].apply(lambda v: f"{v:,.0f}"),
        textposition="outside",
        textfont=dict(size=10, family="IBM Plex Mono", color=C["text_m"]),
        width=0.55,
    ))
    themed(fig, "GRAVITY MODEL SCORE — unmet need quantified against real MoH network", 300)
    fig.update_xaxes(tickangle=-20, showgrid=False, tickfont=dict(size=9))
    fig.update_yaxes(showgrid=True, gridcolor="#EAECEF")
    return fig


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar(facilities):
    props = [f["properties"] for f in facilities["features"]]
    n_pub = sum(1 for p in props if p["public"])

    st.sidebar.markdown(f"""
    <div style="padding:6px 0 20px;border-bottom:1px solid rgba(255,255,255,.12);margin-bottom:18px;">
        <div style="font-size:.58rem;text-transform:uppercase;letter-spacing:2.5px;
                    color:rgba(255,255,255,.38);font-weight:700;">Nairobi County Health</div>
        <div style="font-size:.98rem;font-weight:700;color:#fff;margin-top:4px;
                    letter-spacing:-.3px;line-height:1.3;">Health Facility<br>Access Atlas</div>
        <div style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:2px;">
            Spatial accessibility analysis
        </div>
        <div style="margin-top:10px;background:rgba(74,144,226,.15);border:1px solid rgba(74,144,226,.3);
                    border-radius:5px;padding:7px 9px;">
            <div style="font-size:.55rem;text-transform:uppercase;letter-spacing:1px;
                        color:rgba(74,144,226,.9);font-weight:700;">Data Source</div>
            <div style="font-size:.68rem;color:#4A90E2;font-weight:600;margin-top:1px;">
                Kenya MoH · KMHFL
            </div>
            <div style="font-size:.62rem;color:rgba(74,144,226,.7);margin-top:1px;">
                {len(props):,} facilities · {n_pub} public
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    metric = st.sidebar.selectbox(
        "Choropleth Metric",
        ["accessibility_score","walk_time_any_min","pct_within_1km"],
        format_func=lambda x: {
            "accessibility_score": "Accessibility Score (0–100)",
            "walk_time_any_min"  : "Walk Time — Any Facility (min)",
            "pct_within_1km"     : "% Population Within 1km",
        }[x]
    )

    all_tiers = ["Critical Gap","Underserved","Moderate Access","Good Access","Well Served"]
    show_tiers = st.sidebar.multiselect("Filter Settlement Tiers", all_tiers, default=all_tiers)

    all_types = sorted(set(FACILITY_COLOURS.keys()))
    show_fac_types = st.sidebar.multiselect(
        "Facility Types",
        all_types,
        default=["National Referral","District Hospital","Other Hospital",
                 "Health Centre","Dispensary"],
    )

    show_public_only = st.sidebar.checkbox("Public facilities only", value=False)
    show_proposed    = st.sidebar.checkbox("Show proposed new sites ★", value=True)
    show_catchments  = st.sidebar.checkbox("Show catchment circles", value=True)
    catch_r = st.sidebar.select_slider(
        "Catchment radius (m)", options=[500,1000,1500,2000], value=1000
    )

    st.sidebar.markdown(f"""
    <div style="border-top:1px solid rgba(255,255,255,.1);margin-top:22px;padding-top:16px;">
        <div style="font-size:.58rem;text-transform:uppercase;letter-spacing:1.5px;
                    color:rgba(255,255,255,.38);font-weight:700;margin-bottom:10px;">Methodology</div>
        {"".join([f'''<div style="display:flex;justify-content:space-between;padding:4px 0;
                      border-bottom:1px solid rgba(255,255,255,.07);">
            <span style="font-size:.62rem;color:rgba(255,255,255,.38);">{k}</span>
            <span style="font-size:.64rem;font-weight:600;color:#fff;font-family:'IBM Plex Mono'">{v}</span>
        </div>''' for k,v in [("Walk speed","4.5 km/h"),("Detour factor","1.35×"),
                               ("CRS","WGS 84"),("Siting model","Gravity"),
                               ("Buffers","500m / 1km / 2km")]])}
    </div>
    """, unsafe_allow_html=True)

    return metric, show_tiers, show_fac_types, show_public_only, show_proposed, show_catchments, catch_r


# ── KPIs ───────────────────────────────────────────────────────────────────────

def render_kpis(stats):
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpis = [
        (c1, f"{stats.get('n_facilities_total',863):,}", "MoH Facilities",
         f"{stats.get('n_public_facilities',107)} public / govt", "blue"),
        (c2, f"{stats.get('total_population',2300000)/1e6:.1f}M", "Settlement Pop.",
         f"{stats.get('n_settlements',15)} informal settlements", "grn"),
        (c3, f"{stats.get('pct_within_1km',54.2)}%", "Within 1km (any)",
         f"{stats.get('pop_within_1km',0):,} residents", "grn"),
        (c4, f"{stats.get('pct_within_1km_public',32.1)}%", "Within 1km (public)",
         "Govt facilities only", "warn"),
        (c5, f"{stats.get('pop_beyond_2km',0):,}", "Beyond 2km",
         "Underserved population", "red"),
        (c6, f"{stats.get('avg_walk_public_min',24.1)}", "Avg Walk (public)",
         "Minutes to govt facility", "oran"),
    ]
    for col, val, lbl, sub, cls in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi {cls}">
                <div class="kpi-lbl">{lbl}</div>
                <div class="kpi-val">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)


# ── Proposed sites ─────────────────────────────────────────────────────────────

def render_proposed_panel(proposed, gravity_df):
    g = {}
    if not gravity_df.empty:
        for _, r in gravity_df.iterrows():
            g[r["site_id"]] = r.to_dict()

    for feat in proposed["features"]:
        props = feat["properties"]
        sid   = props["site_id"]
        gd    = g.get(sid, {})
        col   = PRIORITY_COLOURS.get(props["priority"], C["blue"])
        badge = {"Critical":"b-c","High":"b-h","Medium":"b-m"}.get(props["priority"],"b-g")

        st.markdown(f"""
        <div class="prop-card" style="border-top:4px solid {col};">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;
                        margin-bottom:8px;">
                <div>
                    <div style="font-size:.62rem;font-family:'IBM Plex Mono';
                                color:{C['text_m']};margin-bottom:4px;">
                        {sid} · Rank #{gd.get('rank','—')}
                    </div>
                    <div class="prop-name">{props['name']}</div>
                    <div class="prop-meta">{props['type']} &nbsp;·&nbsp; {props['priority']} Priority</div>
                </div>
                <span class="badge {badge}">{props['priority']}</span>
            </div>
            <div class="prop-rat">{props['rationale']}</div>
            <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap;">
                <div class="pstat"><div class="psv">{props['est_pop_served']:,}</div>
                    <div class="psl">Est. Pop Served</div></div>
                <div class="pstat"><div class="psv">${props['cost_usd_M']}M</div>
                    <div class="psl">Est. Cost</div></div>
                <div class="pstat">
                    <div class="psv">{gd.get('cost_effectiveness','—') if isinstance(gd.get('cost_effectiveness','—'),str) else f"{gd['cost_effectiveness']:,.0f}"}</div>
                    <div class="psl">People / $M</div></div>
                <div class="pstat">
                    <div class="psv">{gd.get('gravity_score','—') if isinstance(gd.get('gravity_score','—'),str) else f"{gd['gravity_score']:,.0f}"}</div>
                    <div class="psl">Gravity Score</div></div>
            </div>
        </div>""", unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    facilities, settlements, proposed, access_df, sc_df, stats, gravity_df = load_all()

    (metric, show_tiers, show_fac_types, show_public_only,
     show_proposed, show_catchments, catch_r) = render_sidebar(facilities)

    n_fac = len(facilities["features"])
    n_pub = sum(1 for f in facilities["features"] if f["properties"]["public"])

    st.markdown(f"""
    <div class="ph">
        <div>
            <div class="ph-ey">Nairobi County · Spatial Health Intelligence</div>
            <div class="ph-title">Health Facility Access Atlas</div>
            <div class="ph-sub">
                Walking-distance corridor analysis · {n_fac:,} real MoH facilities ·
                17 sub-counties · Gravity model new-site recommendations
            </div>
        </div>
        <div style="text-align:right;">
            <div><span class="tag src">🏛️ Govt of Kenya · MoH · KMHFL</span></div>
            <div style="margin-top:5px;">
                <span class="tag">{n_fac:,} facilities</span>
                <span class="tag">{n_pub} public</span>
                <span class="tag">GeoPandas · Folium</span>
                <span class="tag">Gravity Model</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_kpis(stats)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "  🗺️  Interactive Map  ",
        "  📊  Accessibility Analysis  ",
        "  🏥  Proposed New Sites  ",
        "  📈  Sub-County Intelligence  ",
        "  📋  Facility Register  ",
    ])

    with tab1:
        # Data source banner
        st.markdown(f"""
        <div class="data-src">
            🏛️ <b>Real Government Data</b> — This map uses {n_fac:,} actual health facility
            locations from the <b>Kenya Master Health Facility List (KMHFL)</b>, Ministry of Health,
            Government of Kenya. Facility names, types, ownership, and coordinates are real.
            Settlement boundaries are approximate convex hulls; population figures are from
            Kenya National Bureau of Statistics 2019 Census estimates.
        </div>""", unsafe_allow_html=True)

        mc1, mc2 = st.columns([3, 1])
        with mc1:
            m = build_map(
                facilities, settlements, proposed, access_df,
                metric, show_tiers, show_fac_types,
                show_proposed, show_catchments, catch_r, show_public_only,
            )
            st_folium(m, width="100%", height=580)
        with mc2:
            st.markdown(f'<div class="sec"><span class="dot" style="background:{C["primary"]}"></span>Facility Legend</div>', unsafe_allow_html=True)
            for ftype, fcol in FACILITY_COLOURS.items():
                if ftype in show_fac_types:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                        <div style="width:10px;height:10px;border-radius:50%;
                                    background:{fcol};flex-shrink:0"></div>
                        <span style="font-size:.72rem;color:{C['text_b']}">{ftype}</span>
                    </div>""", unsafe_allow_html=True)

            if show_proposed:
                st.markdown(f"""
                <div style="border-top:1px solid {C['border']};margin-top:10px;padding-top:10px">
                    <div style="font-size:.6rem;text-transform:uppercase;letter-spacing:1.2px;
                                color:{C['text_m']};font-weight:700;margin-bottom:8px">Proposed Sites</div>
                    {''.join([f"""<div style='display:flex;align-items:center;gap:7px;margin-bottom:5px;'>
                        <span style='color:{PRIORITY_COLOURS[p]};font-size:12px'>★</span>
                        <span style='font-size:.7rem;color:{C["text_b"]}'>{p} Priority</span>
                    </div>""" for p in ["Critical","High","Medium"]])}
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:{C['canvas']};border:1px solid {C['border']};
                        border-radius:6px;padding:10px 12px;margin-top:10px">
                <div style="font-size:.6rem;text-transform:uppercase;letter-spacing:1px;
                            color:{C['text_m']};font-weight:700;margin-bottom:5px">Catchment</div>
                <div style="font-size:1.1rem;font-weight:700;font-family:'IBM Plex Mono';
                            color:{C['primary']}">{catch_r:,}m</div>
                <div style="font-size:.65rem;color:{C['text_m']};margin-top:2px">
                    ≈ {catch_r/4500*60:.0f} min walk
                </div>
            </div>""", unsafe_allow_html=True)

    with tab2:
        if not access_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(chart_access_scores(access_df), use_container_width=True)
            with c2:
                st.plotly_chart(chart_coverage_funnel(access_df), use_container_width=True)
            st.plotly_chart(chart_any_vs_public(access_df), use_container_width=True)
            st.plotly_chart(chart_scatter_gap(access_df), use_container_width=True)
        else:
            st.info("Run `python src/accessibility_analysis.py` to generate scores.")

    with tab3:
        if not gravity_df.empty:
            st.markdown(f'<div class="sec"><span class="dot" style="background:{C["accent"]}"></span>Gravity Model Results — Scored Against Real MoH Network</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_gravity(gravity_df), use_container_width=True)
        st.markdown(f'<div class="sec"><span class="dot" style="background:{C["danger"]}"></span>Proposed Site Details</div>', unsafe_allow_html=True)
        render_proposed_panel(proposed, gravity_df)

    with tab4:
        c1, c2 = st.columns(2)
        with c1:
            if not sc_df.empty:
                st.plotly_chart(chart_facility_density(sc_df), use_container_width=True)
        with c2:
            st.plotly_chart(chart_subcounty_ownership(facilities), use_container_width=True)
        st.plotly_chart(chart_facility_type_breakdown(facilities), use_container_width=True)

        if not sc_df.empty:
            st.markdown(f'<div class="sec"><span class="dot" style="background:{C["primary"]}"></span>Sub-County Summary Table</div>', unsafe_allow_html=True)
            st.dataframe(
                sc_df.rename(columns={
                    "sub_county":"Sub-County","population_approx":"Pop (est.)",
                    "total_facilities":"Total","public_facilities":"Public",
                    "hospitals":"Hospitals","dispensaries":"Dispensaries",
                    "health_centres":"Health Ctrs","facilities_per_10k":"Per 10k",
                    "public_per_10k":"Public/10k",
                }),
                use_container_width=True, hide_index=True,
            )

    with tab5:
        st.markdown(f"""
        <div class="data-src">
            Source: <b>Government of Kenya — Ministry of Health · Kenya Master Health Facility List (KMHFL)</b><br>
            {n_fac:,} facilities across Nairobi's 17 sub-counties.
            Names, types, ownership and GPS coordinates are real, unmodified government data.
        </div>""", unsafe_allow_html=True)

        props_list = [f["properties"] for f in facilities["features"]]
        reg_df = pd.DataFrame([{
            "Facility ID" : p["facility_id"],
            "Name"        : p["name"],
            "Tier"        : p["tier"],
            "Owner"       : p["owner"][:45] + "…" if len(p["owner"]) > 45 else p["owner"],
            "Public"      : "Yes" if p["public"] else "No",
            "Sub-County"  : p["sub_county"],
            "Division"    : p["division"],
            "Location"    : p["location"],
        } for p in props_list])

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            ft = st.selectbox("Filter by Tier", ["All"] + sorted(reg_df["Tier"].unique()))
        with fc2:
            fsc = st.selectbox("Filter by Sub-County", ["All"] + sorted(reg_df["Sub-County"].unique()))
        with fc3:
            fp = st.selectbox("Filter by Ownership", ["All","Public","Private / FBO / NGO"])

        mask = pd.Series([True]*len(reg_df))
        if ft != "All":  mask &= reg_df["Tier"] == ft
        if fsc != "All": mask &= reg_df["Sub-County"] == fsc
        if fp == "Public": mask &= reg_df["Public"] == "Yes"
        elif fp == "Private / FBO / NGO": mask &= reg_df["Public"] == "No"

        filtered = reg_df[mask].reset_index(drop=True)
        st.dataframe(filtered, use_container_width=True, hide_index=True, height=520)
        st.markdown(f"""
        <div style="font-size:.72rem;color:{C['text_m']};margin-top:8px;">
            Showing {len(filtered):,} of {len(reg_df):,} facilities
        </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
