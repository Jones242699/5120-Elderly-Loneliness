"""
AWS Lambda handler for the counseling API.
Processes requests to find nearby counseling centers based on latitude, longitude, and radius.
"""
import json
from db import get_nearby_counseling_centers


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body)
    }

def format_hours(value):
    return value if value else "Closed"


def lambda_handler(event, context):

    try:
        params = event.get("queryStringParameters") or {}

        lat = params.get("lat")
        lng = params.get("lng")
        radius = params.get("radius", 5000)

        if not lat or not lng:
            return build_response(400, {
                "error": "Missing required parameters: lat, lng"
            })

        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return build_response(400, {
                "error": "Invalid parameter format"
            })

        centers = get_nearby_counseling_centers(lat, lng, radius)

        result = []

        for c in centers:
            result.append({
                "id": int(c["id"]) if c.get("id") is not None else None,
                "name": c.get("name"),
                "address": c.get("address"),
                "latitude": float(c["latitude"]),
                "longitude": float(c["longitude"]),
                "distance_meters": round(c["distance"]),
                "rating": float(c["google_rating"]) if c.get("google_rating") else None,
                "phone": c.get("phone"),
                "website": c.get("website"),
                "open_hours": {
                    "monday": format_hours(c.get("monday_open_hours")),
                    "tuesday": format_hours(c.get("tuesday_open_hours")),
                    "wednesday": format_hours(c.get("wednesday_open_hours")),
                    "thursday": format_hours(c.get("thursday_open_hours")),
                    "friday": format_hours(c.get("friday_open_hours")),
                    "saturday": format_hours(c.get("saturday_open_hours")),
                    "sunday": format_hours(c.get("sunday_open_hours"))
                }
            })

        return build_response(200, {
            "status": "success",
            "count": len(result),
            "data": result
        })

    except Exception as e:
        print("Lambda error:", str(e))
        return build_response(500, {
            "error": "Internal server error"
        })