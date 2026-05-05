"""
Database operations for the counseling API.
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor

conn = None


def get_connection():
    global conn

    if conn is None or conn.closed != 0:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=5432,
            connect_timeout=5
        )

    return conn


def get_nearby_counseling_centers(lat, lng, radius):
    conn = get_connection()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    name,
                    address,
                    latitude,
                    longitude,
                    google_rating,
                    phone,
                    website,
                    monday_open_hours,
                    tuesday_open_hours,
                    wednesday_open_hours,
                    thursday_open_hours,
                    friday_open_hours,
                    saturday_open_hours,
                    sunday_open_hours,

                    -- calculate distance in meters
                    ST_Distance(
                        geom,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    ) AS distance

                FROM mental_health_services

                WHERE ST_DWithin(
                    geom,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s
                )

                ORDER BY distance ASC;
            """, (lng, lat, lng, lat, radius))

            return cur.fetchall()

    except Exception as e:
        print("Query error:", str(e))
        raise e