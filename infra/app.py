import os
import aws_cdk as cdk
from stacks.api_stack import ApiStack
from stacks.places_stack import PlacesStack
from stacks.counseling_stack import CounselingStack
from stacks.benches_stack import BenchesStack
from stacks.pedestrian_score_stack import PedestrianScoreStack
from stacks.shade_score_stack import ShadeScoreStack
from stacks.sync_pedestrian_stack import SyncPedestrianStack
from stacks.routes_stack import RoutesStack

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

CounselingStack(
    app,
    "CounselingStack",
    api=api_stack.api,
    env=env
)

BenchesStack(
    app,
    "BenchesStack",
    api=api_stack.api,
    env=env
)

PedestrianScoreStack(
    app,
    "PedestrianScoreStack",
    api=api_stack.api,
    env=env
)

ShadeScoreStack(
    app,
    "ShadeScoreStack",
    api=api_stack.api,
    env=env
)

SyncPedestrianStack(
    app,
    "SyncPedestrianStack",
    env=env
)

RoutesStack(
    app,
    "RoutesStack",
    api=api_stack.api,
    env=env
)

app.synth()