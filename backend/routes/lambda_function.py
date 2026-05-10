import json
import os
import urllib.parse
import urllib.request

GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]

API_BASE_URL = "https://mk3ban19bb.execute-api.ap-southeast-2.amazonaws.com"


def decode_polyline(encoded):

    points = []

    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):

        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5

            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5

            if b < 0x20:
                break

        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        points.append({
            "lat": lat / 1e5,
            "lng": lng / 1e5
        })

    return points


def lambda_handler(event, context):

    try:

        body = json.loads(event.get("body", "{}"))

        start = body.get("start")
        destination = body.get("destination")
        travel_mode = body.get("travelMode", "WALKING")

        if not start or not destination:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({
                    "error": "start and destination are required"
                })
            }

        # ===== Google Directions API =====

        params = {
            "origin": f"{start['lat']},{start['lng']}",
            "destination": f"{destination['lat']},{destination['lng']}",
            "mode": travel_mode.lower(),
            "alternatives": "true",
            "key": GOOGLE_MAPS_API_KEY
        }

        url = (
            "https://maps.googleapis.com/maps/api/directions/json?"
            + urllib.parse.urlencode(params)
        )

        with urllib.request.urlopen(url) as response:
            directions_data = json.loads(response.read())

        routes = directions_data.get("routes", [])

        # ===== Decode route polylines =====

        scoring_routes = []

        for route in routes:

            polyline = route["overview_polyline"]["points"]

            decoded_path = decode_polyline(polyline)

            scoring_routes.append(decoded_path)

        # ===== Call Shade Score API =====

        shade_request = urllib.request.Request(
            f"{API_BASE_URL}/score/shade",
            data=json.dumps({
                "routes": scoring_routes
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(shade_request) as response:
            shade_data = json.loads(response.read())

        # ===== Call Pedestrian Score API =====

        pedestrian_request = urllib.request.Request(
            f"{API_BASE_URL}/score/pedestrian",
            data=json.dumps({
                "routes": scoring_routes
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(pedestrian_request) as response:
            pedestrian_data = json.loads(response.read())

        shade_scores = shade_data.get("results", [])
        pedestrian_scores = pedestrian_data.get("results", [])

        # ===== Build score maps =====

        shade_score_map = {
            item["id"]: item["shadeScore"]
            for item in shade_scores
        }

        social_score_map = {
            item["id"]: item["socialScore"]
            for item in pedestrian_scores
        }

        # ===== Merge scores =====

        formatted_routes = []

        for idx, route in enumerate(routes):

            leg = route["legs"][0]

            shade_score = shade_score_map.get(idx, 0)

            social_score = social_score_map.get(idx, 0)

            overall_score = round(
                (shade_score + social_score) / 2,
                2
            )

            formatted_routes.append({
                "id": idx,
                "summary": route.get("summary"),
                "distance": leg["distance"],
                "duration": leg["duration"],
                "polyline": route["overview_polyline"]["points"],
                "shadeScore": shade_score,
                "socialScore": social_score,
                "overallScore": overall_score
            })

        # ===== Sort routes =====

        formatted_routes.sort(
            key=lambda r: r["overallScore"],
            reverse=True
        )

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "routes": formatted_routes
            })
        }

    except Exception as e:

        print("Error:", str(e))

        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({
                "error": str(e)
            })
        }


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }