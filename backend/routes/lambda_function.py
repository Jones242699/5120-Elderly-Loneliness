import json
import os
import urllib.parse
import urllib.request

GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]


def lambda_handler(event, context):

    try:
        body = json.loads(event.get("body", "{}"))

        origin = body.get("origin")
        destination = body.get("destination")
        travel_mode = body.get("travelMode", "WALKING")

        if not origin or not destination:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({
                    "error": "origin and destination are required"
                })
            }

        # ===== Google Directions API =====
        params = {
            "origin": f"{origin['lat']},{origin['lng']}",
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

        print(directions_data)

        routes = directions_data.get("routes", [])

        formatted_routes = []

        for idx, route in enumerate(routes):

            leg = route["legs"][0]

            formatted_routes.append({
                "id": idx,
                "summary": route.get("summary"),
                "distance": leg["distance"],
                "duration": leg["duration"],
                "polyline": route["overview_polyline"]["points"]
            })

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "routes": formatted_routes
            })
        }

    except Exception as e:

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