import os

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
)

from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as integrations

from constructs import Construct


class EventsStack(Stack):

    def __init__(self, scope: Construct, id: str, api: apigwv2.HttpApi, **kwargs):
        super().__init__(scope, id, **kwargs)

        # ===== Lambda =====
        get_events_function = lambda_.Function(
            self,
            "GetEventsFunction",

            function_name="elderly-support-getEvents",

            runtime=lambda_.Runtime.PYTHON_3_12,

            handler="lambda_function.lambda_handler",

            code=lambda_.Code.from_asset("../backend/events"),

            timeout=Duration.seconds(10),

            memory_size=128,

            environment={
                "TICKETMASTER_API_KEY": os.getenv("TICKETMASTER_API_KEY")
            }
        )

        # ===== Integration =====
        integration = integrations.HttpLambdaIntegration(
            "EventsIntegration",
            get_events_function
        )

        # ===== Routes =====
        api.add_routes(
            path="/events",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration
        )

        api.add_routes(
            path="/events/{id}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration
        )