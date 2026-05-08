from aws_cdk import Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.api = apigwv2.HttpApi(
            self,
            "ElderlySupportAPI",
            api_name="Elderly Support API",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=[
                    "http://localhost:5173",
                    "https://5120-loneliness-web.pages.dev",
                    "https://iterationone.5120-loneliness-web.pages.dev",
                    "https://iterationtwo.5120-loneliness-web.pages.dev",
                    "https://iterationthree.5120-loneliness-web.pages.dev",
                ],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=[
                    "Content-Type",
                ],
            ),
        )