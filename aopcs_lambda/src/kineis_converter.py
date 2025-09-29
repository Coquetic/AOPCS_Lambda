from io import StringIO
import os
from typing import Any, List, Tuple
import requests

from aws_lambda_powertools import Logger
from aopcs_lambda.src.global_config import global_config
from aopcs_lambda.src.tools.convert_binary_to_aop_configuration_file_for_previpass import (
    convert_to_csv,
    parse_binary_data,
    FormatReference,
)
from aopcs_lambda.src.models.metadata_model import AOPCSMetadataModel

logger = Logger()

DEFAULT_TIMEOUT = global_config.kineis_timeout


def get_kineis_jwt(client_id: str, client_secret: str) -> Any:
    try:
        response = requests.post(
            global_config.kineis_auth_url,
            headers={"content-type": "application/x-www-form-urlencoded"},
            data={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        logger.info("Successfully obtained Kinéis JWT token")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Kinéis JWT token: {e}")
        raise e


def get_allcast_response(jwt_token: str) -> bytes:
    try:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(global_config.kineis_api_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        logger.info("Successfully fetched Allcast data")
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Allcast data: {e}")
        raise e


def process_allcast_binary(binary_data: bytes, output_csv_path: str) -> None:
    try:
        parsed_data = parse_binary_data(binary_data)

        logger.debug(f"Parsed binary frame: {parsed_data}")

        # Output csv
        convert_to_csv(parsed_data, output_csv_path)

        configs = []
        constellation_status = []

        for frame in parsed_data:
            if frame.get("formatReference") in [FormatReference.AOP_MONOSAT.name, FormatReference.AOP_MULTISAT.name]:
                configs.append(frame)
            elif frame.get("formatReference") in [FormatReference.CS_2_SAT.name, FormatReference.CS_10_SAT.name, FormatReference.CS_17_SAT.name]:
                constellation_status.append(frame)
            else:
                logger.warning(f"Unknown format: {frame.get('formatReference')}")

        logger.info(f"Extracted Configurations: {configs}")
        logger.info(f"Constellation status: {constellation_status}")

    except Exception as e:
        logger.error(f"Error processing Allcast binary: {e}")
        raise e


def fetch_and_convert_kineis_data(client_id: str, client_secret: str, satellite_whitelist: List[str]) -> Tuple[StringIO, AOPCSMetadataModel]:
    token = get_kineis_jwt(client_id, client_secret)
    binary_data = get_allcast_response(token)
    parsed_data = parse_binary_data(binary_data)
    csv_buffer, metadata = convert_to_csv(parsed_data=parsed_data, satellite_whitelist=satellite_whitelist)
    return csv_buffer, metadata


if __name__ == "__main__":
    # Secrets as an input on local
    CLIENT_ID = os.getenv("KINEIS_CLIENT_ID", "your_client_id")
    CLIENT_SECRET = os.getenv("KINEIS_CLIENT_SECRET", "your_client_secret")
    SATELLITE_WHITELIST: List[str] = []  # Empty list means no filtering, otherwise provide a list of satellite names to filter

    # Example usage with a destination CSV file path
    csv_file_path = "aopcs_lambda/src/output1.csv"

    try:
        logger.info("\nAuthentication in progress...")
        token = get_kineis_jwt(CLIENT_ID, CLIENT_SECRET)

        logger.debug("\nGet allcast response...")
        binary_data = get_allcast_response(token)

        logger.debug("\nBinary Frame Processing...")
        process_allcast_binary(binary_data, csv_file_path)
    except Exception as e:
        logger.error(f"Error: {e}")

    # Example usage without a destination CSV file path
    try:
        csv_buffer, metadata = fetch_and_convert_kineis_data(CLIENT_ID, CLIENT_SECRET, SATELLITE_WHITELIST)
        logger.info(csv_buffer.getvalue())
        logger.info(metadata)
    except Exception as e:
        logger.error(f"Error: {e}")
