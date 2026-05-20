"""
Database operations for the venues API.
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor

# global connection
conn = None


def get_connection():
    global conn

    try:
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


def get_venues(lat, lng, radius, limit, category=None):
    conn = get_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = """
            SELECT
                id,
                name,
                address,
                suburb,
                category,
                seating_type,
                seats,
                latitude,
                longitude,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance
            FROM cafes
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
        """

        params = [lng, lat, lng, lat, radius]

        if category:
            query += " AND category = %s"
            params.append(category)

        query += " ORDER BY distance LIMIT %s"
        params.append(limit)

        cur.execute(query, tuple(params))
        return cur.fetchall()


def get_venue_by_id(venue_id):
    conn = get_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                id,
                name,
                address,
                suburb,
                category,
                seating_type,
                seats,
                latitude,
                longitude
            FROM cafes
            WHERE id = %s;
        """, (venue_id,))

        return cur.fetchone()