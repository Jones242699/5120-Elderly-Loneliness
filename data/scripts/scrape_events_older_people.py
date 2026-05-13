"""
Scrapes events for older people from City of Melbourne.
URL: https://www.melbourne.vic.gov.au/programs-and-events-older-people

Step 1 — listing page: title, url, startDate, endDate, location, description, imageUrl
Step 2 — detail page per event: frequency, dayOfWeek, time, isOnline, address, cost, phone, email

Output:
  data/cleaned/events_older_people.json
  frontend/src/data/events_older_people.json
"""

import json
import os
import re
import time
import unicodedata
from datetime import date

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(__file__)
CLEANED_DIR = os.path.join(BASE_DIR, "../cleaned")
FRONTEND_DIR = os.path.join(BASE_DIR, "../../frontend/src/data")

SOURCE_URL = "https://www.melbourne.vic.gov.au/programs-and-events-older-people"
BASE_URL = "https://www.melbourne.vic.gov.au"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-AU,en;q=0.9",
}

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def clean_text(text):
    """Strip unicode whitespace and zero-width characters."""
    text = unicodedata.normalize("NFKC", text)
    # Remove zero-width and other invisible unicode characters
    text = re.sub(r"[​‌‍⁠﻿]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def get_soup(url, params=None):
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


# ── Date parsing ──────────────────────────────────────────────────────────────

def parse_date_pair(date_div):
    """
    Parse start/end dates from a .card-event--date div.

    Year logic: try current year for both. If the end date is already past,
    bump both to next year (event series repeats next cycle). If end >= today,
    keep current year even if start has passed (event is ongoing).
    """
    days = date_div.find_all("span", class_="event-day")
    months = date_div.find_all("span", class_="event-month")

    if not days or not months:
        return None, None

    today = date.today()

    try:
        start_day = int(days[0].get_text(strip=True))
        start_month = MONTH_MAP.get(months[0].get_text(strip=True)[:3])
        if not start_month:
            return None, None

        if len(days) >= 2 and len(months) >= 2:
            end_day = int(days[1].get_text(strip=True))
            end_month = MONTH_MAP.get(months[1].get_text(strip=True)[:3]) or start_month
        else:
            end_day, end_month = start_day, start_month

        year = today.year
        if date(year, end_month, end_day) < today:
            year += 1

        return (
            date(year, start_month, start_day).isoformat(),
            date(year, end_month, end_day).isoformat(),
        )
    except (ValueError, KeyError):
        return None, None


# ── Listing page ──────────────────────────────────────────────────────────────

def parse_card(card):
    """Extract fields available on the listing page card."""
    event = {}

    image_div = card.find("div", class_="card-event--image")
    slug = image_div.get("data-link", "") if image_div else ""
    event["url"] = BASE_URL + slug if slug else ""

    date_div = card.find("div", class_="card-event--date")
    event["startDate"], event["endDate"] = parse_date_pair(date_div) if date_div else (None, None)

    title_tag = card.find("h3", class_="card-event--content-title")
    event["title"] = title_tag.get_text(strip=True) if title_tag else ""

    desc_div = card.find("div", class_="content")
    p = desc_div.find("p") if desc_div else None
    event["description"] = p.get_text(strip=True) if p else ""

    tag_icon = card.find("div", class_="tag-icon")
    span = tag_icon.find("span") if tag_icon else None
    event["location"] = span.get_text(strip=True) if span else ""

    picture = card.find("picture")
    if picture:
        source = picture.find("source", type="image/webp")
        if source and source.get("srcset"):
            event["imageUrl"] = source["srcset"].split(",")[0].strip()
        else:
            img = picture.find("img")
            event["imageUrl"] = img["src"] if img and img.get("src") else ""
    else:
        event["imageUrl"] = ""

    return event


# ── Detail page ───────────────────────────────────────────────────────────────

def parse_frequency(raw):
    """
    Extract dayOfWeek and time from the .event-date string.

    Examples:
      "Every Wednesday (excluding public holidays), 2pm to 3pm and 3.15pm to 4pm"
        → day: "Wednesday", time: "2pm to 3pm and 3.15pm to 4pm"
      "Wednesday fortnights (excluding public holidays), 11am to midday"
        → day: "Wednesday", time: "11am to midday"
      "Every Friday, 10am to 11am"
        → day: "Friday", time: "10am to 11am"
    """
    raw = clean_text(raw)

    day = ""
    for d in DAYS_OF_WEEK:
        if d.lower() in raw.lower():
            day = d
            break

    # Time is everything after the last comma
    time_str = ""
    if "," in raw:
        after_comma = raw.rsplit(",", 1)[-1].strip()
        # Strip trailing parenthetical notes
        after_comma = re.sub(r"\(.*?\)", "", after_comma).strip()
        if re.search(r"\d+(am|pm)|midday|midnight|noon", after_comma, re.I):
            time_str = after_comma

    return day, time_str


def scrape_detail(url):
    """Fetch an event detail page and return enrichment fields."""
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"    WARN: could not fetch {url}: {e}")
        return {}

    detail = {}

    # Frequency / schedule string
    event_date_div = soup.find("div", class_="event-date")
    if event_date_div:
        raw_freq = clean_text(event_date_div.get_text(separator=" ", strip=True))
        detail["frequency"] = raw_freq
        detail["dayOfWeek"], detail["time"] = parse_frequency(raw_freq)
    else:
        detail["frequency"] = ""
        detail["dayOfWeek"] = ""
        detail["time"] = ""

    # Cost
    cost_div = soup.find("div", class_="event-details-primary-cost")
    if cost_div:
        cost_text = clean_text(cost_div.get_text(separator=" ", strip=True))
        # Strip the label word "cost" from the start
        detail["cost"] = re.sub(r"^cost\s*", "", cost_text, flags=re.I).strip()
    else:
        detail["cost"] = ""

    # Address — also used to determine isOnline
    addr_div = soup.find("div", class_="event-details-secondary-address")
    if addr_div:
        addr_lines = [clean_text(t) for t in addr_div.stripped_strings]
        # Remove the label "address" and "View map" link text
        addr_lines = [l for l in addr_lines if l.lower() not in ("address", "view map")]
        full_address = ", ".join(addr_lines)
        detail["isOnline"] = full_address.strip().lower() == "online"
        detail["address"] = "" if detail["isOnline"] else full_address
    else:
        detail["isOnline"] = False
        detail["address"] = ""

    # Phone
    phone_div = soup.find("div", class_="event-details-secondary-phone")
    if phone_div:
        phone_text = clean_text(phone_div.get_text(separator=" ", strip=True))
        detail["phone"] = re.sub(r"^phone\s*", "", phone_text, flags=re.I).strip()
    else:
        detail["phone"] = ""

    # Email
    email_div = soup.find("div", class_="event-details-secondary-email")
    if email_div:
        email_text = clean_text(email_div.get_text(separator=" ", strip=True))
        detail["email"] = re.sub(r"^email\s*", "", email_text, flags=re.I).strip()
    else:
        detail["email"] = ""

    return detail


# ── Orchestration ─────────────────────────────────────────────────────────────

def scrape_all_events():
    events = []
    page = 1

    # Step 1: collect all listing cards
    while True:
        params = {"page": page - 1} if page > 1 else {}
        print(f"  Listing page {page}...")
        soup = get_soup(SOURCE_URL, params=params)
        cards = soup.find_all("div", class_="card-event")

        if not cards:
            break

        for card in cards:
            event = parse_card(card)
            if event["title"]:
                events.append(event)

        print(f"    {len(cards)} events (total: {len(events)})")

        if not soup.find("li", class_="pager__item--next"):
            break
        page += 1
        time.sleep(0.5)

    # Step 2: enrich each event from its detail page
    print(f"\n  Fetching detail pages for {len(events)} events...")
    for i, event in enumerate(events, 1):
        if not event["url"]:
            continue
        print(f"  [{i}/{len(events)}] {event['title']}")
        detail = scrape_detail(event["url"])
        event.update(detail)
        time.sleep(0.4)

    return events


def save(events):
    os.makedirs(CLEANED_DIR, exist_ok=True)
    os.makedirs(FRONTEND_DIR, exist_ok=True)

    for path in [
        os.path.join(CLEANED_DIR, "events_older_people.json"),
        os.path.join(FRONTEND_DIR, "events_older_people.json"),
    ]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print(f"  Saved → {path}")


if __name__ == "__main__":
    print("Scraping City of Melbourne — programs and events for older people...")
    events = scrape_all_events()
    print(f"\nTotal events scraped: {len(events)}")
    save(events)
    print("\nDone.")
