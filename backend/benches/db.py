"""
Database operations for the benches API.
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor

# global use: for reuse connection
conn = None


def get_connection():
    global conn

    try:
        # If no connection or connection is closed → reconnect
        if conn is None or conn.closed != 0:
            conn = psycopg2.connect(
                host=os.environ['DB_HOST'],
                database=os.environ['DB_NAME'],
                user=os.environ['DB_USER'],
                password=os.environ['DB_PASSWORD'],
                port=5432,
                connect_timeout=5
            )
    except Exception as e:
        print("DB connection error:", str(e))
        raise e

    return conn

def get_benches_in_bbox(min_lat, max_lat, min_lng, max_lng):
    conn = get_connection()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    description,
                    type,
                    condition,
                    latitude,
                    longitude
                FROM public_benches
                WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326);
            """, (min_lng, min_lat, max_lng, max_lat))

            return cur.fetchall()

    except Exception as e:
        print("BBox query error:", str(e))
        raise e