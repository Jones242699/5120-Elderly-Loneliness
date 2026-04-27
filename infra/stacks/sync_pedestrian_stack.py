from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
)
from constructs import Construct


class SyncPedestrianStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        sync_data = lambda_.Function(
            self,
            "SyncPedestrianDataFunction",

            function_name="elderly-support-syncPedestrianData",

            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("../backend/sync-pedestrian"),

            timeout=Duration.seconds(30),
            memory_size=128,

            environment={
                "DB_HOST": "elderly-loneliness-database.c58eaa0yqnag.ap-southeast-2.rds.amazonaws.com",
                "DB_NAME": "postgres",
                "DB_USER": "postgres",
                "DB_PASSWORD": "fit5120te28"
            }
        )