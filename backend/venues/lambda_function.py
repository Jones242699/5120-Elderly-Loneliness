"""
AWS Lambda handler for the venues API.
Serves endpoints for listing nearby venues and retrieving detailed information about a specific venue.
"""
import json
from db import get_venues, get_venue_by_id


# ===== Default location (Melbourne CBD) =====
DEFAULT_LAT = -37.8136
DEFAULT_LNG = 144.9631


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


# ===== Lambda Entry =====
def lambda_handler(event, context):
    path = event.get("rawPath", "")

    try:
        # /venues
        if path == "/venues":
            return get_venues_list(event)

        # /venues/{id}
        elif path.startswith("/venues/"):
            venue_id = event.get("pathParameters", {}).get("id")

            if not venue_id:
                return response(400, {"error": "Missing venue id"})

            return get_venue_detail(venue_id)

        else:
            return response(404, {"error": "Not Found"})

    except Exception as e:
        print("ERROR:", e)
        return response(500, {"error": str(e)})


# ===== API: List Venues =====
def get_venues_list(event):
    params = event.get("queryStringParameters") or {}

    try:
        lat = float(params.get("lat", DEFAULT_LAT))
        lng = float(params.get("lng", DEFAULT_LNG))
        radius = float(params.get("radius", 3000))
        limit = int(params.get("limit", 20))
    except ValueError:
        return response(400, {"error": "Invalid query parameters"})

    category = params.get("category")

    rows = get_venues(lat, lng, radius, limit, category)

    return response(200, {
        "venues": rows,
        "total": len(rows)
    })


# ===== API: Venue Detail =====
def get_venue_detail(venue_id):
    row = get_venue_by_id(venue_id)

    if not row:
        return response(404, {"error": "Venue not found"})

    return response(200, row)