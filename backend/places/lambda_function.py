import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor


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
            return get_places_list()

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


# API List (for cards)
def get_places_list():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT 
            id,
            name,
            type AS category,
            address,
            latitude,
            longitude
        FROM public_artworks
        LIMIT 50;
    """

    cursor.execute(query)
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


# API Detail (after clicking cards)
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