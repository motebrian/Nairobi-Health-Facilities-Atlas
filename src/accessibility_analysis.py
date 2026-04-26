"""
Nairobi Health Facility Access Atlas
======================================
Spatial Accessibility Analysis — Real MoH Data Edition

Uses 863 real Government of Kenya health facilities to compute:
  • Walking-distance accessibility per informal settlement
  • Public-only vs all-facility coverage comparison
  • Sub-county level facility density analysis
  • Population coverage at 500m / 1km / 2km thresholds
  • Gravity model scores for proposed new sites

Run:
    python src/accessibility_analysis.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

WALK_SPEED_KMH = 4.5
DETOUR_FACTOR  = 1.35   # informal settlement network correction factor


def haversine_m(lon1, lat1, lon2, lat2) -> float:
    R    = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a    = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def walk_time(dist_m: float) -> float:
    return (dist_m * DETOUR_FACTOR) / (WALK_SPEED_KMH * 1000 / 60)


def access_tier(score: float) -> str:
    if score < 25:   return "Critical Gap"
    elif score < 45: return "Underserved"
    elif score < 65: return "Moderate Access"
    elif score < 80: return "Good Access"
    else:            return "Well Served"


class AccessibilityAnalyser:

    def __init__(self):
        with open(DATA_DIR / "facilities_nairobi.geojson") as f:
            self.facilities = json.load(f)
        with open(DATA_DIR / "settlements.geojson") as f:
            self.settlements = json.load(f)
        with open(DATA_DIR / "proposed_sites.geojson") as f:
            self.proposed = json.load(f)
        self.pop_grid = pd.read_csv(DATA_DIR / "population_grid.csv")

        self._all_coords  = [f["geometry"]["coordinates"]
                             for f in self.facilities["features"]]
        self._pub_coords  = [f["geometry"]["coordinates"]
                             for f in self.facilities["features"]
                             if f["properties"]["public"]]
        self._hosp_coords = [f["geometry"]["coordinates"]
                             for f in self.facilities["features"]
                             if f["properties"]["tier"] in
                             ("National Referral","District Hospital","Other Hospital")]

        print(f"  Loaded {len(self._all_coords)} total facilities")
        print(f"  → {len(self._pub_coords)} public / government")
        print(f"  → {len(self._hosp_coords)} hospitals")

    def _nearest(self, lon, lat, coords) -> float:
        return min(haversine_m(lon, lat, c[0], c[1]) for c in coords)

    def _coverage_pct(self, clon, clat, area_km2, nearest_m, threshold_m) -> float:
        radius_km = math.sqrt(area_km2 / math.pi)
        raw = min(1.0, (threshold_m/1000 / radius_km)**1.5) * (
              threshold_m / max(nearest_m, 50))
        return round(min(100.0, raw * 100), 1)

    def compute_settlement_scores(self) -> pd.DataFrame:
        rows = []
        for feat in self.settlements["features"]:
            props = feat["properties"]
            ring  = feat["geometry"]["coordinates"][0]
            clon  = float(np.mean([p[0] for p in ring]))
            clat  = float(np.mean([p[1] for p in ring]))
            pop   = props["population"]
            area  = props["area_km2"]

            near_all  = self._nearest(clon, clat, self._all_coords)
            near_pub  = self._nearest(clon, clat, self._pub_coords)
            near_hosp = self._nearest(clon, clat, self._hosp_coords)
            wt        = walk_time(near_all)
            wt_pub    = walk_time(near_pub)

            p500  = self._coverage_pct(clon, clat, area, near_all, 500)
            p1km  = self._coverage_pct(clon, clat, area, near_all, 1000)
            p2km  = self._coverage_pct(clon, clat, area, near_all, 2000)
            pp500 = self._coverage_pct(clon, clat, area, near_pub, 500)
            pp1km = self._coverage_pct(clon, clat, area, near_pub, 1000)

            n_500m    = sum(1 for c in self._all_coords
                            if haversine_m(clon, clat, c[0], c[1]) <= 500)
            n_1km     = sum(1 for c in self._all_coords
                            if haversine_m(clon, clat, c[0], c[1]) <= 1000)
            n_pub_2km = sum(1 for c in self._pub_coords
                            if haversine_m(clon, clat, c[0], c[1]) <= 2000)

            dist_score = max(0, 100 - (near_all / 2500 * 60))
            pub_score  = max(0, 100 - (near_pub  / 2500 * 60))
            hosp_score = max(0, 100 - (near_hosp / 5000 * 60))
            cov_score  = p1km
            score = round(0.35*dist_score + 0.25*cov_score + 0.25*pub_score + 0.15*hosp_score, 1)

            rows.append({
                "settlement_id"          : props["settlement_id"],
                "name"                   : props["name"],
                "sub_county"             : props["sub_county"],
                "population"             : pop,
                "area_km2"               : area,
                "pop_density_per_km2"    : round(pop / area),
                "nearest_any_m"          : round(near_all),
                "nearest_public_m"       : round(near_pub),
                "nearest_hospital_m"     : round(near_hosp),
                "walk_time_any_min"      : round(wt, 1),
                "walk_time_public_min"   : round(wt_pub, 1),
                "n_facilities_500m"      : n_500m,
                "n_facilities_1km"       : n_1km,
                "n_public_facilities_2km": n_pub_2km,
                "pct_within_500m"        : p500,
                "pct_within_1km"         : p1km,
                "pct_within_2km"         : p2km,
                "public_pct_within_500m" : pp500,
                "public_pct_within_1km"  : pp1km,
                "pop_beyond_2km"         : int(pop * (1 - p2km/100)),
                "accessibility_score"    : score,
                "access_tier"            : access_tier(score),
                "u5_mortality_per1k"     : props["u5_mortality_per1k"],
                "malaria_prev_pct"       : props["malaria_prev_pct"],
                "hiv_prev_pct"           : props["hiv_prev_pct"],
                "water_access_pct"       : props["water_access_pct"],
                "sanitation_pct"         : props["sanitation_pct"],
            })

        return pd.DataFrame(rows).sort_values("accessibility_score").reset_index(drop=True)

    def compute_subcounty_summary(self) -> pd.DataFrame:
        fac_props = [f["properties"] for f in self.facilities["features"]]
        sc       = Counter(p["sub_county"] for p in fac_props)
        sc_pub   = Counter(p["sub_county"] for p in fac_props if p["public"])
        sc_hosp  = Counter(p["sub_county"] for p in fac_props
                           if p["tier"] in ("National Referral","District Hospital","Other Hospital"))
        sc_disp  = Counter(p["sub_county"] for p in fac_props if p["tier"] == "Dispensary")
        sc_hc    = Counter(p["sub_county"] for p in fac_props if p["tier"] == "Health Centre")

        SC_POP = {
            "Starehe":180000,"Kibra":260000,"Roysambu":195000,
            "Dagoretti North":210000,"Westlands":185000,"Kamukunji":175000,
            "Langata":228000,"Makadara":168000,"Kasarani":322000,
            "Embakasi Central":192000,"Ruaraka":231000,"Embakasi West":197000,
            "Dagoretti South":158000,"Embakasi South":249000,
            "Embakasi East":213000,"Embakasi North":187000,"Mathare":148000,
        }

        rows = []
        for sc_name in sorted(sc.keys()):
            pop = SC_POP.get(sc_name, 150000)
            tot = sc[sc_name]
            rows.append({
                "sub_county"          : sc_name,
                "population_approx"   : pop,
                "total_facilities"    : tot,
                "public_facilities"   : sc_pub.get(sc_name, 0),
                "hospitals"           : sc_hosp.get(sc_name, 0),
                "dispensaries"        : sc_disp.get(sc_name, 0),
                "health_centres"      : sc_hc.get(sc_name, 0),
                "facilities_per_10k"  : round(tot / pop * 10000, 1),
                "public_per_10k"      : round(sc_pub.get(sc_name, 0) / pop * 10000, 1),
            })

        return pd.DataFrame(rows).sort_values("facilities_per_10k").reset_index(drop=True)

    def compute_coverage_stats(self, scores_df: pd.DataFrame) -> dict:
        pop   = scores_df["population"].sum()
        w1km  = (scores_df["pct_within_1km"]/100 * scores_df["population"]).sum()
        w2km  = (scores_df["pct_within_2km"]/100 * scores_df["population"]).sum()
        pw1km = (scores_df["public_pct_within_1km"]/100 * scores_df["population"]).sum()
        fprops = [f["properties"] for f in self.facilities["features"]]

        return {
            "total_population"        : int(pop),
            "n_settlements"           : len(scores_df),
            "n_facilities_total"      : len(fprops),
            "n_public_facilities"     : len(self._pub_coords),
            "n_hospitals"             : len(self._hosp_coords),
            "n_dispensaries"          : sum(1 for p in fprops if p["tier"]=="Dispensary"),
            "n_health_centres"        : sum(1 for p in fprops if p["tier"]=="Health Centre"),
            "n_medical_clinics"       : sum(1 for p in fprops if p["tier"]=="Medical Clinic"),
            "pop_within_1km"          : int(w1km),
            "pop_within_2km"          : int(w2km),
            "pop_within_1km_public"   : int(pw1km),
            "pop_beyond_2km"          : int(scores_df["pop_beyond_2km"].sum()),
            "pct_within_1km"          : round(w1km/pop*100, 1),
            "pct_within_2km"          : round(w2km/pop*100, 1),
            "pct_within_1km_public"   : round(pw1km/pop*100, 1),
            "avg_walk_time_min"       : round(scores_df["walk_time_any_min"].mean(), 1),
            "avg_walk_public_min"     : round(scores_df["walk_time_public_min"].mean(), 1),
            "median_walk_time_min"    : round(scores_df["walk_time_any_min"].median(), 1),
            "avg_accessibility_score" : round(scores_df["accessibility_score"].mean(), 1),
            "critical_gap_settlements": int((scores_df["access_tier"]=="Critical Gap").sum()),
            "underserved_settlements" : int((scores_df["access_tier"]=="Underserved").sum()),
            "data_source"             : "Government of Kenya — Ministry of Health (KMHFL)",
            "n_sub_counties"          : int(scores_df["sub_county"].nunique()),
        }

    def gravity_model(self, scores_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for feat in self.proposed["features"]:
            props = feat["properties"]
            plon  = feat["geometry"]["coordinates"][0]
            plat  = feat["geometry"]["coordinates"][1]

            gravity = 0.0
            for _, row in self.pop_grid.iterrows():
                d = haversine_m(plon, plat, row["lon"], row["lat"])
                if d < 10: d = 10
                nearest_existing = min(
                    haversine_m(row["lon"], row["lat"], c[0], c[1])
                    for c in self._all_coords
                )
                if nearest_existing < d:
                    continue
                gravity += row["population"] / (d/1000)**2

            rows.append({
                "site_id"           : props["site_id"],
                "name"              : props["name"],
                "priority"          : props["priority"],
                "type"              : props["type"],
                "est_pop_served"    : props["est_pop_served"],
                "cost_usd_M"        : props["cost_usd_M"],
                "rationale"         : props["rationale"],
                "gravity_score"     : round(gravity),
                "cost_effectiveness": round(props["est_pop_served"] / props["cost_usd_M"]),
            })

        df = pd.DataFrame(rows).sort_values("gravity_score", ascending=False).reset_index(drop=True)
        df["rank"] = range(1, len(df)+1)
        return df


def run():
    print("="*58)
    print("  Nairobi Health Atlas — Accessibility Analysis")
    print("  Source: Government of Kenya MoH Facility Registry")
    print("="*58)

    analyser = AccessibilityAnalyser()

    print("\n[1/4] Computing settlement accessibility scores...")
    scores = analyser.compute_settlement_scores()
    scores.to_csv(DATA_DIR / "accessibility_scores.csv", index=False)
    print(scores[["name","nearest_any_m","nearest_public_m",
                  "walk_time_any_min","n_facilities_1km",
                  "accessibility_score","access_tier"]].to_string(index=False))

    print("\n[2/4] Computing sub-county facility density...")
    sc_df = analyser.compute_subcounty_summary()
    sc_df.to_csv(DATA_DIR / "subcounty_summary.csv", index=False)
    print(sc_df[["sub_county","total_facilities","public_facilities",
                 "facilities_per_10k","public_per_10k"]].to_string(index=False))

    print("\n[3/4] Computing aggregate coverage statistics...")
    stats = analyser.compute_coverage_stats(scores)
    with open(DATA_DIR / "coverage_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n[4/4] Running gravity model for proposed sites...")
    gravity = analyser.gravity_model(scores)
    gravity.to_csv(DATA_DIR / "proposed_site_scores.csv", index=False)
    print(gravity[["rank","name","priority","gravity_score","cost_effectiveness"]].to_string(index=False))

    print("\n✓ Analysis complete — run: streamlit run streamlit_app/app.py")
    return scores, stats, gravity


if __name__ == "__main__":
    run()
