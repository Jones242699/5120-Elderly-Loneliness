"""
AWS Lambda handler for the crowd-density API.
Returns live pedestrian volume data for map overlays.
"""

import json
from db import get_nearby_sensor_volumes

DEFAULT_LAT = -37.8136
DEFAULT_LNG = 144.9631
DEFAULT_RADIUS = 2000


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def get_volume_level(volume):

    if volume < 10:
        return "quiet"

    elif volume < 20:
        return "moderate"

    return "busy"


def lambda_handler(event, context):

    try:

        params = event.get("queryStringParameters") or {}

        try:
            lat = float(params.get("lat", DEFAULT_LAT))
            lng = float(params.get("lng", DEFAULT_LNG))
            radius = int(params.get("radius", DEFAULT_RADIUS))

        except ValueError:
            return build_response(400, {
                "error": "Invalid query parameters"
            })

        rows = get_nearby_sensor_volumes(lat, lng, radius)

        results = []

        for row in rows:

            sensor_id = row[0]
            sensor_lat = row[1]
            sensor_lng = row[2]
            volume = float(row[3])

            results.append({
                "sensor_id": sensor_id,
                "lat": sensor_lat,
                "lng": sensor_lng,
                "volume": volume,
                "level": get_volume_level(volume)
            })

        return build_response(200, {
            "results": results
        })

    except Exception as e:

        print("Error:", str(e))

        return build_response(500, {
            "error": "Internal server error"
        })