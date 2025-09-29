from typing import Optional

from pydantic import BaseModel

from aopcs_lambda.src.models.base_model import base_config, UTC_DT_TYPE


class AOPCSMetadataModel(BaseModel):
    model_config = base_config

    file_name: Optional[str] = None
    upload_date: Optional[UTC_DT_TYPE] = None
    satellite_prevision_min_date: Optional[UTC_DT_TYPE] = None
    satellite_prevision_max_date: Optional[UTC_DT_TYPE] = None
