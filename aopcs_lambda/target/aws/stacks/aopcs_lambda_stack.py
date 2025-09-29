from typing import Any

from aws_cdk import Duration, Stack, IgnoreMode
from aws_cdk import aws_lambda, aws_logs, aws_ecr_assets, aws_s3, aws_events, aws_events_targets, aws_iam

from constructs import Construct

from aopcs_lambda.target.aws.environments.atlas_environment import AtlasEnvironment
from aopcs_lambda.target.aws.aopcs_lambda_configuration_model import AopcsLambdaConfigurationModel


class AopcsLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env: AtlasEnvironment, **kwargs: Any) -> None:
        """Initialize stack.

        Args:
            scope (Construct): Scope of construct.
            construct_id (str): Name of stack.
            env (AtlasEnvironment): Atlas environment to deploy to.
        """
        self.env = env
        super().__init__(scope, construct_id, env=env.cdk_value, **kwargs)
        self.configuration = AopcsLambdaConfigurationModel.read_configuration(environment=str(env))
        self.aopcs_bucket = self.__import_bucket()
        self.aopcs_lambda = self.__create_aopcs_lambda()
        self.__set_lambda_permissions()

        self.__create_event_bridge()

    def __import_bucket(self) -> aws_s3.IBucket:
        return aws_s3.Bucket.from_bucket_name(
            self, "atlas-resources-bucket", bucket_name=self.configuration.lambda_configuration.environment_variables["bucket_name"]
        )

    def __create_aopcs_lambda(self) -> aws_lambda.Function:
        base_path = __file__.split("aopcs_lambda")[0]
        return aws_lambda.DockerImageFunction(
            self,
            id="aopcs-lambda",
            function_name="aopcs-lambda",
            code=aws_lambda.DockerImageCode.from_image_asset(
                directory=base_path, file="Dockerfile", ignore_mode=IgnoreMode.DOCKER, network_mode=aws_ecr_assets.NetworkMode.HOST
            ),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            environment={**self.configuration.lambda_configuration.environment_variables},
            timeout=Duration.seconds(self.configuration.lambda_configuration.duration),
            memory_size=self.configuration.lambda_configuration.memory,
        )

    def __set_lambda_permissions(self) -> None:
        self.aopcs_bucket.grant_read_write(self.aopcs_lambda)

        # Authorize access to Kinéis secret
        secret_arn = self.configuration.secret_manager_arn
        if secret_arn:
            self.aopcs_lambda.add_to_role_policy(aws_iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], resources=[secret_arn]))

    def __create_event_bridge(self) -> None:
        """Create EventBridge."""
        # Production : run evey week day at 08:00 in Summer time zone & 07:00 in Winter time zone
        lambda_config = self.configuration.lambda_configuration
        aws_events.Rule(
            self,
            "ATLAS-aopcs-kineis",
            description="Get Kinéis AOPCS once a day",
            targets=[aws_events_targets.LambdaFunction(self.aopcs_lambda)],
            schedule=aws_events.Schedule.cron(minute=str(lambda_config.eventbridge_minute), hour=str(lambda_config.eventbridge_hour), day="*", month="*"),
        )
