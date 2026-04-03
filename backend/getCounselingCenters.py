import json
import math
import urllib.request


# Toggle mock mode (True = use mock data, False = call real API)
USE_MOCK = True


# Build a standard response (ensures headers are always included)
def build_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_dict)
    }


# Calculate distance using Haversine formula (in meters)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# Fetch data from teammate API
def fetch_centers_from_api():
    url = "https://api-url/counseling-centers"  # TODO: replace

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())

        return {
            "success": True,
            "data": data.get("data", [])
        }

    except Exception as e:
        print("ERROR: Failed to fetch counseling centers API:", str(e))
        return {
            "success": False,
            "data": []
        }


def lambda_handler(event, context):

    # 1. Extract query parameters safely
    params = event.get("queryStringParameters", {}) or {}

    # 2. Validate required parameters
    if not params.get("lat") or not params.get("lng"):
        return build_response(400, {
            "status": "error",
            "message": "Missing user's location (lat/lng)"
        })

    # 3. Convert parameters to float
    try:
        user_lat = float(params.get("lat"))
        user_lng = float(params.get("lng"))
    except ValueError:
        return build_response(400, {
            "status": "error",
            "message": "Invalid lat/lng, coordinates must be numbers"
        })

    # 4. Get data source (mock or API)
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
        api_result = fetch_centers_from_api()

        # External API failure
        if not api_result["success"]:
            return build_response(500, {
                "status": "error",
                "message": "Failed to fetch data from upstream service"
            })

        centers = api_result["data"]

    # 4.5 Database is empty (API succeeded but no records exist)
    if not centers:
        print("WARNING: Database returned empty dataset")

        return build_response(200, {
            "status": "success",
            "data": [],
            "message": "No counseling centers exist in the database."
        })

    # 5. Calculate distance
    result = []

    for c in centers:
        try:
            lat = float(c["latitude"])
            lng = float(c["longitude"])
        except (TypeError, ValueError, KeyError):
            continue  # skip invalid records

        distance = calculate_distance(user_lat, user_lng, lat, lng)

        item = c.copy()
        item["distance_meters"] = round(distance)
        item["distance_km"] = round(distance / 1000, 2)

        result.append(item)

    # 6. Filtering result is empty (valid case)
    if not result:
        print("INFO: No centers matched after filtering")

        return build_response(200, {
            "status": "success",
            "data": [],
            "message": "No counseling centers found"
        })

    # 7. Sort by distance (ascending)
    result.sort(key=lambda x: x["distance_meters"])

    # 8. Limit results
    LIMIT = 10
    result = result[:LIMIT]

    # 9. Return success response
    return build_response(200, {
        "status": "success",
        "data": result
    })