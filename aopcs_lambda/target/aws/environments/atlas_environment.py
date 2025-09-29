from enum import unique

import aws_cdk as cdk

from .base_environment import BaseEnvironment


@unique
class AtlasEnvironment(BaseEnvironment):
    """Enum representing the environment to deploy to."""

    DEVELOPMENT = cdk.Environment(account="277707127236", region="eu-west-3")
    VALIDATION = cdk.Environment(account="182399725777", region="eu-west-3")
    PREPRODUCTION = cdk.Environment(account="354918403859", region="eu-west-3")
    PRODUCTION = cdk.Environment(account="816069150588", region="eu-west-3")
