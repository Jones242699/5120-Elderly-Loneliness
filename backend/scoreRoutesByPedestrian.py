import json
import math
from db import get_nearby_sensor_volumes

MAX_DENSITY = 2000


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def calculate_social_score(path):
    if not path:
        return 0

    sensor_map = {}

    for point in path:
        lat = point.get("lat")
        lng = point.get("lng")

        if lat is None or lng is None:
            continue

        try:
            rows = get_nearby_sensor_volumes(lat, lng)
        except Exception as db_error:
            print("DB error:", str(db_error))
            rows = []

        for row in rows:
            sensor_id = row[0]
            volume = float(row[1])

            if sensor_id not in sensor_map:
                sensor_map[sensor_id] = volume
            else:
                sensor_map[sensor_id] = max(sensor_map[sensor_id], volume)

    if len(path) > 0:
        density = sum(sensor_map.values()) / len(path)
    else:
        density = 0

    # log normalization + clamp
    if density <= 0:
        score = 0
    else:
        score = min(
            100,
            math.log(density + 1) / math.log(MAX_DENSITY + 1) * 100
        )

    return round(score, 2)


def lambda_handler(event, context):
    try:
        body = event.get("body", {})

        if isinstance(body, str):
            body = json.loads(body)

        routes = body.get("routes", [])

        if not routes:
            return build_response(400, {
                "error": "No routes provided"
            })

        results = []

        for i, route in enumerate(routes):

            if isinstance(route, list):
                path = route
                route_id = i
            else:
                path = route.get("path", [])
                route_id = route.get("id", i)

            score = calculate_social_score(path)

            results.append({
                "id": route_id,
                "socialScore": score
            })

        return build_response(200, {
            "results": results
        })

    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {
            "error": "Internal server error"
        })