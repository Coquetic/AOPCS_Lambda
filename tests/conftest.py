import json
import boto3
import pytest
import types
from typing import Any, Generator
from pytest import MonkeyPatch
from moto import mock_aws


# === Constants as session-scoped fixtures ===
@pytest.fixture(autouse=True, scope="function")
def set_aws_region_env(monkeypatch: MonkeyPatch, aws_region: str) -> None:
    monkeypatch.setenv("AWS_REGION", aws_region)
    monkeypatch.setenv("AWS_DEFAULT_REGION", aws_region)


@pytest.fixture(scope="session")
def aws_region() -> str:
    return "eu-west-3"


@pytest.fixture(scope="session")
def test_bucket_name() -> str:
    return "test-bucket"


@pytest.fixture(scope="session")
def test_secret_name() -> str:
    return "test-secret"


# === Environment setup ===


@pytest.fixture(scope="function")
def set_env_vars(monkeypatch: MonkeyPatch, test_bucket_name: str, test_secret_name: str) -> None:
    monkeypatch.setenv("bucket_name", test_bucket_name)
    monkeypatch.setenv("aopcs_path", "resources/aopcs/kineis/aop")
    monkeypatch.setenv("secret_manager_arn", test_secret_name)


# === AWS mock clients ===


@pytest.fixture(scope="function")
def s3(aws_region: str) -> Generator[Any, None, None]:
    with mock_aws():
        client = boto3.client("s3", region_name=aws_region)
        yield client


@pytest.fixture(scope="function")
def create_test_bucket(s3: Any, test_bucket_name: str, aws_region: str) -> Any:
    s3.create_bucket(Bucket=test_bucket_name, CreateBucketConfiguration={"LocationConstraint": aws_region})
    return s3


@pytest.fixture(scope="function")
def secrets_client(aws_region: str, test_secret_name: str) -> Generator[Any, None, None]:
    with mock_aws():
        client = boto3.client("secretsmanager", region_name=aws_region)
        client.create_secret(Name=test_secret_name, SecretString=json.dumps({"client_id": "testuser", "client_secret": "testpass"}))
        yield client


# === Lambda Context compatible ===


@pytest.fixture(scope="function")
def lambda_context() -> Any:
    context = types.SimpleNamespace()
    context.function_name = "test-function"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:eu-west-3:123456789012:function:test-function"
    context.memory_limit_in_mb = "128"
    context.aws_request_id = "test-request-id"
    context.log_group_name = "/aws/lambda/test-function"
    context.log_stream_name = "2024/01/01/[$LATEST]abcdef123456"
    context.identity = None
    context.client_context = None
    return context
