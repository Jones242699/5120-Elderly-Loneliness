from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
)
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as integrations
from constructs import Construct


class PedestrianScoreStack(Stack):

    def __init__(self, scope: Construct, id: str, api: apigwv2.HttpApi, **kwargs):
        super().__init__(scope, id, **kwargs)

        score_pedestrian = lambda_.Function(
            self,
            "ScoreRoutesByPedestrianFunction",

            function_name="elderly-support-scoreRoutesByPedestrian",

            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("../backend/pedestrian-score"),

            timeout=Duration.seconds(10),
            memory_size=128,

            environment={
                "DB_HOST": "elderly-loneliness-database.c58eaa0yqnag.ap-southeast-2.rds.amazonaws.com",
                "DB_NAME": "postgres",
                "DB_USER": "postgres",
                "DB_PASSWORD": "fit5120te28"
            },

            layers=[
                lambda_.LayerVersion.from_layer_version_arn(
                    self,
                    "Psycopg2LayerPedestrian",
                    "arn:aws:lambda:ap-southeast-2:021104859098:layer:psycopg2:2"
                )
            ]
        )

        integration = integrations.HttpLambdaIntegration(
            "PedestrianIntegration",
            score_pedestrian
        )

        api.add_routes(
            path="/score/pedestrian",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration
        )