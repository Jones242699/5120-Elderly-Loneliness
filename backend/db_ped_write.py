import psycopg2
import os
from datetime import datetime

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


def upsert_pedestrian_data(sensor_data):
    """
    sensor_data: dict
    {
        sensor_id: weighted_volume
    }
    """

    conn = get_connection()
    cursor = conn.cursor()

    for sensor_id, value in sensor_data.items():
        cursor.execute("""
            INSERT INTO pedestrian_data (sensor_id, weighted_volume, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (sensor_id)
            DO UPDATE SET
                weighted_volume = EXCLUDED.weighted_volume,
                updated_at = EXCLUDED.updated_at
        """, (
            sensor_id,
            value,
            datetime.utcnow()
        ))

    conn.commit()
    cursor.close()