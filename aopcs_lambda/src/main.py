from datetime import datetime
from io import BytesIO
import json
from typing import Any, Dict
import boto3
import botocore.exceptions
import pytz
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger
from aopcs_lambda.src.global_config import global_config
from aopcs_lambda.src.kineis_converter import fetch_and_convert_kineis_data

logger = Logger()


def get_s3_client() -> Any:
    return boto3.client("s3")


def get_secrets_client() -> Any:
    return boto3.client("secretsmanager")


def get_kineis_secrets(secret_arn: str) -> Dict[str, str]:
    """Fetch Kinéis secrets (client_id and client_secret) from AWS Secrets Manager."""
    secrets_client = get_secrets_client()
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_dict = json.loads(response["SecretString"])
        return {"client_id": secret_dict["client_id"], "client_secret": secret_dict["client_secret"]}
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error fetching Kinéis secrets: {e}")
        raise e
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding secrets JSON: {e}")
        raise e


def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    s3_client = get_s3_client()
    try:
        # Load config from environment
        bucket_name = global_config.bucket_name
        aopcs_path = global_config.aopcs_path
        secret_arn = global_config.secret_manager_arn

        logger.debug(
            "Loaded environment variables",
            extra={
                "bucket": bucket_name,
                "path": aopcs_path,
                "secret_arn": secret_arn,
            },
        )

        # Get secrets
        secrets = get_kineis_secrets(secret_arn)
        client_id = secrets["client_id"]
        client_secret = secrets["client_secret"]

        # satellite whitelist:
        satellite_whitelist = global_config.previpass_v1_satellite_whitelist.split(",") if global_config.previpass_v1_satellite_whitelist else []

        # Fetch & convert data to CSV
        logger.info("Fetching and converting Kinéis data...")
        csv_output, metadata_obj = fetch_and_convert_kineis_data(client_id, client_secret, satellite_whitelist)

        # Convert to bytes for S3 upload
        csv_bytes = BytesIO(csv_output.getvalue().encode("utf-8"))
        csv_bytes.seek(0)

        metadata_obj.file_name = "aop"
        metadata_obj.upload_date = pytz.timezone("Europe/Paris").normalize(datetime.now(tz=pytz.utc))
        metadata_json_bytes = BytesIO(metadata_obj.model_dump_json().encode("utf-8"))
        metadata_json_bytes.seek(0)

        # Define S3 key and upload
        csv_s3_key = f"{aopcs_path}/aop"
        metadata_s3_key = f"{aopcs_path}/metadata.json"
        try:
            s3_client.upload_fileobj(csv_bytes, bucket_name, csv_s3_key)
            logger.info("CSV uploaded successfully", extra={"s3_uri": f"s3://{bucket_name}/{csv_s3_key}"})
            s3_client.upload_fileobj(metadata_json_bytes, bucket_name, metadata_s3_key)
            logger.info("Metadata uploaded successfully", extra={"s3_uri": f"s3://{bucket_name}/{metadata_s3_key}"})
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error uploading DATA to S3: {e}")
            raise e

    except botocore.exceptions.ClientError as e:
        logger.error(f"AWS client error: {e}")
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error during Kinéis processing: {e}")
        raise e
