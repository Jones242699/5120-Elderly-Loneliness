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


def get_nearby_trees(lat, lng, radius=15):
    """
    Query trees near a point (returns canopy_area)
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT canopy_id, canopy_area
        FROM tree_canopies_cleaned
        WHERE ST_DWithin(
            geom,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326),
            %s
        )
    """

    cursor.execute(query, (lng, lat, radius))
    rows = cursor.fetchall()

    cursor.close()
    return rows