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


def get_nearby_sensor_volumes(lat, lng):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            p.sensor_id,
            p.weighted_volume
        FROM pedestrian_data p
        JOIN sensor_locations s
        ON p.sensor_id = s.location_id
        WHERE ST_DistanceSphere(
            ST_MakePoint(s.longitude, s.latitude),
            ST_MakePoint(%s, %s)
        ) <= 500
    """, (lng, lat))

    rows = cursor.fetchall()
    cursor.close()

    return rows