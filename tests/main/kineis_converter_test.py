from typing import Any
import pytest
from pytest_mock import MockerFixture
from requests.exceptions import RequestException


class TestKineisConverter:
    """Test of get_kineis_jwt & get_allcast_response functions"""

    def test_get_kineis_jwt_success(self, mocker: MockerFixture, set_env_vars: None, secrets_client: Any, create_test_bucket: Any) -> None:
        from aopcs_lambda.src.kineis_converter import get_kineis_jwt

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mocked_token"}

        mock_post = mocker.patch("aopcs_lambda.src.kineis_converter.requests.post", return_value=mock_response)

        token = get_kineis_jwt("fake_client_id", "fake_client_secret")

        assert token == "mocked_token"
        mock_post.assert_called_once()

    def test_get_kineis_jwt_failure(self, mocker: MockerFixture, set_env_vars: None, secrets_client: Any, create_test_bucket: Any) -> None:
        from aopcs_lambda.src.kineis_converter import get_kineis_jwt

        mocker.patch("aopcs_lambda.src.kineis_converter.requests.post", side_effect=RequestException("Connection error"))

        with pytest.raises(RequestException):
            get_kineis_jwt("fake_client_id", "fake_client_secret")

    def test_get_allcast_response_success(self, mocker: MockerFixture, set_env_vars: None, secrets_client: Any, create_test_bucket: Any) -> None:
        from aopcs_lambda.src.kineis_converter import get_allcast_response

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.content = b"mocked_binary_data"

        mock_get = mocker.patch("aopcs_lambda.src.kineis_converter.requests.get", return_value=mock_response)

        result = get_allcast_response("mocked_jwt_token")

        assert result == b"mocked_binary_data"
        mock_get.assert_called_once()
        assert "Authorization" in mock_get.call_args[1]["headers"]

    def test_get_allcast_response_failure(self, mocker: MockerFixture, set_env_vars: None, secrets_client: Any, create_test_bucket: Any) -> None:
        from aopcs_lambda.src.kineis_converter import get_allcast_response

        mocker.patch("aopcs_lambda.src.kineis_converter.requests.get", side_effect=RequestException("Timeout"))

        with pytest.raises(RequestException):
            get_allcast_response("mocked_jwt_token")
