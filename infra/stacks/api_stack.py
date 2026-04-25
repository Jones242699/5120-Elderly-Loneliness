from aws_cdk import Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.api = apigwv2.HttpApi(
            self,
            "ElderlySupportAPI",
            api_name="Elderly Support API"
        )