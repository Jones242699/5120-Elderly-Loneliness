import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "status": "success",
            "data": [
                {
                    "id": "1",
                    "name": "Downtown Coffee Shop",
                    "address": "123 Main Street, New York, NY 10001",
                    "latitude": 40.7128,
                    "longitude": -74.0060
                },
                {
                    "id": "2",
                    "name": "Riverside Bookstore",
                    "address": "456 River Road, Portland, OR 97204",
                    "latitude": 45.5152,
                    "longitude": -122.6784
                }
            ]
        })
    }