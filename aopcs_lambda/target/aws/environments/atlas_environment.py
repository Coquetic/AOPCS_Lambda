from enum import unique

import aws_cdk as cdk

from .base_environment import BaseEnvironment


@unique
class AtlasEnvironment(BaseEnvironment):
    """Enum representing the environment to deploy to."""

    DEVELOPMENT = cdk.Environment(account="XXXXXXXXXXXXX", region="your_region")
    VALIDATION = cdk.Environment(account="XXXXXXXXXXXXX", region="your_region")
    PREPRODUCTION = cdk.Environment(account="XXXXXXXXXXXXX", region="your_region")
    PRODUCTION = cdk.Environment(account="XXXXXXXXXXXXX", region="your_region")
