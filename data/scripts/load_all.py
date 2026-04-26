"""
Load all cleaned datasets into PostgreSQL RDS.
Tables already handled separately: public_benches, public_toilets, pedestrian_data, sensor_locations
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../py_packages"))

import psycopg2
import pandas as pd

BASE = os.path.dirname(__file__)
CLEANED = os.path.join(BASE, "../cleaned")

DB = dict(
    host="elderly-loneliness-database.c58eaa0yqnag.ap-southeast-2.rds.amazonaws.com",
    port=5432, dbname="postgres", user="postgres", password="fit5120te28"
)

conn = psycopg2.connect(**DB)
cur = conn.cursor()


def load(table, df, create_sql, insert_sql, row_fn):
    cur.execute(create_sql)
    cur.execute(f"TRUNCATE {table} RESTART IDENTITY;")
    rows = [row_fn(r) for _, r in df.iterrows()]
    cur.executemany(insert_sql, rows)
    conn.commit()
    cur.execute(f"SELECT COUNT(*) FROM {table};")
    print(f"  {table}: {cur.fetchone()[0]:,} rows loaded")


def val(v):
    """Convert NaN to None for SQL."""
    return None if pd.isna(v) else v


# ─────────────────────────────────────────────
# 1. CAFES
# ─────────────────────────────────────────────
print("\n[1] Loading cafes...")
df = pd.read_csv(os.path.join(CLEANED, "cafes.csv"))

load(
    "cafes", df,
    """
    CREATE TABLE IF NOT EXISTS cafes (
        id          SERIAL PRIMARY KEY,
        name        TEXT,
        address     TEXT,
        suburb      VARCHAR(100),
        category    VARCHAR(150),
        seating_type VARCHAR(20),
        seats       INT,
        latitude    DOUBLE PRECISION NOT NULL,
        longitude   DOUBLE PRECISION NOT NULL,
        census_year SMALLINT,
        geom        GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_cafes_geom ON cafes USING GIST(geom);
    """,
    """
    INSERT INTO cafes (name, address, suburb, category, seating_type, seats, latitude, longitude, census_year, geom)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["name"]), val(r["address"]), val(r["suburb"]), val(r["category"]),
               val(r["seating_type"]), val(r["seats"]), float(r["latitude"]), float(r["longitude"]),
               val(r["census_year"]), float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 2. HEALTH SERVICES (all CoM)
# ─────────────────────────────────────────────
print("\n[2] Loading health_services...")
df = pd.read_csv(os.path.join(CLEANED, "health_services.csv"))

load(
    "health_services", df,
    """
    CREATE TABLE IF NOT EXISTS health_services (
        id                  SERIAL PRIMARY KEY,
        service_id          VARCHAR(100),
        status              VARCHAR(50),
        name                TEXT,
        address             TEXT,
        city                VARCHAR(100),
        state               VARCHAR(10),
        postcode            VARCHAR(10),
        monday_open_hours   VARCHAR(50),
        tuesday_open_hours  VARCHAR(50),
        wednesday_open_hours VARCHAR(50),
        thursday_open_hours VARCHAR(50),
        friday_open_hours   VARCHAR(50),
        saturday_open_hours VARCHAR(50),
        sunday_open_hours   VARCHAR(50),
        parent_org          TEXT,
        latitude            DOUBLE PRECISION NOT NULL,
        longitude           DOUBLE PRECISION NOT NULL,
        geom                GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_health_geom ON health_services USING GIST(geom);
    """,
    """
    INSERT INTO health_services
        (service_id, status, name, address, city, state, postcode,
         monday_open_hours, tuesday_open_hours, wednesday_open_hours,
         thursday_open_hours, friday_open_hours, saturday_open_hours, sunday_open_hours,
         parent_org, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["service_id"]), val(r["status"]), val(r["name"]),
               val(r["address"]), val(r["city"]), val(r["state"]), val(r["postcode"]),
               val(r["monday_open_hours"]), val(r["tuesday_open_hours"]), val(r["wednesday_open_hours"]),
               val(r["thursday_open_hours"]), val(r["friday_open_hours"]), val(r["saturday_open_hours"]),
               val(r["sunday_open_hours"]), val(r["parent_org"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 3. MENTAL HEALTH SERVICES (enriched)
# ─────────────────────────────────────────────
print("\n[3] Loading mental_health_services (enriched)...")
df = pd.read_csv(os.path.join(CLEANED, "mental_health_services_enriched.csv"))

load(
    "mental_health_services", df,
    """
    CREATE TABLE IF NOT EXISTS mental_health_services (
        id                  SERIAL PRIMARY KEY,
        service_id          VARCHAR(100),
        name                TEXT,
        address             TEXT,
        city                VARCHAR(100),
        postcode            VARCHAR(10),
        monday_open_hours   VARCHAR(50),
        tuesday_open_hours  VARCHAR(50),
        wednesday_open_hours VARCHAR(50),
        thursday_open_hours VARCHAR(50),
        friday_open_hours   VARCHAR(50),
        saturday_open_hours VARCHAR(50),
        sunday_open_hours   VARCHAR(50),
        phone               VARCHAR(30),
        website             TEXT,
        google_rating       NUMERIC(3,1),
        google_maps_url     TEXT,
        appointment_note    TEXT,
        latitude            DOUBLE PRECISION NOT NULL,
        longitude           DOUBLE PRECISION NOT NULL,
        geom                GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_mhs_geom ON mental_health_services USING GIST(geom);
    """,
    """
    INSERT INTO mental_health_services
        (service_id, name, address, city, postcode,
         monday_open_hours, tuesday_open_hours, wednesday_open_hours,
         thursday_open_hours, friday_open_hours, saturday_open_hours, sunday_open_hours,
         phone, website, google_rating, google_maps_url, appointment_note,
         latitude, longitude, geom)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["service_id"]), val(r["name"]), val(r["address"]),
               val(r["city"]), val(r["postcode"]),
               val(r["monday_open_hours"]), val(r["tuesday_open_hours"]), val(r["wednesday_open_hours"]),
               val(r["thursday_open_hours"]), val(r["friday_open_hours"]), val(r["saturday_open_hours"]),
               val(r["sunday_open_hours"]), val(r["phone"]), val(r["website"]),
               val(r["google_rating"]), val(r["google_maps_url"]), val(r["appointment_note"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 4. MEMORIALS
# ─────────────────────────────────────────────
print("\n[4] Loading memorials...")
df = pd.read_csv(os.path.join(CLEANED, "memorials.csv"))

load(
    "memorials", df,
    """
    CREATE TABLE IF NOT EXISTS memorials (
        id        SERIAL PRIMARY KEY,
        type      TEXT,
        name      TEXT,
        latitude  DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        geom      GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_memorials_geom ON memorials USING GIST(geom);
    """,
    """
    INSERT INTO memorials (type, name, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["type"]), val(r["name"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 5. OUTDOOR ARTWORKS
# ─────────────────────────────────────────────
print("\n[5] Loading outdoor_artworks...")
df = pd.read_csv(os.path.join(CLEANED, "outdoor_artworks.csv"))

load(
    "outdoor_artworks", df,
    """
    CREATE TABLE IF NOT EXISTS outdoor_artworks (
        id             SERIAL PRIMARY KEY,
        name           TEXT,
        type           VARCHAR(100),
        description    TEXT,
        artist         TEXT,
        year           VARCHAR(50),
        classification VARCHAR(100),
        address        TEXT,
        park_name      TEXT,
        owner          VARCHAR(100),
        latitude       DOUBLE PRECISION NOT NULL,
        longitude      DOUBLE PRECISION NOT NULL,
        geom           GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_artworks_geom ON outdoor_artworks USING GIST(geom);
    """,
    """
    INSERT INTO outdoor_artworks
        (name, type, description, artist, year, classification, address, park_name, owner, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["name"]), val(r["type"]), val(r["description"]), val(r["artist"]),
               val(r["year"]), val(r["classification"]), val(r["address"]), val(r["park_name"]),
               val(r["owner"]), float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 6. PUBLIC ARTWORKS (fountains & monuments)
# ─────────────────────────────────────────────
print("\n[6] Loading public_artworks...")
df = pd.read_csv(os.path.join(CLEANED, "public_artworks.csv"))

load(
    "public_artworks", df,
    """
    CREATE TABLE IF NOT EXISTS public_artworks (
        id          SERIAL PRIMARY KEY,
        type        VARCHAR(100),
        name        TEXT,
        address     TEXT,
        artist      TEXT,
        year        VARCHAR(50),
        description TEXT,
        latitude    DOUBLE PRECISION NOT NULL,
        longitude   DOUBLE PRECISION NOT NULL,
        geom        GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_pub_art_geom ON public_artworks USING GIST(geom);
    """,
    """
    INSERT INTO public_artworks (type, name, address, artist, year, description, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["type"]), val(r["name"]), val(r["address"]), val(r["artist"]),
               val(r["year"]), val(r["description"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 7. PEDESTRIAN HOURLY AVERAGES
# ─────────────────────────────────────────────
print("\n[7] Loading pedestrian_hourly...")
df = pd.read_csv(os.path.join(CLEANED, "pedestrian_hourly.csv"))

load(
    "pedestrian_hourly", df,
    """
    CREATE TABLE IF NOT EXISTS pedestrian_hourly (
        id               SERIAL PRIMARY KEY,
        sensor_name      VARCHAR(50),
        hour             SMALLINT,
        avg_pedestrians  NUMERIC(8,1),
        latitude         DOUBLE PRECISION NOT NULL,
        longitude        DOUBLE PRECISION NOT NULL,
        geom             GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_ped_hourly_geom ON pedestrian_hourly USING GIST(geom);
    CREATE INDEX IF NOT EXISTS idx_ped_hourly_sensor ON pedestrian_hourly (sensor_name, hour);
    """,
    """
    INSERT INTO pedestrian_hourly (sensor_name, hour, avg_pedestrians, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["sensor_name"]), int(r["hour"]), float(r["avg_pedestrians"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 8. PEDESTRIAN SUMMARY (daily average per sensor)
# ─────────────────────────────────────────────
print("\n[8] Loading pedestrian_summary...")
df = pd.read_csv(os.path.join(CLEANED, "pedestrian_summary.csv"))

load(
    "pedestrian_summary", df,
    """
    CREATE TABLE IF NOT EXISTS pedestrian_summary (
        id                    SERIAL PRIMARY KEY,
        sensor_name           VARCHAR(50),
        avg_daily_pedestrians NUMERIC(8,1),
        latitude              DOUBLE PRECISION NOT NULL,
        longitude             DOUBLE PRECISION NOT NULL,
        geom                  GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_ped_summary_geom ON pedestrian_summary USING GIST(geom);
    """,
    """
    INSERT INTO pedestrian_summary (sensor_name, avg_daily_pedestrians, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["sensor_name"]), float(r["avg_daily_pedestrians"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# 9. PLACES (AI-enriched landmarks, artworks, memorials)
# ─────────────────────────────────────────────
print("\n[9] Loading places...")
df = pd.read_csv(os.path.join(CLEANED, "places_final.csv"))

load(
    "places", df,
    """
    CREATE TABLE IF NOT EXISTS places (
        id           SERIAL PRIMARY KEY,
        name         TEXT,
        category     VARCHAR(100),
        sub_category TEXT,
        address      TEXT,
        artist       TEXT,
        year         VARCHAR(50),
        description  TEXT,
        material     TEXT,
        ai_validated BOOLEAN DEFAULT FALSE,
        latitude     DOUBLE PRECISION NOT NULL,
        longitude    DOUBLE PRECISION NOT NULL,
        geom         GEOGRAPHY(POINT, 4326)
    );
    CREATE INDEX IF NOT EXISTS idx_places_geom ON places USING GIST(geom);
    CREATE INDEX IF NOT EXISTS idx_places_category ON places (category);
    """,
    """
    INSERT INTO places
        (name, category, sub_category, address, artist, year, description, material, ai_validated, latitude, longitude, geom)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326))
    """,
    lambda r: (val(r["name"]), val(r["category"]), val(r["sub_category"]),
               val(r["address"]), val(r["artist"]), val(r["year"]),
               val(r["description"]), val(r["material"]),
               bool(r["ai_validated"]),
               float(r["latitude"]), float(r["longitude"]),
               float(r["longitude"]), float(r["latitude"]))
)

# ─────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────
print("\n=== All tables in database ===")
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name NOT IN ('geography_columns','geometry_columns','spatial_ref_sys')
    ORDER BY table_name;
""")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t};")
    print(f"  {t}: {cur.fetchone()[0]:,} rows")

cur.close()
conn.close()
print("\nDone!")
