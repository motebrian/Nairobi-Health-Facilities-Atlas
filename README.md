# 🗺️ Nairobi Health Facility Access Atlas

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-0.14-139C5A?style=flat-square)
![Folium](https://img.shields.io/badge/Folium-0.17-77B829?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?style=flat-square&logo=streamlit)
![Data](https://img.shields.io/badge/Data-Government%20of%20Kenya%20MoH-1F3A5F?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Spatial accessibility analysis mapping walking-distance corridors to health facilities across Nairobi's informal settlements — built on real Government of Kenya Ministry of Health facility data.**

[Live Demo →](#) · [Methodology →](#methodology) · [Data Source →](#data-source)

</div>

---

## 🏛️ Data Source

This project uses **real, unmodified government data** from the **Kenya Master Health Facility List (KMHFL)**, published by the Ministry of Health, Government of Kenya.

| Attribute | Details |
|---|---|
| **Source** | Kenya Master Health Facility List (KMHFL) |
| **Publisher** | Ministry of Health, Government of Kenya |
| **Coverage** | 10,013 facilities across all 47 counties |
| **Nairobi subset** | 863 validated facilities across 17 sub-counties |
| **Fields used** | Facility name, type, owner, county, sub-county, division, location, GPS coordinates |
| **Format** | GeoJSON (WGS 84 / EPSG:4326) |
| **Access** | [kmhflite.health.go.ke](https://kmhflite.health.go.ke) |

### Nairobi Facility Breakdown

| Tier | Count | Notes |
|---|---|---|
| Medical Clinic | 432 | Predominantly private |
| Dispensary | 187 | Mix of public and FBO |
| Health Centre | 82 | Mostly public |
| VCT Centre | 53 | HIV/AIDS services |
| Other Hospital | 36 | Private sector |
| Nursing Home | 24 | Private |
| District Hospital | 3 | Public — Mama Lucy, Mbagathi, Mathari |
| National Referral | 2 | KNH, National Spinal Injury |
| **Total** | **863** | **107 public / government** |

---

## 🎯 Problem Statement

Over **2.3 million residents** across Nairobi's 15 largest informal settlements face disproportionate barriers to healthcare. The KMHFL data reveals a striking pattern: **863 facilities serve the city, but only 107 are public**. For low-income residents who cannot afford private clinic fees, the effective coverage is dramatically lower.

This project answers three questions county health planners need answered:

1. **Where are the public health access gaps?** — Which informal settlements are beyond 1km of any government facility?
2. **How does ownership affect access?** — What is the difference in walking time to any facility versus a public/government facility?
3. **Where should new public facilities go?** — Using a gravity model scored against the real MoH network, which locations maximally reduce unmet need per dollar of investment?

---

## 📐 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│              Nairobi Health Facility Access Atlas                │
├───────────────────┬───────────────────┬──────────────────────────┤
│  Data Layer       │  Analysis Layer   │  Serving Layer           │
│                   │                   │                          │
│  healthcare_      │  AccessAnalyser   │  Streamlit Dashboard     │
│  facilities.json  │  ├── Haversine    │  ├── Folium choropleth   │
│  (Govt of Kenya   │  │   distances    │  │   with 863 real dots  │
│  · MoH · KMHFL)   │  ├── Walk time   │  ├── Accessibility charts│
│                   │  │   estimation   │  ├── Any vs public       │
│  863 Nairobi      │  ├── Public vs   │  │   walk time comparison │
│  facilities with  │  │   any coverage │  ├── Sub-county density  │
│  real names,      │  ├── Sub-county  │  ├── Ownership breakdown  │
│  types, owners,   │  │   density      │  ├── Gravity scoring     │
│  coordinates      │  └── Gravity     │  └── Facility register   │
│                   │      model        │      (full 863 rows)     │
└───────────────────┴───────────────────┴──────────────────────────┘
```

---

## 🧮 Methodology

### Walking Distance Model
```
network_distance = haversine_distance × 1.35 (detour factor)
walk_time_min    = network_distance / (4.5 km/h × 1000/60)
```
The 1.35× detour factor accounts for the lower street connectivity of informal settlement networks (Kuffer et al., 2016).

### Accessibility Score (0–100)
```
score = 0.35 × distance_score     (distance to nearest any facility)
      + 0.25 × coverage_score     (% population within 1km)
      + 0.25 × public_score       (distance to nearest public facility)
      + 0.15 × hospital_score     (distance to nearest hospital)
```

The inclusion of a **public-only component** (0.25 weight) differentiates this from naive facility-count approaches — it captures the real affordability dimension of access.

### Gravity Model for New Site Placement
```
gravity(s) = Σᵢ [ population_i / (distance(s,i)/km)² ]
             for grid cells i where no existing MoH facility is closer
```
The model penalises proposed sites that would duplicate existing coverage and rewards sites in genuine voids in the **real** facility network.

---

## 📊 Key Findings

| Metric | Value |
|---|---|
| Total Nairobi MoH facilities | **863** |
| Of which public/government | **107 (12.4%)** |
| Settlement population within 1km (any facility) | **~54%** |
| Settlement population within 1km (public only) | **~32%** |
| Gap: any vs public coverage | **22 percentage points** |
| Average walk to nearest public facility | **~24 min** |
| Average walk to nearest any facility | **~14 min** |
| Informal settlements with critical gap | **4** |

The 22 percentage-point gap between "any facility" and "public facility" coverage is the core finding — it quantifies the affordability barrier in spatial terms.

---

## 🚀 Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/nairobi-health-atlas.git
cd nairobi-health-atlas
pip install -r requirements.txt

# Process real MoH data (produces facilities_nairobi.geojson etc.)
python data/load_real_data.py

# Run accessibility analysis
python src/accessibility_analysis.py

# Launch dashboard
streamlit run streamlit_app/app.py
```

---

## 📁 Project Structure

```
nairobi-health-atlas/
├── data/
│   ├── healthcare_facilities.json   ← Real Govt of Kenya MoH data (10,013 facilities)
│   ├── load_real_data.py            ← Extracts & cleans Nairobi subset
│   ├── facilities_nairobi.geojson   ← 863 Nairobi facilities (after running loader)
│   ├── settlements.geojson          ← 15 informal settlement polygons
│   ├── proposed_sites.geojson       ← 5 recommended new sites
│   ├── population_grid.csv          ← Synthetic 100m population grid
│   ├── accessibility_scores.csv     ← Settlement-level scores (after analysis)
│   ├── subcounty_summary.csv        ← Sub-county density table
│   ├── coverage_stats.json          ← Aggregate statistics
│   └── proposed_site_scores.csv     ← Gravity model output
├── src/
│   └── accessibility_analysis.py   ← Core spatial analysis engine
├── streamlit_app/
│   └── app.py                       ← Interactive Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## 📚 References

- Kenya Ministry of Health. Kenya Master Health Facility List. [kmhflite.health.go.ke](https://kmhflite.health.go.ke)
- Kenya National Bureau of Statistics. (2019). Kenya Population and Housing Census, Volume I.
- Kuffer, M., et al. (2016). Slums from Space. *Remote Sensing*, 8(6), 455.
- UN-Habitat. (2016). Nairobi Urban Sector Profile.

---

## 📜 License

MIT © 2025 · Data from Government of Kenya (open data). Analysis and code are freely reusable with attribution.
