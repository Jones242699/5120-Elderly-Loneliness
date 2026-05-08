from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
)

from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as integrations

from constructs import Construct
import os


class RoutesStack(Stack):

    def __init__(self, scope: Construct, id: str, api: apigwv2.HttpApi, **kwargs):
        super().__init__(scope, id, **kwargs)

        # ===== Lambda =====
        generate_routes = lambda_.Function(
            self,
            "GenerateRoutesFunction",

            function_name="elderly-support-generateRoutes",

            runtime=lambda_.Runtime.PYTHON_3_12,

            handler="lambda_function.lambda_handler",

            code=lambda_.Code.from_asset("../backend/routes"),

            timeout=Duration.seconds(15),

            memory_size=256,

            environment={
                "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY")
            }
        )

        # ===== Integration =====
        integration = integrations.HttpLambdaIntegration(
            "RoutesIntegration",
            generate_routes
        )

        # ===== Routes =====
        api.add_routes(
            path="/routes/generate",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration
        )