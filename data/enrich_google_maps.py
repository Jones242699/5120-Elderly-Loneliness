"""
Enriches mental_health_services.csv with data from Google Places API:
  - Accurate opening hours
  - Phone number
  - Website (for appointment booking)
  - Google rating
  - Google Maps URL

Usage:
    python enrich_google_maps.py <YOUR_GOOGLE_MAPS_API_KEY>
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "py_packages"))

import pandas as pd
import urllib.request
import urllib.parse
import json

if len(sys.argv) < 2:
    print("Usage: python enrich_google_maps.py <YOUR_GOOGLE_MAPS_API_KEY>")
    sys.exit(1)

API_KEY = sys.argv[1]
BASE = os.path.dirname(__file__)
INPUT = os.path.join(BASE, "cleaned", "mental_health_services.csv")
OUTPUT = os.path.join(BASE, "cleaned", "mental_health_services_enriched.csv")

TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

DETAIL_FIELDS = "name,formatted_phone_number,website,opening_hours,rating,url,formatted_address"


def find_place(name, city):
    """Find a place ID using Text Search, trying progressively simpler queries."""
    # Strip location suffixes like " - Melbourne CBD", " - Kensington" from names
    clean_name = name.split(" - ")[0].strip()

    queries = [
        f"{clean_name} {city} Melbourne VIC",
        f"{clean_name} Melbourne",
    ]
    for query in queries:
        params = urllib.parse.urlencode({
            "query": query,
            "key": API_KEY,
        })
        url = f"{TEXTSEARCH_URL}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            results = data.get("results", [])
            if results:
                return results[0]["place_id"]
        except Exception as e:
            print(f"    Search error for '{name}': {e}")
    return None


def get_place_details(place_id):
    """Get detailed info for a place ID."""
    params = urllib.parse.urlencode({
        "place_id": place_id,
        "fields": DETAIL_FIELDS,
        "key": API_KEY,
    })
    url = f"{DETAILS_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("result", {})
    except Exception as e:
        print(f"    Details error for place_id '{place_id}': {e}")
    return {}


def format_hours(opening_hours):
    """Convert Google opening_hours periods into a readable dict."""
    if not opening_hours:
        return {}
    day_names = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    result = {}
    for period in opening_hours.get("periods", []):
        open_day = period.get("open", {})
        close_day = period.get("close", {})
        day = day_names[open_day.get("day", 0)]
        open_time = open_day.get("time", "")
        close_time = close_day.get("time", "")
        if open_time and close_time:
            # Format HHMM -> HH:MM
            result[day] = f"{open_time[:2]}:{open_time[2:]} - {close_time[:2]}:{close_time[2:]}"
        elif open_time == "0000" and not close_time:
            result[day] = "Open 24 hours"
    return result


df = pd.read_csv(INPUT)
print(f"Enriching {len(df)} services via Google Places API...")
print()

# New columns to add
new_cols = {
    "phone": pd.NA,
    "website": pd.NA,
    "google_rating": pd.NA,
    "google_maps_url": pd.NA,
    "appointment_note": pd.NA,
}
for col, val in new_cols.items():
    df[col] = val

hour_cols = ["monday_open_hours", "tuesday_open_hours", "wednesday_open_hours",
             "thursday_open_hours", "friday_open_hours", "saturday_open_hours",
             "sunday_open_hours"]

enriched = 0
skipped = 0

for idx, row in df.iterrows():
    name = row["name"]
    address = row.get("address", "")
    city = row.get("city", "Melbourne")

    # Only call API if hours are missing OR we want phone/website regardless
    print(f"[{idx+1}/{len(df)}] {name}")

    place_id = find_place(name, city)
    if not place_id:
        print(f"    Not found in Google Maps")
        skipped += 1
        time.sleep(0.2)
        continue

    details = get_place_details(place_id)
    if not details:
        skipped += 1
        time.sleep(0.2)
        continue

    # Phone
    if details.get("formatted_phone_number"):
        df.at[idx, "phone"] = details["formatted_phone_number"]

    # Website
    website = details.get("website", "")
    if website:
        df.at[idx, "website"] = website
        # Simple appointment note heuristic
        if any(kw in website.lower() for kw in ["book", "appoint", "health2u", "healthengine",
                                                  "hotdoc", "myhealth", "connect"]):
            df.at[idx, "appointment_note"] = "Online booking available — see website"
        else:
            df.at[idx, "appointment_note"] = "Call or visit website to book"

    # Rating
    if details.get("rating"):
        df.at[idx, "google_rating"] = details["rating"]

    # Google Maps URL
    if details.get("url"):
        df.at[idx, "google_maps_url"] = details["url"]

    # Opening hours — only fill missing days from Google
    google_hours = format_hours(details.get("opening_hours", {}))
    day_map = {
        "monday": "monday_open_hours",
        "tuesday": "tuesday_open_hours",
        "wednesday": "wednesday_open_hours",
        "thursday": "thursday_open_hours",
        "friday": "friday_open_hours",
        "saturday": "saturday_open_hours",
        "sunday": "sunday_open_hours",
    }
    for day, col in day_map.items():
        if pd.isna(df.at[idx, col]) and day in google_hours:
            df.at[idx, col] = google_hours[day]

    enriched += 1
    print(f"    OK — phone: {details.get('formatted_phone_number','—')} | "
          f"rating: {details.get('rating','—')} | website: {'yes' if website else 'no'}")

    # Respect API rate limits
    time.sleep(0.2)

print()
print(f"Done. Enriched: {enriched} | Not found: {skipped}")
df.to_csv(OUTPUT, index=False, encoding="utf-8")
print(f"Saved {OUTPUT}")
