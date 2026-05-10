"""
Match each tree point to a canopy polygon using point-in-polygon logic.

Input:
- data/cleaned/tree_canopies_2021_cleaned.csv
- data/cleaned/urban_trees_species_cleaned.csv

Output:
- data/cleaned/tree_canopy_matches.csv
"""

import csv
import json
import math
import os
import sys

csv.field_size_limit(sys.maxsize)

CELL_SIZE = 0.001


def haversine_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def get_cell(latitude, longitude):
    row = math.floor(latitude / CELL_SIZE)
    col = math.floor(longitude / CELL_SIZE)
    return row, col


def point_on_segment(point_lat, point_lon, start_lon, start_lat, end_lon, end_lat):
    cross = (point_lat - start_lat) * (end_lon - start_lon) - (point_lon - start_lon) * (end_lat - start_lat)
    if abs(cross) > 1e-12:
        return False

    min_lon = min(start_lon, end_lon) - 1e-12
    max_lon = max(start_lon, end_lon) + 1e-12
    min_lat = min(start_lat, end_lat) - 1e-12
    max_lat = max(start_lat, end_lat) + 1e-12

    return min_lon <= point_lon <= max_lon and min_lat <= point_lat <= max_lat


def point_in_ring(point_lat, point_lon, ring):
    inside = False

    for i in range(len(ring)):
        start_lon, start_lat = ring[i]
        end_lon, end_lat = ring[(i + 1) % len(ring)]

        if point_on_segment(point_lat, point_lon, start_lon, start_lat, end_lon, end_lat):
            return True

        intersects = ((start_lat > point_lat) != (end_lat > point_lat))
        if intersects:
            cross_lon = (end_lon - start_lon) * (point_lat - start_lat) / (end_lat - start_lat) + start_lon
            if point_lon < cross_lon:
                inside = not inside

    return inside


def point_in_polygon(point_lat, point_lon, polygon):
    if not polygon:
        return False

    if not point_in_ring(point_lat, point_lon, polygon[0]):
        return False

    for hole in polygon[1:]:
        if point_in_ring(point_lat, point_lon, hole):
            return False

    return True


def point_in_geometry(point_lat, point_lon, geometry):
    geometry_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        return point_in_polygon(point_lat, point_lon, coordinates)

    if geometry_type == "MultiPolygon":
        for polygon in coordinates:
            if point_in_polygon(point_lat, point_lon, polygon):
                return True
        return False

    return False


def get_bbox(geometry):
    all_points = []

    geometry_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        for ring in coordinates:
            all_points.extend(ring)

    elif geometry_type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                all_points.extend(ring)

    longitudes = [point[0] for point in all_points]
    latitudes = [point[1] for point in all_points]

    return min(latitudes), max(latitudes), min(longitudes), max(longitudes)


def build_canopy_index():
    canopies = []
    canopy_grid = {}

    with open("data/cleaned/tree_canopies_2021_cleaned.csv", "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            geometry = json.loads(row["geo_shape"])
            min_lat, max_lat, min_lon, max_lon = get_bbox(geometry)

            canopy = {
                "canopy_id": int(row["canopy_id"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "canopy_area": float(row["canopy_area"]) if row["canopy_area"] else None,
                "canopy_diameter": float(row["canopy_diameter"]) if row["canopy_diameter"] else None,
                "geometry": geometry,
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon,
            }

            canopies.append(canopy)

            start_row, start_col = get_cell(min_lat, min_lon)
            end_row, end_col = get_cell(max_lat, max_lon)

            for row_index in range(start_row, end_row + 1):
                for col_index in range(start_col, end_col + 1):
                    cell = (row_index, col_index)
                    if cell not in canopy_grid:
                        canopy_grid[cell] = []
                    canopy_grid[cell].append(canopy)

    return canopies, canopy_grid


def choose_best_canopy(tree_latitude, tree_longitude, candidates):
    containing_canopies = []

    for canopy in candidates:
        if not (canopy["min_lat"] <= tree_latitude <= canopy["max_lat"]):
            continue
        if not (canopy["min_lon"] <= tree_longitude <= canopy["max_lon"]):
            continue

        if point_in_geometry(tree_latitude, tree_longitude, canopy["geometry"]):
            distance = haversine_distance(
                tree_latitude,
                tree_longitude,
                canopy["latitude"],
                canopy["longitude"],
            )
            containing_canopies.append((distance, canopy))

    if not containing_canopies:
        return None, None

    containing_canopies.sort(key=lambda item: item[0])
    best_distance, best_canopy = containing_canopies[0]
    return best_canopy, best_distance


def match_trees_to_canopies():
    os.makedirs("data/cleaned", exist_ok=True)

    _, canopy_grid = build_canopy_index()
    matched_rows = []
    matched_count = 0
    unmatched_count = 0

    with open("data/cleaned/urban_trees_species_cleaned.csv", "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            tree_id = int(row["tree_id"])
            scientific_name = row["scientific_name"]
            diameter_breast_height_cm = row["diameter_breast_height_cm"] or None
            tree_latitude = float(row["latitude"])
            tree_longitude = float(row["longitude"])

            cell = get_cell(tree_latitude, tree_longitude)
            candidates = canopy_grid.get(cell, [])

            best_canopy, _ = choose_best_canopy(
                tree_latitude,
                tree_longitude,
                candidates,
            )

            if best_canopy is None:
                unmatched_count += 1
                continue

            matched_count += 1
            matched_rows.append(
                {
                    "tree_id": tree_id,
                    "scientific_name": scientific_name,
                    "diameter_breast_height_cm": diameter_breast_height_cm,
                    "tree_latitude": tree_latitude,
                    "tree_longitude": tree_longitude,
                    "canopy_id": best_canopy["canopy_id"],
                    "canopy_area": best_canopy["canopy_area"],
                    "canopy_diameter": best_canopy["canopy_diameter"],
                }
            )

    with open("data/cleaned/tree_canopy_matches.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "tree_id",
                "scientific_name",
                "diameter_breast_height_cm",
                "tree_latitude",
                "tree_longitude",
                "canopy_id",
                "canopy_area",
                "canopy_diameter",
            ],
        )
        writer.writeheader()
        writer.writerows(matched_rows)

    print("trees matched:", matched_count)
    print("trees unmatched:", unmatched_count)


def main():
    match_trees_to_canopies()


if __name__ == "__main__":
    main()
