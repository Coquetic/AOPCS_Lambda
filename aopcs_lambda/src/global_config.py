from enum import Enum, unique
from typing import Annotated, Literal
from pydantic import StringConstraints
from pydantic_settings import BaseSettings


@unique
class DataSourceEnum(Enum):
    S3 = "S3"
    LOCAL_FILE = "LOCAL_FILE"


class GlobalConfig(BaseSettings):
    """Global configuration settings for AOPCS Lambda."""

    log_level: Annotated[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], StringConstraints(to_upper=True)] = "INFO"
    logger_name: str = "your_logger_name"
    bucket_name: str
    aopcs_path: str
    secret_manager_arn: str
    data_source: DataSourceEnum = DataSourceEnum.S3
    kineis_auth_url: str = "your_auth_url"
    kineis_api_url: str = "your_api_url"
    kineis_timeout: int = 10
    previpass_v1_satellite_whitelist: str = "1A,1B,1E,3A,3B,3D,5A,5C,5E"  # With more than 9 satellites embedded previpass will crash


# Create platform configuration based on environment variables.
global_config = GlobalConfig()  # type: ignore[call-arg]
