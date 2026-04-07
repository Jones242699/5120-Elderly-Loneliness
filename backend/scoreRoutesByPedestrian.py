import json
import math
from db import get_nearby_sensor_volumes

MAX_DENSITY = 2000


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        routes = body.get("routes", [])

        if not routes:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No routes provided"})
            }

        results = []

        # go over each route
        for route_idx, route in enumerate(routes):

            sensor_map = {}  # use to deduplicate sensor_id

            # go over each point on the route
            for point in route:
                lat = point.get("lat")
                lng = point.get("lng")

                # skip abnormal points
                if lat is None or lng is None:
                    continue

                try:
                    rows = get_nearby_sensor_volumes(lat, lng)
                except Exception as db_error:
                    print("DB error:", str(db_error))
                    rows = []

                # rows: [(sensor_id, volume), ...]
                for row in rows:
                    sensor_id = row[0]
                    volume = float(row[1])

                    # deduplicate + keep max value (avoid duplicate point accumulation)
                    if sensor_id not in sensor_map:
                        sensor_map[sensor_id] = volume
                    else:
                        sensor_map[sensor_id] = max(sensor_map[sensor_id], volume)

            # density average (avoid route length impact)
            if len(route) > 0:
                density = sum(sensor_map.values()) / len(route)
            else:
                density = 0

            # score calculation
            score = math.log(density + 1) / math.log(MAX_DENSITY + 1) * 100

            results.append({
                "id": route_idx,
                "socialScore": round(score, 2)
            })

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "results": results
            })
        }

    except Exception as e:
        print("Error:", str(e))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }