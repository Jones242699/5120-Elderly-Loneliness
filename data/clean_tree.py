"""
Clean two Urban Forest datasets:
1. tree canopies
2. trees with species and diameter data

Output files:
1. tree_canopies_2021_cleaned.csv
2. urban_trees_species_cleaned.csv
"""

import csv
import json
import math
import sys

csv.field_size_limit(sys.maxsize)

# Convert a geo point string into latitude and longitude floats.
def parse_geo_point(value):
    lat_text, lon_text = [part.strip() for part in value.split(",", 1)]
    latitude = float(lat_text)
    longitude = float(lon_text)

    # Check that the values are within valid ranges.
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude}")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude: {longitude}")

    return latitude, longitude

# Calculate the area of tree canopy polygons in square meters.
def project_to_meters(longitude, latitude):
    """
    The raw GeoJSON stores coordinates in longitude/latitude degrees.
    To calculate polygon area, we first convert them into approximate meters.
    This uses a simple local projection around Melbourne.
    """
    earth_radius = 6371000
    melbourne_lat = math.radians(-37.8136)

    x = earth_radius * math.radians(longitude) * math.cos(melbourne_lat)
    y = earth_radius * math.radians(latitude)
    return x, y

# Calculate one polygon ring's area
# referenced from https://math.stackexchange.com/questions/3926443/whats-the-difference-between-picks-formula-and-the-shoelace-formulagausses-f#:~:text=1-,But%20what's%20the%20difference?,formula%20is%20trivial%20to%20implement.
def ring_area(ring):
    
    if len(ring) < 3:
        return 0.0

    points = []
    for point in ring:
        longitude = point[0]
        latitude = point[1]
        points.append(project_to_meters(longitude, latitude))

    total = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        total += (x1 * y2) - (x2 * y1)

    return abs(total) / 2.0

# Calculate one polygon's area, accounting for holes if any.
# canopy_area = outer area - hole areas
def polygon_area(polygon):
    
    if not polygon:
        return 0.0

    outer_area = ring_area(polygon[0])
    holes_area = 0.0

    for hole in polygon[1:]:
        holes_area += ring_area(hole)

    return max(outer_area - holes_area, 0.0)

# Calculate canopy area from the GeoJSON shape.
# If the shape is Polygon, calculate one polygon's area
# If the shape is MultiPolygon, add each polygon's area together
def geometry_area(geometry):
    geometry_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        return polygon_area(coordinates)

    if geometry_type == "MultiPolygon":
        total_area = 0.0
        for polygon in coordinates:
            total_area += polygon_area(polygon)
        return total_area

    raise ValueError(f"Unsupported geometry type: {geometry_type}")


def clean_tree_canopies():
    input_path = "data/raw/tree-canopies-2021-urban-forest.csv"
    output_path = "data/cleaned/tree_canopies_2021_cleaned.csv"

    cleaned_rows = []
    seen_keys = set()
    skipped_rows = 0

    with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_number, row in enumerate(reader, start=1):
            try:
                geo_point = (row.get("Geo Point") or "").strip()
                geo_shape = (row.get("Geo Shape") or "").strip()

                # filter out rows with missing geo point or geo shape
                if not geo_point or not geo_shape:
                    skipped_rows += 1
                    continue
                
                # parse geo point into latitude and longitude
                latitude, longitude = parse_geo_point(geo_point)
                geometry = json.loads(geo_shape)
                geometry_type = geometry.get("type", "").strip()

                if geometry_type not in {"Polygon", "MultiPolygon"}:
                    skipped_rows += 1
                    continue

                normalized_shape = json.dumps(
                    geometry,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )

                # Calculate area of the tree canopy polygon in square meters.
                canopy_area = round(geometry_area(geometry), 3)

                # Calculate canopy diameter in meters, assuming the canopy is circular.
                canopy_diameter = None
                if canopy_area > 0:
                    canopy_diameter = round(2 * math.sqrt(canopy_area / math.pi), 3)

                # remove duplicates based on latitude, longitude, and geo shape
                dedupe_key = (latitude, longitude, normalized_shape)
                if dedupe_key in seen_keys:
                    skipped_rows += 1
                    continue

                seen_keys.add(dedupe_key)
                
                cleaned_rows.append(
                    {
                        "canopy_id": row_number,
                        "latitude": latitude,
                        "longitude": longitude,
                        "canopy_area": canopy_area,
                        "canopy_diameter": canopy_diameter,
                        "geo_shape": normalized_shape,
                    }
                )
            except (ValueError, json.JSONDecodeError, IndexError, TypeError):
                skipped_rows += 1

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "canopy_id",
                "latitude",
                "longitude",
                "canopy_area",
                "canopy_diameter",
                "geo_shape",
            ],
        )
        writer.writeheader()
        writer.writerows(cleaned_rows)


def clean_urban_trees_species():
    input_path = "data/raw/trees-with-species-and-dimensions-urban-forest.csv"
    output_path = "data/cleaned/urban_trees_species_cleaned.csv"

    cleaned_rows = []
    seen_tree_ids = set()
    skipped_rows = 0

    with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                tree_id_text = (row.get("CoM ID") or "").strip()
                scientific_name = (row.get("Scientific Name") or "").strip()
                diameter_text = (row.get("Diameter Breast Height") or "").strip()
                latitude_text = (row.get("Latitude") or "").strip()
                longitude_text = (row.get("Longitude") or "").strip()

                # filter out rows with missing fields: tree ID, latitude, or longitude
                if not tree_id_text or not latitude_text or not longitude_text:
                    skipped_rows += 1
                    continue

                tree_id = int(float(tree_id_text))
                latitude = float(latitude_text)
                longitude = float(longitude_text)
                
                if diameter_text:
                    diameter_breast_height_cm = float(diameter_text)
                else:
                    diameter_breast_height_cm = None

                # remove duplicates based on tree ID
                if tree_id in seen_tree_ids:
                    skipped_rows += 1
                    continue

                seen_tree_ids.add(tree_id)

                cleaned_rows.append(
                    {
                        "tree_id": tree_id,
                        "scientific_name": scientific_name or None,
                        "diameter_breast_height_cm": diameter_breast_height_cm,
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                )
            except ValueError:
                skipped_rows += 1

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "tree_id",
                "scientific_name",
                "diameter_breast_height_cm",
                "latitude",
                "longitude",
            ],
        )
        writer.writeheader()
        writer.writerows(cleaned_rows)

def main():
    clean_tree_canopies()
    clean_urban_trees_species()


if __name__ == "__main__":
    main()
