"""
Load seats/benches from cleaned street_furniture.csv into PostgreSQL.

Usage:
    python load_benches.py <host> <port> <dbname> <user> <password>

Example:
    python load_benches.py localhost 5432 echo_db postgres mypassword
    python load_benches.py mydb.rds.amazonaws.com 5432 echo_db admin mypassword
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "py_packages"))

import pandas as pd

if len(sys.argv) < 6:
    print("Usage: python load_benches.py <host> <port> <dbname> <user> <password>")
    sys.exit(1)

host, port, dbname, user, password = sys.argv[1:6]

try:
    import psycopg2
except ModuleNotFoundError:
    print("Installing psycopg2...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary",
                           f"--target={os.path.join(os.path.dirname(__file__), 'py_packages')}",
                           "--quiet"])
    import psycopg2

BASE = os.path.dirname(__file__)

# Load and filter to seats/benches only
df = pd.read_csv(os.path.join(BASE, "cleaned", "street_furniture.csv"))
benches = df[df["type"].isin(["Seat", "Picnic Setting"])].copy()
benches = benches.dropna(subset=["latitude", "longitude"])

# Replace NaN with None for SQL NULL
benches = benches.where(pd.notna(benches), None)

print(f"Loaded {len(benches)} benches/seats from CSV")
print(f"Connecting to {user}@{host}:{port}/{dbname} ...")

conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
cur = conn.cursor()

# Create table
cur.execute("""
    CREATE TABLE IF NOT EXISTS public_benches (
        id          SERIAL PRIMARY KEY,
        description TEXT,
        type        VARCHAR(50),
        model       VARCHAR(255),
        location    TEXT,
        condition   NUMERIC(4,2),
        latitude    DOUBLE PRECISION NOT NULL,
        longitude   DOUBLE PRECISION NOT NULL
    );
""")

cur.execute("CREATE INDEX IF NOT EXISTS idx_benches_lat_lon ON public_benches (latitude, longitude);")

# Clear existing data before reload
cur.execute("TRUNCATE public_benches RESTART IDENTITY;")

# Bulk insert
rows = [
    (
        row["description"],
        row["type"],
        row["model"],
        row["location"],
        row["condition"],
        float(row["latitude"]),
        float(row["longitude"]),
    )
    for _, row in benches.iterrows()
]

cur.executemany("""
    INSERT INTO public_benches (description, type, model, location, condition, latitude, longitude)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", rows)

conn.commit()
cur.close()
conn.close()

print(f"Done! {len(rows)} rows inserted into public_benches.")
