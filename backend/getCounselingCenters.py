import json
import math


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


def lambda_handler(event, context):

    # 1. Extract query parameters safely
    params = event.get("queryStringParameters", {}) or {}

    # 2. Validate required parameters
    if not params.get("lat") or not params.get("lng"):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing lat/lng"})
        }

    # 3. Convert parameters to float
    try:
        user_lat = float(params.get("lat"))
        user_lng = float(params.get("lng"))
    except ValueError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid lat/lng"})
        }

    # 4. Mock data (to be replaced by database or external API)
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

    # 5. Calculate distance and build result list
    result = []

    for c in centers:
        distance = calculate_distance(
            user_lat,
            user_lng,
            c["latitude"],
            c["longitude"]
        )

        item = c.copy()
        item["distance_meters"] = round(distance)
        item["distance_km"] = round(distance / 1000, 2)

        result.append(item)

    # 6. Sort by distance (ascending)
    result.sort(key=lambda x: x["distance_meters"])

    # 7. Return response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "status": "success",
            "data": result
        })
    }