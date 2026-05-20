"""
Loads events_older_people.json into PostgreSQL RDS.

Run scrape_events_older_people.py first to generate the JSON, then run this script.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../py_packages"))

import psycopg2

BASE = os.path.dirname(__file__)
CLEANED = os.path.join(BASE, "../cleaned")

DB = dict(
    host="elderly-loneliness-database.c58eaa0yqnag.ap-southeast-2.rds.amazonaws.com",
    port=5432, dbname="postgres", user="postgres", password="fit5120te28"
)

JSON_PATH = os.path.join(CLEANED, "events_older_people.json")

if not os.path.exists(JSON_PATH):
    print("ERROR: events_older_people.json not found. Run scrape_events_older_people.py first.")
    sys.exit(1)

with open(JSON_PATH, encoding="utf-8") as f:
    events = json.load(f)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

print("Creating events_older_people table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS events_older_people (
        id          SERIAL PRIMARY KEY,
        title       TEXT,
        url         TEXT,
        start_date  DATE,
        end_date    DATE,
        location    TEXT,
        description TEXT,
        image_url   TEXT,
        frequency   TEXT,
        day_of_week VARCHAR(20),
        time        VARCHAR(100),
        is_online   BOOLEAN,
        address     TEXT,
        cost        TEXT,
        phone       VARCHAR(30),
        email       VARCHAR(100)
    );
""")

print("Truncating existing rows...")
cur.execute("TRUNCATE events_older_people RESTART IDENTITY;")

INSERT_SQL = """
    INSERT INTO events_older_people
        (title, url, start_date, end_date, location, description, image_url,
         frequency, day_of_week, time, is_online, address, cost, phone, email)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""

rows = [
    (
        e.get("title") or None,
        e.get("url") or None,
        e.get("startDate") or None,
        e.get("endDate") or None,
        e.get("location") or None,
        e.get("description") or None,
        e.get("imageUrl") or None,
        e.get("frequency") or None,
        e.get("dayOfWeek") or None,
        e.get("time") or None,
        bool(e.get("isOnline", False)),
        e.get("address") or None,
        e.get("cost") or None,
        e.get("phone") or None,
        e.get("email") or None,
    )
    for e in events
]

cur.executemany(INSERT_SQL, rows)
conn.commit()

cur.execute("SELECT COUNT(*) FROM events_older_people;")
count = cur.fetchone()[0]
print(f"  events_older_people: {count} rows loaded")

cur.close()
conn.close()
print("\nDone.")
