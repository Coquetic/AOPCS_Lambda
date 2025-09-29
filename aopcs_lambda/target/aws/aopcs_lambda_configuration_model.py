import os
import tomllib
from typing import Dict, Self

from pydantic import BaseModel, Field, NonNegativeInt


class LambdaConfiguration(BaseModel):
    duration: NonNegativeInt
    memory: NonNegativeInt
    eventbridge_hour: NonNegativeInt = Field(default=6)
    eventbridge_minute: NonNegativeInt = Field(default=0)
    environment_variables: Dict[str, str] = Field(default={})
    log_level: str = Field(default="DEBUG")


class AopcsLambdaConfigurationModel(BaseModel):
    bucket_name: str
    aopcs_path: str
    secret_manager_arn: str
    lambda_configuration: LambdaConfiguration

    @classmethod
    def read_configuration(cls, environment: str) -> Self:
        try:
            variables_filename = os.path.join(os.path.dirname(__file__), "environments", f"{environment}.toml")
            with open(variables_filename, "rb") as file:
                return cls(**tomllib.load(file))
        except Exception as ex:
            error_mes = f"Error setting environment variables {ex}. Check the file {variables_filename} has the definition for the env: {environment}"
            raise ValueError(error_mes) from ex
