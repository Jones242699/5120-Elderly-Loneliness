"""
Enriches places.csv with descriptions scraped from the Wikipedia REST API.

Targets:
  - Rows with no description
  - Rows with descriptions < 100 chars (likely just raw material notes)
  - Rows where Wikipedia returned a clearly wrong/generic result

Results are cached to cleaned/wikipedia_cache.json so re-runs skip already-fetched entries.
Clear the cache or delete an entry to force a re-fetch.

Usage:
    python enrich_descriptions.py

Output: data/cleaned/places_enriched.csv
"""

import os
import json
import time
import urllib.parse
import urllib.request
import pandas as pd

BASE = os.path.dirname(__file__)
CLEANED = os.path.join(BASE, "../cleaned")
CACHE_FILE = os.path.join(CLEANED, "wikipedia_cache.json")

HEADERS = {
    "User-Agent": "FIT5120-ElderlyLoneliness/1.0 (student project)"
}
SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

# Phrases that signal Wikipedia returned the wrong / too-generic article
GENERIC_SIGNALS = [
    "this is a list of",
    "the following is a",
    "may refer to",
    "disambiguation",
    "is a retired",
    "is an american",
    "is a british",
    "is an english",
    "is a former",
    "is a canadian",
    "is a french sculptor",
    "waterfalls in australia",
    "theatres in melbourne",
    "timeline of the history",
    "band names",
    "artistic gymnast",
    "mermaiding is the practice",
    "2020s is the current decade",
    "surname",
]


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_json(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def search_wikipedia(query):
    """Return up to 3 Wikipedia page titles matching query."""
    data = fetch_json(SEARCH_URL, {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 3,
        "format": "json",
    })
    if not data:
        return []
    return [r["title"] for r in data.get("query", {}).get("search", [])]


def get_summary(title):
    """Return the Wikipedia plain-text extract for a page, or ''."""
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    data = fetch_json(SUMMARY_URL.format(encoded))
    if not data:
        return ""
    if data.get("type") == "disambiguation":
        return ""
    extract = data.get("extract", "").strip()
    # Trim to ~600 chars at a sentence boundary
    if len(extract) > 600:
        cut = extract[:600].rfind(".")
        extract = extract[: cut + 1] if cut > 200 else extract[:600]
    return extract


def is_generic(text, name):
    """Return True if the text looks like a wrong/generic Wikipedia hit."""
    if not text:
        return True
    low = text.lower()
    if any(sig in low for sig in GENERIC_SIGNALS):
        return True
    # If the extract is very short it's probably useless
    if len(text) < 60:
        return True
    return False


def lookup(name, sub_category, artist, cache_key, cache):
    """
    Try multiple Wikipedia search strategies for a place.
    Returns the best description found, or ''.
    """
    if cache_key in cache:
        cached = cache[cache_key]
        # Only trust the cache if it's a real description (not a previous failure)
        if cached and not is_generic(cached, name):
            return cached
        # Re-try on empty or generic cached result
        if cached == "__skip__":
            return ""

    strategies = [
        f"{name} Melbourne",
        f"{name} Melbourne artwork",
        f"{name} Melbourne Victoria",
    ]
    if artist and str(artist).strip() not in ("", "nan", "Unknown", "Unknown<br>"):
        strategies.insert(1, f"{name} {artist} Melbourne")
    if sub_category:
        strategies.append(f"{name} {sub_category} Melbourne")

    best = ""
    for query in strategies:
        titles = search_wikipedia(query)
        time.sleep(0.25)
        for title in titles:
            summary = get_summary(title)
            time.sleep(0.25)
            if not is_generic(summary, name):
                best = summary
                break
        if best:
            break

    cache[cache_key] = best if best else "__skip__"
    return best


def needs_enrichment(desc):
    """Return True if the description is missing or too short/generic."""
    desc = str(desc).strip() if pd.notna(desc) else ""
    if not desc or desc.lower() in ("nan", "none"):
        return True
    if len(desc) < 100:
        return True
    return False


def build_fallback(row):
    """
    Build a human-readable description from structured fields when
    Wikipedia returns nothing useful.
    """
    name = str(row["name"]).strip()
    sub = str(row["sub_category"]).strip() if pd.notna(row["sub_category"]) else ""
    artist = str(row["artist"]).strip() if pd.notna(row["artist"]) else ""
    year = str(row["year"]).strip() if pd.notna(row["year"]) else ""
    address = str(row["address"]).strip() if pd.notna(row["address"]) else ""
    category = str(row["category"]).strip()
    material = str(row["material"]).strip() if pd.notna(row["material"]) else ""

    # Clean up bad artist strings
    artist = artist.replace("<br>", "").replace("Unknown", "").strip(" ,")

    parts = []

    if sub and sub.lower() not in ("nan", "none", ""):
        parts.append(f"{name} is a {sub.lower()} located in Melbourne")
    else:
        parts.append(f"{name} is a {category.lower()} located in Melbourne")

    if address and address.lower() not in ("nan", "none", ""):
        parts.append(f"at {address}")

    sentence = " ".join(parts) + "."

    details = []
    if artist:
        details.append(f"Created by {artist}")
    if year and year not in ("nan", "None", ""):
        details.append(f"in {year}")
    if material and material.lower() not in ("nan", "none", ""):
        details.append(f"using {material.lower()}")

    if details:
        sentence += " " + " ".join(details) + "."

    return sentence


# ── Main ──────────────────────────────────────────────────────────────────────
places_path = os.path.join(CLEANED, "places.csv")
if not os.path.exists(places_path):
    raise FileNotFoundError("Run clean_places.py first to generate places.csv")

df = pd.read_csv(places_path, encoding="utf-8")
cache = load_cache()

# Clear stale/generic cache entries so they get retried with better queries
stale_keys = [k for k, v in cache.items() if v and (is_generic(v, k) or v == "__skip__")]
for k in stale_keys:
    del cache[k]
if stale_keys:
    print(f"Cleared {len(stale_keys)} stale/generic cache entries.")

target_mask = df["description"].apply(needs_enrichment)
total = target_mask.sum()
print(f"Enriching {total} places (missing or short description) via Wikipedia...")
print(f"Category breakdown: {df[target_mask]['category'].value_counts().to_dict()}\n")

enriched = 0
for idx in df[target_mask].index:
    name = str(df.at[idx, "name"])
    sub = str(df.at[idx, "sub_category"]) if pd.notna(df.at[idx, "sub_category"]) else ""
    artist = str(df.at[idx, "artist"]) if pd.notna(df.at[idx, "artist"]) else ""
    cache_key = name

    desc = lookup(name, sub, artist, cache_key, cache)
    if not desc:
        desc = build_fallback(df.loc[idx])
    if desc:
        df.at[idx, "description"] = desc
        enriched += 1

    done = enriched + (idx - df[target_mask].index[0] - enriched + 1)
    if done % 50 == 0:
        save_cache(cache)
        print(f"  ...processed {done}/{total}, enriched {enriched} so far.")

save_cache(cache)

# Final pass: replace any remaining wrong/generic Wikipedia hits with fallback
fixed = 0
for idx, row in df.iterrows():
    desc = str(row["description"]).strip() if pd.notna(row["description"]) else ""
    if is_generic(desc, str(row["name"])):
        df.at[idx, "description"] = build_fallback(row)
        fixed += 1

if fixed:
    print(f"Fixed {fixed} remaining bad/generic descriptions with fallback text.")

out_path = os.path.join(CLEANED, "places_enriched.csv")
df.to_csv(out_path, index=False, encoding="utf-8")

still_missing = df["description"].apply(needs_enrichment).sum()
print(f"\nDone. Enriched {enriched} / {total} targeted places.")
print(f"Places still needing description: {still_missing}")
print(f"Saved → {out_path}")
