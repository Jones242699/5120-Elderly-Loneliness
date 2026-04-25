import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor


# Default location (Melbourne CBD)
DEFAULT_LAT = -37.8136
DEFAULT_LNG = 144.9631


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )


def lambda_handler(event, context):
    path = event.get("resource")

    try:
        if path == "/places":
            return get_places_list(event)

        elif path == "/places/{id}":
            place_id = event["pathParameters"]["id"]
            return get_place_detail(place_id)

        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Not Found"})
            }

    except Exception as e:
        print("ERROR:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# API List (with distance + filter)
def get_places_list(event):
    params = event.get("queryStringParameters") or {}

    lat = float(params.get("lat", DEFAULT_LAT))
    lng = float(params.get("lng", DEFAULT_LNG))
    radius = float(params.get("radius", 5000))   # meters
    limit = int(params.get("limit", 20))
    category = params.get("category")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT 
            id,
            name,
            type AS category,
            address,
            latitude,
            longitude,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance
        FROM public_artworks
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        )
    """

    params_list = [lng, lat, lng, lat, radius]

    # category filter
    if category:
        query += " AND type = %s"
        params_list.append(category)

    query += " ORDER BY distance LIMIT %s"
    params_list.append(limit)

    cursor.execute(query, tuple(params_list))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "places": rows,
            "total": len(rows)
        })
    }


# API Detail
def get_place_detail(place_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT 
            id,
            name,
            type AS category,
            address,
            artist,
            year,
            description,
            latitude,
            longitude
        FROM public_artworks
        WHERE id = %s;
    """

    cursor.execute(query, (place_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Place not found"})
        }

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(row)
    }