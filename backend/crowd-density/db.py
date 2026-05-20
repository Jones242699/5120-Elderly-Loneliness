"""
Database operations for the crowd-density API.
"""

import psycopg2
import os

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


def get_all_sensor_volumes():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.location_id,
            s.latitude,
            s.longitude,
            p.weighted_volume,
            p.updated_at
        FROM pedestrian_data p
        JOIN sensor_locations s
        ON p.sensor_id = s.location_id
    """)

    rows = cursor.fetchall()

    cursor.close()

    return rows


def get_nearby_sensor_volumes(lat, lng, radius, limit):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.location_id,
            s.latitude,
            s.longitude,
            p.weighted_volume,

            ST_DistanceSphere(
                ST_MakePoint(s.longitude, s.latitude),
                ST_MakePoint(%s, %s)
            ) AS distance

        FROM pedestrian_data p

        JOIN sensor_locations s
        ON p.sensor_id = s.location_id

        WHERE ST_DistanceSphere(
            ST_MakePoint(s.longitude, s.latitude),
            ST_MakePoint(%s, %s)
        ) <= %s

        ORDER BY distance ASC

        LIMIT %s
    """, (
        lng,
        lat,
        lng,
        lat,
        radius,
        limit
    ))

    rows = cursor.fetchall()

    cursor.close()

    return rows