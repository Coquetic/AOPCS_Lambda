#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aopcs_lambda.target.aws.stacks.aopcs_lambda_stack import AopcsLambdaStack
from aopcs_lambda.target.aws.environments.atlas_environment import AtlasEnvironment

app = cdk.App()

env_str = app.node.try_get_context("environment")

atlas_env = AtlasEnvironment(env_str)

stack = AopcsLambdaStack(app, "AopcsLambdaStack", env=atlas_env)

branch_tag = os.environ.get("BRANCH", "not-set")
version_tag = os.environ.get("VERSION", "not-set")

cdk.Tags.of(stack).add("BRANCH", branch_tag)
cdk.Tags.of(stack).add("VERSION", version_tag)

app.synth()
