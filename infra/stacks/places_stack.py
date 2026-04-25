from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
)
from constructs import Construct


class PlacesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ===== 1. Use Existing VPC =====
        vpc = ec2.Vpc.from_lookup(
            self,
            "ExistingVPC",
            vpc_id="vpc-0eaca89cdd2d95a39"
        )

        # ===== 2. Use Existing Security Group =====
        sg = ec2.SecurityGroup.from_security_group_id(
            self,
            "LambdaSecurityGroup",
            "sg-0fe7cdc5d12e9a677"
        )

        # ===== 3. Use psycopg2 layer =====
        psycopg2_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "Psycopg2Layer",
            "arn:aws:lambda:ap-southeast-2:021104859098:layer:psycopg2:2"
        )

        # ===== 4. Lambda：getNearbyPlaces =====
        get_nearby_places = lambda_.Function(
            self,
            "getNearbyPlaces",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("../backend/places"),

            timeout=Duration.seconds(10),
            memory_size=128,

            vpc=vpc,
            security_groups=[sg],

            allow_public_subnet=True,  # 🔥 加这一行

            environment={
                "DB_HOST": "elderly-loneliness-database.c58eaa0yqnag.ap-southeast-2.rds.amazonaws.com",
                "DB_NAME": "postgres",
                "DB_USER": "postgres",
                "DB_PASSWORD": "fit5120te28"
            },

            layers=[psycopg2_layer]
        )

        # ===== 5. API Gateway =====
        api = apigateway.RestApi(
            self,
            "PlacesApi",
            rest_api_name="Places Service",
        )

        # /places endpoint
        places = api.root.add_resource("places")

        places.add_method(
            "GET",
            apigateway.LambdaIntegration(get_nearby_places)
        )