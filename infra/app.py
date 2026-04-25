import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack
from stacks.places_stack import PlacesStack

app = cdk.App()

#  define unique environment
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region="ap-southeast-2"
)

#  create API Stack
api_stack = ApiStack(
    app,
    "ApiStack",
    env=env
)

#  create Places Stack
PlacesStack(
    app,
    "PlacesStack",
    api=api_stack.api,
    env=env
)

app.synth()