import json
import urllib.request
from collections import defaultdict
from datetime import datetime
from db import upsert_pedestrian_data

def lambda_handler(event, context):
    try:
        url = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/pedestrian-counting-system-past-hour-counts-per-minute/records?limit=100"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        response = urllib.request.urlopen(req)
        data = json.loads(response.read())

        # Store the time series for each sensor
        sensor_records = defaultdict(list)

        for item in data.get("results", []):
            sensor_id = item.get("location_id")
            count = item.get("total_of_directions", 0)
            timestamp = item.get("sensing_datetime")

            if sensor_id and timestamp:
                sensor_records[sensor_id].append((timestamp, count))

        sensor_weighted_avg = {}

        # Do linear weighted average for each sensor
        for sensor_id, records in sensor_records.items():
            # Sort by time (old → new)
            records.sort(key=lambda x: x[0])

            total_weight = 0
            weighted_sum = 0

            for i, (_, count) in enumerate(records):
                weight = i + 1
                weighted_sum += count * weight
                total_weight += weight

            if total_weight > 0:
                sensor_weighted_avg[sensor_id] = round(weighted_sum / total_weight, 2)

        # Write to database
        try:
            upsert_pedestrian_data(sensor_weighted_avg)
        except Exception as db_error:
            print("DB not ready:", str(db_error))
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Database write failed"})
            }

        print("Sync success:", len(sensor_weighted_avg), "sensors")
        print("Sample:", list(sensor_weighted_avg.items())[:5])

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Sync success",
                "sensor_count": len(sensor_weighted_avg),
                "updated_at": datetime.utcnow().isoformat()
            })
        }

    except Exception as e:
        print("Error:", str(e))

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }