"""
Merges three raw datasets into a single unified places.csv for Epic 4.

Sources:
  - public-memorials-and-sculptures.csv      → category: Memorials & Sculptures
  - outdoor-artworks.csv                     → category: Artworks & Fountains
  - public-artworks-fountains-and-monuments.csv (supplement artworks)
  - landmarks-and-places-of-interest-*.csv   → category: Landmarks

Output: data/cleaned/places.csv
Schema: id, name, category, sub_category, address, latitude, longitude,
        artist, year, description, material
"""

import os
import re
import pandas as pd

BASE = os.path.dirname(__file__)
RAW = os.path.join(BASE, "../raw")
OUT = os.path.join(BASE, "../cleaned")
os.makedirs(OUT, exist_ok=True)


def split_coords(series):
    split = series.str.split(",", expand=True)
    lat = pd.to_numeric(split[0].str.strip(), errors="coerce")
    lon = pd.to_numeric(split[1].str.strip(), errors="coerce")
    return lat, lon


def strip_html(text):
    if pd.isna(text):
        return ""
    return re.sub(r"<[^>]+>", " ", str(text)).strip()


# ── 1. MEMORIALS & SCULPTURES ─────────────────────────────────────────────────
print("[1] Loading memorials & sculptures...")

mem = pd.read_csv(os.path.join(RAW, "public-memorials-and-sculptures.csv"), encoding="utf-8-sig")
mem["latitude"], mem["longitude"] = split_coords(mem["Co-ordinates"])
mem = mem.dropna(subset=["latitude", "longitude"])
mem = mem.rename(columns={"Title": "name", "Description": "sub_category"})
mem["category"] = "Memorials & Sculptures"
mem["address"] = ""
mem["artist"] = ""
mem["year"] = ""
mem["description"] = ""
mem["material"] = ""
mem = mem[["name", "category", "sub_category", "address", "latitude", "longitude",
           "artist", "year", "description", "material"]]

print(f"   {len(mem)} memorials loaded.")

# ── 2. ARTWORKS & FOUNTAINS ───────────────────────────────────────────────────
print("[2] Loading outdoor artworks (primary)...")

art1 = pd.read_csv(os.path.join(RAW, "outdoor-artworks.csv"), encoding="utf-8-sig")
# lat/lon columns are swapped in source — fix
art1 = art1.rename(columns={"latitude": "longitude", "longitude": "latitude"})
art1["latitude"] = pd.to_numeric(art1["latitude"], errors="coerce")
art1["longitude"] = pd.to_numeric(art1["longitude"], errors="coerce")
art1 = art1.dropna(subset=["latitude", "longitude"])
art1["name"] = art1["title"].str.strip()
art1["sub_category"] = art1["object_type"].str.strip()
art1["category"] = "Artworks & Fountains"
art1["address"] = art1["location"].fillna("").str.strip()
art1["artist"] = art1["makers"].fillna("").str.strip()
art1["year"] = art1["art_date"].fillna("").astype(str).str.strip()
art1["description"] = art1["description"].apply(strip_html)
art1["material"] = ""
art1 = art1[["name", "category", "sub_category", "address", "latitude", "longitude",
             "artist", "year", "description", "material"]]

print(f"   {len(art1)} outdoor artworks loaded.")

print("[2b] Loading public artworks & monuments (supplement)...")

art2 = pd.read_csv(os.path.join(RAW, "public-artworks-fountains-and-monuments.csv"), encoding="utf-8-sig")
art2["latitude"], art2["longitude"] = split_coords(art2["Co-ordinates"])
art2 = art2.dropna(subset=["latitude", "longitude"])
art2["name"] = art2["Name"].str.strip()
art2["sub_category"] = art2["Asset Type"].str.strip()
art2["category"] = "Artworks & Fountains"
art2["address"] = art2["Address Point"].fillna("").str.strip()
art2["artist"] = art2["Artist"].fillna("").str.strip()
art2["year"] = art2["Art Date"].fillna("").astype(str).str.strip()
art2["description"] = art2["Structure"].fillna("").str.strip()
art2["material"] = ""
art2 = art2[["name", "category", "sub_category", "address", "latitude", "longitude",
             "artist", "year", "description", "material"]]

# Deduplicate: drop art2 rows that are within ~50m of any art1 row
def round_coord(x, decimals=3):
    return round(float(x), decimals)

art1_keys = set(
    zip(art1["latitude"].apply(round_coord), art1["longitude"].apply(round_coord))
)
art2_mask = art2.apply(
    lambda r: (round_coord(r["latitude"]), round_coord(r["longitude"])) not in art1_keys,
    axis=1,
)
art2_new = art2[art2_mask]
print(f"   {len(art2_new)} additional artworks after deduplication.")

artworks = pd.concat([art1, art2_new], ignore_index=True)

# ── 3. LANDMARKS ──────────────────────────────────────────────────────────────
print("[3] Loading landmarks & places of interest...")

lm = pd.read_csv(
    os.path.join(RAW, "landmarks-and-places-of-interest-including-schools-theatres-health-services-spor.csv"),
    encoding="utf-8-sig",
)
lm["latitude"], lm["longitude"] = split_coords(lm["Co-ordinates"])
lm = lm.dropna(subset=["latitude", "longitude"])

# Keep only sub-themes relevant to curious outings for older adults
keep_sub = {
    "Art Gallery/Museum",
    "Library",
    "Theatre Live",
    "Cinema",
    "Function/Conference/Exhibition Centre",
    "Informal Outdoor Facility (Park/Garden/Reserve)",
    "Observation Tower/Wheel",
    "Outdoor Recreation Facility (Zoo, Golf Course)",
    "Visitor Centre",
    "Aquarium",
    "Bridge",
    "Cemetery",
}
lm = lm[lm["Sub Theme"].isin(keep_sub)]

lm["name"] = lm["Feature Name"].str.strip()
lm["category"] = "Landmarks"
lm["sub_category"] = lm["Sub Theme"].str.strip()
lm["address"] = ""
lm["artist"] = ""
lm["year"] = ""
lm["description"] = ""
lm["material"] = ""
lm = lm[["name", "category", "sub_category", "address", "latitude", "longitude",
         "artist", "year", "description", "material"]]

print(f"   {len(lm)} landmarks loaded.")

# ── 4. MERGE & ASSIGN IDs ─────────────────────────────────────────────────────
print("[4] Merging all sources...")

places = pd.concat([mem, artworks, lm], ignore_index=True)

# Drop rows with no name
places = places[places["name"].str.strip() != ""]
places = places.reset_index(drop=True)
places.insert(0, "id", range(1, len(places) + 1))

# Clean up year column — strip ".0" floats
places["year"] = places["year"].astype(str).str.replace(r"\.0$", "", regex=True)
places["year"] = places["year"].replace({"nan": "", "None": ""})

print(f"   Total: {len(places)} places ({len(mem)} memorials, {len(artworks)} artworks, {len(lm)} landmarks)")

out_path = os.path.join(OUT, "places.csv")
places.to_csv(out_path, index=False, encoding="utf-8")
print(f"\nSaved → {out_path}")
print(places["category"].value_counts().to_string())
