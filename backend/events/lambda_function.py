"""
AWS Lambda handler for the events API.

Endpoints:
GET /events
GET /events/{id}
"""

import json
import os
import urllib.request
import urllib.parse
import time


# ===== API Config =====
API_KEY = os.environ["TICKETMASTER_API_KEY"]

# ===== Default Location (Melbourne CBD) =====
DEFAULT_LAT = -37.8136
DEFAULT_LNG = 144.9631

DEFAULT_LIMIT = 100

# ===== Per Keyword Limit =====
PER_KEYWORD_LIMIT = 10

# ===== Max Distance Filter (KM) =====
MAX_DISTANCE_KM = 50

# ===== Australia Country Code =====
AU_COUNTRY_CODE = "AU"

# ===== Search Keywords =====
SEARCH_KEYWORDS = [
    "community",
    "music",
    "art",
    "wellness",
    "workshop",
    "walking",
    "seniors",
    "gardening",
    "yoga",
    "theatre"
]

# ===== Local Elderly-Friendly Filter =====
FILTER_KEYWORDS = [
    "book club",
    "digital literacy",
    "coffee morning",
    "friendship",
    "balance class",
    "tai chi",
    "bird watching",
    "gentle exercise",
    "community lunch",
    "reading",
    "history",
    "heritage"
]

# ===== Excluded Words =====
EXCLUDED_WORDS = [
    "motogp",
    "campground",
    "coach",
    "race day"
]


# ===== Standard Response =====
def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


# ===== Fetch Event List =====
def fetch_events(lat, lng, limit, keyword):

    query_params = {
        "apikey": API_KEY,

        "latlong": f"{lat},{lng}",

        "sort": "distance,asc",

        "size": limit,

        "keyword": keyword
    }

    encoded_params = urllib.parse.urlencode(query_params)

    url = (
        "https://app.ticketmaster.com"
        f"/discovery/v2/events.json?{encoded_params}"
    )

    print("Request URL:", url)

    with urllib.request.urlopen(url) as api_response:

        data = json.loads(
            api_response.read().decode("utf-8")
        )

    raw_events = (
        data.get("_embedded", {})
        .get("events", [])
    )

    formatted_events = []

    for event_item in raw_events:

        venue_name = None
        venue_lat = None
        venue_lng = None
        venue_country = None

        embedded = event_item.get("_embedded", {})
        venues = embedded.get("venues", [])

        if venues:

            venue = venues[0]

            venue_name = venue.get("name")

            location = venue.get("location", {})

            venue_lat = location.get("latitude")
            venue_lng = location.get("longitude")

            country = venue.get("country", {})

            venue_country = country.get("countryCode")

        image_url = None

        images = event_item.get("images", [])

        if images:
            image_url = images[0].get("url")

        classification = None

        classifications = event_item.get("classifications", [])

        if classifications:

            segment = classifications[0].get("segment", {})

            classification = segment.get("name")

        formatted_events.append({
            "id": event_item.get("id"),

            "name": event_item.get("name"),

            "keyword": keyword,

            "date": (
                event_item.get("dates", {})
                .get("start", {})
                .get("localDate")
            ),

            "classification": classification,

            "venue": venue_name,

            "latitude": venue_lat,
            "longitude": venue_lng,

            "country": venue_country,

            "distance": event_item.get("distance"),

            "image": image_url,

            "url": event_item.get("url")
        })

    return formatted_events


# ===== Fetch Event Detail =====
def fetch_event_detail(event_id):

    query_params = {
        "apikey": API_KEY
    }

    encoded_params = urllib.parse.urlencode(query_params)

    url = (
        "https://app.ticketmaster.com"
        f"/discovery/v2/events/{event_id}.json?{encoded_params}"
    )

    print("Detail URL:", url)

    with urllib.request.urlopen(url) as api_response:

        event_item = json.loads(
            api_response.read().decode("utf-8")
        )

    # ===== Venue =====
    venue_data = {}

    embedded = event_item.get("_embedded", {})

    venues = embedded.get("venues", [])

    if venues:

        venue = venues[0]

        location = venue.get("location", {})

        country = venue.get("country", {})

        venue_data = {
            "name": venue.get("name"),

            "address": (
                venue.get("address", {})
                .get("line1")
            ),

            "city": (
                venue.get("city", {})
                .get("name")
            ),

            "country": country.get("countryCode"),

            "latitude": location.get("latitude"),

            "longitude": location.get("longitude")
        }

    # ===== Images =====
    images = []

    for image in event_item.get("images", []):

        images.append({
            "url": image.get("url"),

            "width": image.get("width"),

            "height": image.get("height")
        })

    # ===== Classification =====
    classification = None

    classifications = event_item.get("classifications", [])

    if classifications:

        segment = classifications[0].get("segment", {})

        classification = segment.get("name")

    # ===== Price Range =====
    price_data = None

    price_ranges = event_item.get("priceRanges", [])

    if price_ranges:

        price = price_ranges[0]

        price_data = {
            "min": price.get("min"),

            "max": price.get("max"),

            "currency": price.get("currency")
        }

    return {
        "id": event_item.get("id"),

        "name": event_item.get("name"),

        "description": event_item.get("info"),

        "pleaseNote": event_item.get("pleaseNote"),

        "date": (
            event_item.get("dates", {})
            .get("start", {})
            .get("localDate")
        ),

        "classification": classification,

        "priceRanges": price_data,

        "venue": venue_data,

        "accessibility": event_item.get("accessibility"),

        "images": images,

        "ticketUrl": event_item.get("url"),

        "distance": event_item.get("distance"),

        "source": "Ticketmaster"
    }


# ===== Local Event Filter =====
def is_relevant_event(event_item):

    name = (event_item.get("name") or "").lower()

    classification = (
        event_item.get("classification") or ""
    ).lower()

    venue = (event_item.get("venue") or "").lower()

    combined_text = (
        f"{name} {classification} {venue}"
    )

    # ===== Exclude Bad Results =====
    for excluded_word in EXCLUDED_WORDS:

        if excluded_word in combined_text:
            return False

    # ===== Local Elderly Keyword Filter =====
    for keyword in FILTER_KEYWORDS:

        if keyword.lower() in combined_text:
            return True

    return True


# ===== Lambda Entry =====
def lambda_handler(event, context):

    try:

        path = event.get("rawPath", "")

        # ==================================================
        # GET /events/{id}
        # ==================================================
        if path.startswith("/events/"):

            event_id = (
                event.get("pathParameters", {})
                .get("id")
            )

            if not event_id:

                return response(400, {
                    "error": "Missing event id"
                })

            detail = fetch_event_detail(event_id)

            return response(200, detail)

        # ==================================================
        # GET /events
        # ==================================================
        params = event.get("queryStringParameters") or {}

        lat = float(params.get("lat", DEFAULT_LAT))

        lng = float(params.get("lng", DEFAULT_LNG))

        limit = int(params.get("limit", DEFAULT_LIMIT))

        user_keyword = params.get("keyword")

        all_events = []

        seen_ids = set()
        seen_events = set()

        # ===== User Filter =====
        if user_keyword:

            keywords = [user_keyword]

            fetch_limit = limit

        # ===== Default Mixed Recommendation =====
        else:

            keywords = SEARCH_KEYWORDS

            fetch_limit = PER_KEYWORD_LIMIT

        # ===== Fetch Events =====
        for keyword in keywords:

            time.sleep(0.5)

            events = fetch_events(
                lat,
                lng,
                fetch_limit,
                keyword
            )

            for event_item in events:

                # ===== Distance Filter =====
                distance = event_item.get("distance")

                if (
                    distance is not None
                    and distance > MAX_DISTANCE_KM
                ):
                    continue

                # ===== Australia Only Filter =====
                country = event_item.get("country")

                if country != AU_COUNTRY_CODE:
                    continue

                # ===== Local Filter =====
                if not is_relevant_event(event_item):
                    continue

                event_id = event_item.get("id")

                # ===== Exact ID Deduplicate =====
                if event_id in seen_ids:
                    continue

                # ===== Smart Deduplicate =====
                event_key = (
                    (event_item.get("name") or "").strip().lower(),
                    (event_item.get("venue") or "").strip().lower()
                )

                if event_key in seen_events:
                    continue

                seen_ids.add(event_id)
                seen_events.add(event_key)

                all_events.append(event_item)

        # ===== Final Limit =====
        all_events = all_events[:limit]

        return response(200, {
            "events": all_events,
            "total": len(all_events)
        })

    except ValueError:

        return response(400, {
            "error": "Invalid query parameters"
        })

    except Exception as e:

        print("ERROR:", e)

        return response(500, {
            "error": str(e)
        })