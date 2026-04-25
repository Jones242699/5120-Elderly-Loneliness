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
    try:
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
            "body": json.dumps(rows)
        }

    except Exception as e:
        print("ERROR:", e)

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }