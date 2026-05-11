"""
Scrapes artwork/memorial descriptions from Melbourne City Collection.
URL: https://citycollection.melbourne.vic.gov.au/collections/?col=Public+art+and+memorials

Steps:
  1. Crawl all listing pages to collect artwork slugs + names
  2. Fetch each detail page and extract: title, description, artist, year, medium, location
  3. Fuzzy-match by name against places_enriched.csv
  4. Update descriptions (and artist/year/material where blank in places)
  5. Save to cleaned/places_enriched.csv  (overwrites in-place)

Cache: cleaned/city_collection_cache.json — re-runs skip already-fetched slugs.
"""

import os
import re
import json
import time
import unicodedata

import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = os.path.dirname(__file__)
CLEANED = os.path.join(BASE, "../cleaned")
CACHE_FILE = os.path.join(CLEANED, "city_collection_cache.json")

BASE_URL = "https://citycollection.melbourne.vic.gov.au"
COLLECTION_URL_P1 = BASE_URL + "/collections/?col=Public+art+and+memorials"
COLLECTION_URL = BASE_URL + "/collections/page/{}/?col=Public+art+and+memorials"

HEADERS = {"User-Agent": "FIT5120-ElderlyLoneliness/1.0 (student research project)"}
DELAY = 0.4  # seconds between requests


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"  WARN: failed to fetch {url}: {e}")
        return None


def normalise(text):
    """Lowercase, strip accents, remove non-alphanumeric for fuzzy matching."""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def word_overlap(a, b):
    """Fraction of words in the shorter string that appear in the longer."""
    wa, wb = set(normalise(a).split()), set(normalise(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


# ── Step 1: crawl listing pages to collect slugs ──────────────────────────────

def collect_slugs():
    """Return list of (name, slug) tuples from all listing pages."""
    slugs = []
    # Page 1 has a different URL than pages 2+
    pages_urls = [COLLECTION_URL_P1] + [COLLECTION_URL.format(p) for p in range(2, 10)]

    for url in pages_urls:
        soup = get_soup(url)
        if not soup:
            break
        time.sleep(DELAY)

        # Cards: <a href="https://citycollection.../{slug}/"><img><h4>Title</h4>...</a>
        found = []
        for a in soup.find_all("a", href=re.compile(r"citycollection\.melbourne\.vic\.gov\.au/[^/?#]+/$")):
            h4 = a.find("h4")
            if not h4:
                continue
            title = h4.get_text(strip=True)
            href = a["href"].rstrip("/")
            slug = href.split("/")[-1]
            # Skip collection/category pages
            if slug in ("collections", "public-art-and-memorials", ""):
                continue
            if title:
                found.append((title, slug))

        if not found:
            break  # past last page

        slugs.extend(found)
        print(f"  {url.split('?')[0]}: {len(found)} artworks (total: {len(slugs)})")

        # Stop if there's no "Next" link
        next_link = soup.find("a", string=re.compile(r"Next", re.I))
        if not next_link:
            break

    return slugs


# ── Step 2: scrape detail page ────────────────────────────────────────────────

def scrape_detail(slug):
    """
    Fetch /slug/ and return dict:
      title, description, artist, year, medium, location
    """
    url = f"{BASE_URL}/{slug}/"
    soup = get_soup(url)
    if not soup:
        return None
    time.sleep(DELAY)

    result = {"slug": slug, "title": "", "description": "", "artist": "",
              "year": "", "medium": "", "location": ""}

    # Title — use <h1> but strip any immediately adjacent text nodes (e.g. "undated")
    h1 = soup.find("h1")
    if h1:
        # Only take the direct text of the h1, not nested tags
        title_text = h1.find(string=True, recursive=False)
        if title_text:
            result["title"] = title_text.strip()
        else:
            result["title"] = h1.get_text(strip=True)

    # Try to find the main content area
    content = (soup.find("div", class_=re.compile(r"entry-content|post-content|single-content|content", re.I))
               or soup.find("article")
               or soup.find("main"))

    if not content:
        return result

    # Metadata label prefixes to strip from description text
    META_PREFIXES = re.compile(
        r"^(Location|Medium|Materials?|Community contribution|Credit|Inscription|"
        r"Dimensions|Registration|Maker|Artist|Year|Date|Donated)[:\s].*",
        re.I | re.MULTILINE,
    )

    def clean_desc(text):
        """Remove metadata label lines and tidy whitespace."""
        lines = [l.strip() for l in text.splitlines()]
        clean = [l for l in lines if l and not META_PREFIXES.match(l)]
        return " ".join(clean).strip()

    # Description: first try the text after <h4>Summary</h4>
    summary_h4 = content.find("h4", string=re.compile(r"summary", re.I))
    if summary_h4:
        parts = []
        for sib in summary_h4.next_siblings:
            if sib.name == "h4":
                break
            text = sib.get_text(strip=True) if hasattr(sib, "get_text") else str(sib).strip()
            if text:
                parts.append(text)
        summary_text = clean_desc("\n".join(parts))
        if len(summary_text) > 40:
            result["description"] = summary_text

    # Fallback: longest <p> in content
    if not result["description"]:
        paragraphs = content.find_all("p")
        best_para = max(
            (clean_desc(p.get_text(strip=True)) for p in paragraphs if len(p.get_text(strip=True)) > 40),
            key=len,
            default="",
        )
        result["description"] = best_para

    # Metadata: site uses <h4> labels followed by sibling text or <p>
    full_text = content.get_text("\n")

    # Build a label→value map from h4 headings and their following siblings
    label_map = {}
    for h4 in content.find_all("h4"):
        label = h4.get_text(strip=True).lower().rstrip(":")
        # Next sibling text
        sibling = h4.find_next_sibling()
        if sibling:
            val = sibling.get_text(strip=True)
        else:
            val = ""
        if val and val.lower() not in ("undated", "unknown", "maker unknown", ""):
            label_map[label] = val

    def from_map(*keys):
        for k in keys:
            for label, val in label_map.items():
                if k in label:
                    return val
        return ""

    # Fall back to regex on full text if label_map misses
    def from_regex(patterns):
        for pat in patterns:
            m = re.search(pat, full_text, re.I | re.MULTILINE)
            if m:
                val = m.group(1).strip()
                val = re.split(r"\n", val)[0].strip()
                if val and val.lower() not in ("undated", "unknown", "maker unknown", ""):
                    return val
        return ""

    result["artist"] = (from_map("artist", "maker", "sculptor", "designer")
                        or from_regex([r"Artist[:\s]+([^\n]+)", r"Maker[:\s]+([^\n]+)"]))

    result["year"] = (from_map("year", "date", "production")
                      or from_regex([r"Year[:\s]+(\d{4})", r"\b(1[89]\d{2}|20[012]\d)\b"]))

    result["medium"] = (from_map("medium", "material")
                        or from_regex([r"Medium[:\s]+([^\n]+)", r"Materials?[:\s]+([^\n]+)"]))

    result["location"] = (from_map("location", "installed")
                          or from_regex([r"Location[:\s]+([^\n]+)"]))

    return result


# ── Step 3: load cache ────────────────────────────────────────────────────────

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# ── Step 4: match scraped entries to places dataframe ────────────────────────

def match_to_places(df, scraped_records):
    """
    For each scraped record, find the best-matching row in df by name.
    Updates description (and artist/year/medium if blank).
    Returns number of rows updated.
    """
    updated = 0
    for rec in scraped_records:
        scraped_name = rec.get("title", "") or rec.get("slug", "").replace("-", " ")
        desc = rec.get("description", "").strip()
        if not desc or len(desc) < 60:
            continue

        best_idx = None
        best_score = 0.0
        for idx, row in df.iterrows():
            score = word_overlap(scraped_name, row["name"])
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx is None or best_score < 0.6:
            continue  # no confident match

        # Only update if scraped description is richer than what we have
        existing = str(df.at[best_idx, "description"]).strip()
        if True:  # City Collection always takes priority over Wikipedia
            df.at[best_idx, "description"] = desc
            updated += 1

        # Fill in blank metadata fields
        for field, col in [("artist", "artist"), ("year", "year"), ("medium", "material")]:
            val = rec.get(field, "").strip()
            if val and str(df.at[best_idx, col]).strip() in ("", "nan", "None"):
                df.at[best_idx, col] = val

    return updated


# ── Main ──────────────────────────────────────────────────────────────────────

enriched_path = os.path.join(CLEANED, "places_enriched.csv")
if not os.path.exists(enriched_path):
    raise FileNotFoundError("Run enrich_descriptions.py first to generate places_enriched.csv")

df = pd.read_csv(enriched_path, encoding="utf-8")
cache = load_cache()

print("Step 1: Collecting artwork slugs from Melbourne City Collection...")
slugs = collect_slugs()
print(f"  Found {len(slugs)} artworks total.\n")

print("Step 2: Fetching detail pages (skipping cached)...")
new_fetches = 0
for name, slug in slugs:
    if slug in cache:
        continue
    rec = scrape_detail(slug)
    if rec:
        cache[slug] = rec
        new_fetches += 1
    if new_fetches % 20 == 0 and new_fetches > 0:
        save_cache(cache)
        print(f"  ...fetched {new_fetches} new pages, cache saved.")

save_cache(cache)
print(f"  Fetched {new_fetches} new detail pages ({len(cache)} total in cache).\n")

print("Step 3: Matching scraped descriptions to places...")
records = list(cache.values())
updated = match_to_places(df, records)
print(f"  Updated {updated} place descriptions from City Collection.\n")

# Step 4: add City Collection entries that have no match in our dataset
# (these are memorials/artworks in the collection but not in the open data CSVs)
print("Step 4: Adding unmatched City Collection entries as new rows...")

existing_norm = set(normalise(n) for n in df["name"])
new_rows = []
for rec in records:
    title = rec.get("title", "").strip()
    desc = rec.get("description", "").strip()
    if not title or not desc or len(desc) < 60:
        continue
    if normalise(title) in existing_norm:
        continue
    # Only add if we have at least a description
    new_rows.append({
        "id": None,  # will reassign below
        "name": title,
        "category": "Memorials & Sculptures",
        "sub_category": "",
        "address": rec.get("location", ""),
        "latitude": None,
        "longitude": None,
        "artist": rec.get("artist", ""),
        "year": rec.get("year", ""),
        "description": desc,
        "material": rec.get("medium", ""),
    })

if new_rows:
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    # Reassign sequential IDs
    df["id"] = range(1, len(df) + 1)
    print(f"  Added {len(new_rows)} new entries from City Collection (no coordinates yet).\n")
else:
    print("  No new entries to add.\n")

df.to_csv(enriched_path, index=False, encoding="utf-8")

still_short = (df["description"].fillna("").str.len() < 60).sum()
print(f"Saved → {enriched_path}")
print(f"Places with short/no description: {still_short} / {len(df)}")
print(f"\nCategory description coverage:")
for cat in df["category"].unique():
    sub = df[df["category"] == cat]
    good = (sub["description"].fillna("").str.len() >= 60).sum()
    print(f"  {cat}: {good}/{len(sub)}")
