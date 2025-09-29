import pytest
from typing import Any
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from io import StringIO
import json
from botocore.exceptions import ClientError

from aopcs_lambda.src.models.metadata_model import AOPCSMetadataModel


class TestHandler:
    """Test of general good functioning of the handler"""

    def test_handler_uploads_csv(
        self,
        monkeypatch: MonkeyPatch,
        mocker: MockerFixture,
        s3: Any,
        create_test_bucket: Any,
        secrets_client: Any,
        set_env_vars: None,
        lambda_context: Any,
    ) -> None:
        from aopcs_lambda.src import main

        dummy_csv = StringIO("satellite_id,timestamp,data\n1,2024-01-01T00:00:00Z,some_data\n")
        mocker.patch("aopcs_lambda.src.main.fetch_and_convert_kineis_data", return_value=(dummy_csv, AOPCSMetadataModel()))

        main.handler({}, lambda_context)

        response = s3.get_object(Bucket="test-bucket", Key="resources/aopcs/kineis/aop/aop")
        content = response["Body"].read().decode("utf-8")

        assert "satellite_id,timestamp,data" in content
        assert "some_data" in content

    def test_handler_upload_s3_clienterror(
        self,
        monkeypatch: MonkeyPatch,
        mocker: MockerFixture,
        s3: Any,
        create_test_bucket: Any,
        secrets_client: Any,
        set_env_vars: None,
        lambda_context: Any,
    ) -> None:
        from aopcs_lambda.src import main

        dummy_csv = StringIO("satellite_id,timestamp,data\n1,2024-01-01T00:00:00Z,some_data\n")
        mocker.patch("aopcs_lambda.src.main.fetch_and_convert_kineis_data", return_value=(dummy_csv, AOPCSMetadataModel()))

        # Patch s3.upload_fileobj to raise ClientError
        def raise_client_error(*args: Any, **kwargs: Any) -> None:
            raise ClientError({"Error": {}}, "UploadFileObj")

        monkeypatch.setattr(main, "get_s3_client", lambda: s3)
        mocker.patch.object(s3, "upload_fileobj", side_effect=raise_client_error)

        with pytest.raises(ClientError):
            main.handler({}, lambda_context)


class TestGetKineisSecrets:
    """Test of get_kineis_secrets (Scerets Manager) function"""

    def test_get_kineis_secrets_success(self, mocker: MockerFixture, secrets_client: Any) -> None:
        mock_response = {"SecretString": json.dumps({"client_id": "id", "client_secret": "secret"})}
        mocker.patch("boto3.client", return_value=secrets_client)
        mocker.patch.object(secrets_client, "get_secret_value", return_value=mock_response)

        from aopcs_lambda.src.main import get_kineis_secrets

        secrets = get_kineis_secrets("dummy-arn")
        assert secrets["client_id"] == "id"
        assert secrets["client_secret"] == "secret"

    def test_get_kineis_secrets_client_error(self, mocker: MockerFixture, secrets_client: Any) -> None:
        mocker.patch("boto3.client", return_value=secrets_client)
        mocker.patch.object(secrets_client, "get_secret_value", side_effect=ClientError({"Error": {}}, "GetSecretValue"))

        from aopcs_lambda.src.main import get_kineis_secrets

        with pytest.raises(ClientError):
            get_kineis_secrets("dummy-arn")

    def test_get_kineis_secrets_json_error(self, mocker: MockerFixture, secrets_client: Any) -> None:
        mocker.patch("boto3.client", return_value=secrets_client)
        mocker.patch.object(secrets_client, "get_secret_value", return_value={"SecretString": "invalid json"})

        from aopcs_lambda.src.main import get_kineis_secrets

        with pytest.raises(json.JSONDecodeError):
            get_kineis_secrets("dummy-arn")

    def test_get_kineis_secrets_secret_not_found(self, mocker: MockerFixture, secrets_client: Any) -> None:
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secrets Manager can't find the specified secret.",
                "Type": "Sender",
            },
            "ResponseMetadata": {
                "RequestId": "123456",
                "HTTPStatusCode": 400,
                "HTTPHeaders": {},
                "RetryAttempts": 0,
            },
        }

        mocker.patch("boto3.client", return_value=secrets_client)
        mocker.patch.object(
            secrets_client,
            "get_secret_value",
            side_effect=ClientError(error_response, "GetSecretValue"),  # type: ignore
        )

        from aopcs_lambda.src.main import get_kineis_secrets

        with pytest.raises(ClientError) as exc_info:
            get_kineis_secrets("non-existent-secret-arn")

        assert exc_info.value.response["Error"]["Code"] == "ResourceNotFoundException"
