import json
from db import get_benches_in_bbox


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):

    # 1. Get query parameters
    params = event.get("queryStringParameters") or {}

    min_lat = params.get("minLat")
    max_lat = params.get("maxLat")
    min_lng = params.get("minLng")
    max_lng = params.get("maxLng")

    # 2. Validate parameters existence
    if not all([min_lat, max_lat, min_lng, max_lng]):
        return build_response(400, {
            "error": "Missing required parameters: minLat, maxLat, minLng, maxLng"
        })

    # 3. Convert to float
    try:
        min_lat = float(min_lat)
        max_lat = float(max_lat)
        min_lng = float(min_lng)
        max_lng = float(max_lng)
    except ValueError:
        return build_response(400, {
            "error": "Invalid parameter format. Must be numbers."
        })

    try:
        # 4. Query database
        benches = get_benches_in_bbox(min_lat, max_lat, min_lng, max_lng)

        # 5. Format response
        result = []
        for b in benches:
            result.append({
                "id": int(b["id"]) if b.get("id") else None,
                "description": b.get("description"),
                "type": b.get("type"),
                "condition": float(b["condition"]) if b.get("condition") else None,
                "latitude": float(b["latitude"]),
                "longitude": float(b["longitude"])
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