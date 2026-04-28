import json
from db import get_places, get_place_by_id


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
        # /places
        if path == "/places":
            return get_places_list(event)

        # /places/{id}
        elif path.startswith("/places/"):
            place_id = event.get("pathParameters", {}).get("id")
            if not place_id:
                return response(400, {"error": "Missing place id"})
            return get_place_detail(place_id)

        else:
            return response(404, {"error": "Not Found"})

    except Exception as e:
        print("ERROR:", e)
        return response(500, {"error": str(e)})


# ===== API: List Places =====
def get_places_list(event):
    params = event.get("queryStringParameters") or {}

    try:
        lat = float(params.get("lat", DEFAULT_LAT))
        lng = float(params.get("lng", DEFAULT_LNG))
        radius = float(params.get("radius", 5000))  # meters
        limit = int(params.get("limit", 20))
    except ValueError:
        return response(400, {"error": "Invalid query parameters"})

    category = params.get("category")

    rows = get_places(lat, lng, radius, limit, category)

    return response(200, {
        "places": rows,
        "total": len(rows)
    })


# ===== API: Place Detail =====
def get_place_detail(place_id):
    row = get_place_by_id(place_id)

    if not row:
        return response(404, {"error": "Place not found"})

    return response(200, row)