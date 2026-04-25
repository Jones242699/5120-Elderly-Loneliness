import os
import aws_cdk as cdk
from stacks.places_stack import PlacesStack

app = cdk.App()

PlacesStack(
    app,
    "PlacesStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region="ap-southeast-2"
    )
)

app.synth()