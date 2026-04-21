"""
Data cleaning and preprocessing pipeline for the Echo elderly loneliness app.
Outputs cleaned CSVs to data/cleaned/.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "py_packages"))

import pandas as pd
import numpy as np

BASE = os.path.dirname(__file__)
OUT = os.path.join(BASE, "cleaned")
os.makedirs(OUT, exist_ok=True)


def save(df, name):
    path = os.path.join(OUT, name)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"  Saved {name}: {len(df)} rows, {len(df.columns)} cols")


def split_coords(series, lat_col="latitude", lon_col="longitude"):
    """Split 'lat, lon' string column into two float columns."""
    split = series.str.split(",", expand=True)
    lat = pd.to_numeric(split[0].str.strip(), errors="coerce")
    lon = pd.to_numeric(split[1].str.strip(), errors="coerce")
    return lat, lon


# ─────────────────────────────────────────────
# 1. CAFES & RESTAURANTS
# ─────────────────────────────────────────────
print("\n[1] Cleaning cafes & restaurants...")

df = pd.read_csv(
    os.path.join(BASE, "cafes-and-restaurants-with-seating-capacity.csv"),
    encoding="utf-8-sig",
)

# Keep only social/hospitality venue types relevant to elderly social outings
social_industries = [
    "Cafes and Restaurants",
    "Pubs, Taverns and Bars",
    "Clubs (Hospitality)",
    "Catering Services",
    "Health and Fitness Centres and Gymnasia Operation",
    "Sports and Physical Recreation Venues, Grounds and Facilities Operation",
    "Sports and Physical Recreation Clubs and Sports Professionals",
    "Zoological and Botanical Gardens Operation",
    "Museum Operation",
    "Performing Arts Operation",
    "Performing Arts Venue Operation",
]
df = df[df["Industry (ANZSIC4) description"].isin(social_industries)]

# Keep only the most recent census year per business+address+seating combination
df = df.sort_values("Census year", ascending=False)
df = df.drop_duplicates(
    subset=["Trading name", "Business address", "Seating type"], keep="first"
)

# Drop rows missing coordinates
df = df.dropna(subset=["Latitude", "Longitude"])

# Select and rename useful columns
df = df[
    [
        "Trading name",
        "Business address",
        "CLUE small area",
        "Industry (ANZSIC4) description",
        "Seating type",
        "Number of seats",
        "Latitude",
        "Longitude",
        "Census year",
    ]
].rename(
    columns={
        "Trading name": "name",
        "Business address": "address",
        "CLUE small area": "suburb",
        "Industry (ANZSIC4) description": "category",
        "Seating type": "seating_type",
        "Number of seats": "seats",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Census year": "census_year",
    }
)

# Normalise seating_type to indoor / outdoor
df["seating_type"] = (
    df["seating_type"]
    .str.replace("Seats - ", "", regex=False)
    .str.lower()
)

df["name"] = df["name"].str.strip().str.title()
df["address"] = df["address"].str.strip()

save(df, "cafes.csv")

# ─────────────────────────────────────────────
# 2. HEALTH SERVICES
# ─────────────────────────────────────────────
print("\n[2] Cleaning health services...")

df = pd.read_csv(
    os.path.join(BASE, "healthdirect_nhsd_services_directory_2025(vic).csv"),
    encoding="utf-8-sig",
    low_memory=False,
)

# Drop all state-specific holiday availability columns — mostly null for VIC
availability_cols = [c for c in df.columns if c.startswith("availability_")]
df = df.drop(columns=availability_cols + ["the_geom", "FID", "organization_id",
                                           "parent_organization_id"])

# Drop rows missing coordinates or organisation name
df = df.dropna(subset=["latitude", "longitude", "organization"])

# Filter to VIC only (dataset label says VIC but double-check)
df = df[df["state"] == "VIC"]

# Drop country column (all AUS)
df = df.drop(columns=["country"])

# Standardise open hours: replace empty strings with NaN
hour_cols = [c for c in df.columns if "open_hours" in c]
for col in hour_cols:
    df[col] = df[col].replace("", np.nan)

# Rename for clarity
df = df.rename(
    columns={
        "nhsd_service_id": "service_id",
        "organization": "name",
        "parent_organization_name": "parent_org",
    }
)

df["name"] = df["name"].str.strip()
df["city"] = df["city"].str.strip().str.title()
df["address"] = df["address"].str.strip()

save(df, "health_services.csv")

# ─────────────────────────────────────────────
# 3. OUTDOOR ARTWORKS
# ─────────────────────────────────────────────
print("\n[3] Cleaning outdoor artworks...")

df = pd.read_csv(
    os.path.join(BASE, "outdoor-artworks.csv"), encoding="utf-8-sig"
)

# Drop redundant/mostly-null columns
df = df.drop(
    columns=["Geo Shape", "road_segment", "history", "inscription",
             "service_manager", "company", "asset_id"]
)

# Latitude and longitude already separated
df = df.rename(
    columns={
        "title": "name",
        "description": "description",
        "object_type": "type",
        "art_date": "year",
        "makers": "artist",
        "classification": "classification",
        "location": "address",
        "property": "park_name",
        "owner_type": "owner",
        # Source CSV has lat/lon column names swapped — fix here
        "latitude": "longitude",
        "longitude": "latitude",
    }
)

# Drop the redundant "Geo Point" string column
df = df.drop(columns=["Geo Point"], errors="ignore")

df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"])

df["name"] = df["name"].str.strip()
df["description"] = df["description"].str.strip()

save(df, "outdoor_artworks.csv")

# ─────────────────────────────────────────────
# 4. PUBLIC ARTWORKS, FOUNTAINS & MONUMENTS
# ─────────────────────────────────────────────
print("\n[4] Cleaning public artworks & monuments...")

df = pd.read_csv(
    os.path.join(BASE, "public-artworks-fountains-and-monuments.csv"),
    encoding="utf-8-sig",
)

# Split "Co-ordinates" column ("-37.xx, 144.xx") into lat/lon
df["latitude"], df["longitude"] = split_coords(df["Co-ordinates"])
df = df.dropna(subset=["latitude", "longitude"])

# Drop redundant projected coordinate columns and unused metadata
df = df.drop(
    columns=["Co-ordinates", "Easting", "Northing", "Xorg", "Xsource",
             "Mel way Ref", "Alternate Name", "Respective Author"]
)

df = df.rename(
    columns={
        "Asset Type": "type",
        "Name": "name",
        "Address Point": "address",
        "Artist": "artist",
        "Art Date": "year",
        "Structure": "description",
    }
)

df["name"] = df["name"].str.strip()

save(df, "public_artworks.csv")

# ─────────────────────────────────────────────
# 5. PUBLIC MEMORIALS & SCULPTURES
# ─────────────────────────────────────────────
print("\n[5] Cleaning public memorials & sculptures...")

df = pd.read_csv(
    os.path.join(BASE, "public-memorials-and-sculptures.csv"),
    encoding="utf-8-sig",
)

df["latitude"], df["longitude"] = split_coords(df["Co-ordinates"])
df = df.dropna(subset=["latitude", "longitude"])
df = df.drop(columns=["Co-ordinates"])

df = df.rename(
    columns={
        "Title": "name",
        "Description": "type",
    }
)

df["name"] = df["name"].str.strip()
df["type"] = df["type"].str.strip()

save(df, "memorials.csv")

# ─────────────────────────────────────────────
# 6. PUBLIC TOILETS
# ─────────────────────────────────────────────
print("\n[6] Cleaning public toilets...")

df = pd.read_csv(os.path.join(BASE, "public-toilets.csv"), encoding="utf-8-sig")

# Drop redundant location string (lat/lon already present)
df = df.drop(columns=["location"])

# Fill missing access flags with 'unknown'
for col in ["female", "male", "wheelchair", "baby_facil"]:
    df[col] = df[col].fillna("unknown")

# Rename for clarity
df = df.rename(
    columns={
        "name": "name",
        "female": "female_access",
        "male": "male_access",
        "wheelchair": "wheelchair_access",
        "baby_facil": "baby_facilities",
        "operator": "operator",
        "lat": "latitude",
        "lon": "longitude",
    }
)

df["name"] = df["name"].str.strip()

save(df, "toilets.csv")

# ─────────────────────────────────────────────
# 7. STREET FURNITURE (benches, fountains, picnic)
# ─────────────────────────────────────────────
print("\n[7] Cleaning street furniture...")

df = pd.read_csv(
    os.path.join(
        BASE,
        "street-furniture-including-bollards-bicycle-rails-bins-drinking-fountains-horse-.csv",
    ),
    encoding="utf-8-sig",
)

# Keep only items useful for elderly outdoor comfort
keep_types = ["Seat", "Drinking Fountain", "Picnic Setting", "Barbeque", "Horse Trough"]
df = df[df["ASSET_TYPE"].isin(keep_types)]

# Split coordinate string into lat/lon
df["latitude"], df["longitude"] = split_coords(df["CoordinateLocation"])
df = df.dropna(subset=["latitude", "longitude"])

# Drop projected coords and admin-only columns
df = df.drop(
    columns=["EASTING", "NORTHING", "CoordinateLocation", "GIS_ID",
             "MODEL_NO", "DIVISION", "COMPANY", "UploadDate",
             "EVALUATION_DATE", "ASSET_CLASS"]
)

df = df.rename(
    columns={
        "DESCRIPTION": "description",
        "ASSET_TYPE": "type",
        "MODEL_DESCR": "model",
        "LOCATION_DESC": "location",
        "CONDITION_RATING": "condition",
    }
)

df["description"] = df["description"].str.strip()
df["location"] = df["location"].str.strip()

save(df, "street_furniture.csv")

# ─────────────────────────────────────────────
# 8. PEDESTRIAN COUNTS — aggregate to hourly averages per sensor
# ─────────────────────────────────────────────
print("\n[8] Aggregating pedestrian counts...")

df = pd.read_csv(
    os.path.join(BASE, "pedestrian-counting-system-monthly-counts-per-hour.csv"),
    encoding="utf-8-sig",
)

# Parse coordinates from Location string "-37.xx, 144.xx"
df["latitude"], df["longitude"] = split_coords(df["Location"])

# Aggregate: average pedestrian count per sensor per hour of day
hourly_avg = (
    df.groupby(["Sensor_Name", "HourDay", "latitude", "longitude"])["Total_of_Directions"]
    .mean()
    .round(1)
    .reset_index()
)

hourly_avg = hourly_avg.rename(
    columns={
        "Sensor_Name": "sensor_name",
        "HourDay": "hour",
        "Total_of_Directions": "avg_pedestrians",
    }
)

# Also produce a simpler summary: overall daily average per sensor
daily_avg = (
    df.groupby(["Sensor_Name", "latitude", "longitude"])["Total_of_Directions"]
    .mean()
    .round(1)
    .reset_index()
    .rename(
        columns={
            "Sensor_Name": "sensor_name",
            "Total_of_Directions": "avg_daily_pedestrians",
        }
    )
)

save(hourly_avg, "pedestrian_hourly.csv")
save(daily_avg, "pedestrian_summary.csv")

print("\nDone! All cleaned files written to data/cleaned/")
