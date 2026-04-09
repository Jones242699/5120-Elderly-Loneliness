import json
import math
from db import get_nearby_trees


SAMPLE_STEP = 5
MAX_SHADE = 500


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def normalize_log(value):
    if value <= 0:
        return 0

    return min(
        100,
        math.log(1 + value) / math.log(1 + MAX_SHADE) * 100
    )


def calculate_shade_score(path):

    if not path:
        return 0

    # sample points
    sampled_points = path[::SAMPLE_STEP]

    if not sampled_points:
        return 0

    total_area = 0

    # deduplicate trees
    seen_tree_ids = set()

    for point in sampled_points:
        lat = point["lat"]
        lng = point["lng"]

        trees = get_nearby_trees(lat, lng)
        # print("Trees found:", len(trees))
        for t in trees:
            tree_id = t["canopy_id"]

            if tree_id not in seen_tree_ids:
                seen_tree_ids.add(tree_id)
                total_area += float(t.get("canopy_area") or 0)

    # average
    avg_area = total_area / len(sampled_points)

    # log normalization
    score = normalize_log(avg_area)

    return round(score, 2)


def lambda_handler(event, context):

    try:
        body = json.loads(event.get("body", "{}"))
        routes = body.get("routes", [])

        if not routes:
            return build_response(400, {
                "error": "No routes provided"
            })

        results = []

        for route in routes:
            route_id = route.get("id")
            path = route.get("path", [])

            score = calculate_shade_score(path)

            results.append({
                "id": route_id,
                "shadeScore": score
            })

        return build_response(200, {
            "results": results
        })

    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {
            "error": "Internal server error"
        })