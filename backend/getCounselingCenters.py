import json
import math
from db import get_counseling_centers  # Add


# Toggle mock mode
USE_MOCK = True


def build_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_dict)
    }


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def lambda_handler(event, context):

    # 1. Extract params
    params = event.get("queryStringParameters", {}) or {}

    if not params.get("lat") or not params.get("lng"):
        return build_response(400, {
            "status": "error",
            "message": "Missing user's location (lat/lng)"
        })

    try:
        user_lat = float(params.get("lat"))
        user_lng = float(params.get("lng"))
    except ValueError:
        return build_response(400, {
            "status": "error",
            "message": "Invalid lat/lng"
        })

    # 2. Data source
    if USE_MOCK:
        centers = [
            {
                "id": "3",
                "name": "Federation Square Cafe",
                "address": "Flinders Street, Melbourne VIC 3000",
                "latitude": -37.8124,
                "longitude": 144.9678
            },
            {
                "id": "4",
                "name": "South Yarra Market Hall",
                "address": "240 Chapel Street, South Yarra VIC 3141",
                "latitude": -37.8408,
                "longitude": 144.9996
            }
        ]
    else:
        try:
            centers = get_counseling_centers()  # Fetch from database
        except Exception as e:
            print("ERROR: DB query failed:", str(e))
            return build_response(500, {
                "status": "error",
                "message": "Database query failed"
            })

    # 3. Empty DB
    if not centers:
        print("WARNING: No data in database")

        return build_response(200, {
            "status": "success",
            "data": [],
            "message": "No counseling centers exist in the database."
        })

    # 4. Calculate distance
    result = []

    for c in centers:
        try:
            lat = float(c["latitude"])
            lng = float(c["longitude"])
        except (TypeError, ValueError, KeyError):
            continue

        distance = calculate_distance(user_lat, user_lng, lat, lng)

        item = dict(c)
        item["distance_meters"] = round(distance)
        item["distance_km"] = round(distance / 1000, 2)

        result.append(item)

    # 5. Filter empty
    if not result:
        print("INFO: No centers matched after filtering")

        return build_response(200, {
            "status": "success",
            "data": [],
            "message": "No counseling centers found"
        })

    # 6. Sort + limit
    result.sort(key=lambda x: x["distance_meters"])
    result = result[:10]

    # 7. Return
    return build_response(200, {
        "status": "success",
        "data": result
    })