"""
Geocodes rows in places_enriched.csv that are missing lat/lon
using the OpenStreetMap Nominatim API (free, no key required).

Appends ", Melbourne, Australia" to each address for better accuracy.
Updates places_enriched.csv in-place.

Usage:
    python geocode_missing.py
"""

import os
import time
import urllib.parse
import urllib.request
import json
import pandas as pd

BASE = os.path.dirname(__file__)
CLEANED = os.path.join(BASE, "../cleaned")
CSV_PATH = os.path.join(CLEANED, "places_enriched.csv")

HEADERS = {"User-Agent": "FIT5120-ElderlyLoneliness/1.0 (student project)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q={}"


def geocode(address):
    """Return (lat, lon) for a plain-text address via Nominatim, or (None, None)."""
    query = urllib.parse.quote(f"{address}, Melbourne, Australia")
    url = NOMINATIM.format(query)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode())
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"  ERROR geocoding '{address}': {e}")
    return None, None


# ── Load & filter rows missing coordinates ────────────────────────────────────
df = pd.read_csv(CSV_PATH, encoding="utf-8")
missing = df[df["latitude"].isna() | df["longitude"].isna()].copy()
print(f"Geocoding {len(missing)} rows with missing coordinates...\n")

# ── Geocode each row ──────────────────────────────────────────────────────────
for idx, row in missing.iterrows():
    address = str(row["address"]).strip() if pd.notna(row["address"]) else ""
    if not address or address.lower() in ("nan", "none", ""):
        print(f"  SKIP (no address): {row['name']}")
        continue

    lat, lon = geocode(address)
    time.sleep(1.1)  # Nominatim enforces a 1 req/sec rate limit

    if lat and lon:
        df.at[idx, "latitude"] = lat
        df.at[idx, "longitude"] = lon
        print(f"  OK  {row['name'][:50]:<50} → {lat:.5f}, {lon:.5f}")
    else:
        print(f"  FAIL {row['name'][:50]}")

# ── Save ──────────────────────────────────────────────────────────────────────
df.to_csv(CSV_PATH, index=False, encoding="utf-8")

still_missing = (df["latitude"].isna() | df["longitude"].isna()).sum()
print(f"\nDone. Rows still missing coordinates: {still_missing}")
print(f"Saved → {CSV_PATH}")
