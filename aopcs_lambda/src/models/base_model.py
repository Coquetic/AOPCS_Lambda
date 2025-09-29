from datetime import datetime, timezone
from typing import Annotated

from pydantic import AliasGenerator, ConfigDict, AwareDatetime
from pydantic.alias_generators import to_camel
from pydantic import PlainSerializer, AfterValidator, BeforeValidator

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def serialize_datetime(dt: AwareDatetime) -> str:
    return dt.strftime(DATETIME_FORMAT)


def convert_to_utc(dt: AwareDatetime) -> AwareDatetime:
    if dt.tzinfo != timezone.utc:
        return dt.astimezone(tz=timezone.utc)
    return dt


def parse_dt_string(dt: datetime | str) -> datetime:
    if isinstance(dt, str):
        return datetime.strptime(dt, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
    elif isinstance(dt, datetime):
        return dt
    raise ValueError(f"Expected timestamp in either datetime or string ({DATETIME_FORMAT}) format.")


UTC_DT_TYPE = Annotated[AwareDatetime, BeforeValidator(parse_dt_string), AfterValidator(convert_to_utc), PlainSerializer(serialize_datetime)]

base_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    alias_generator=AliasGenerator(serialization_alias=to_camel, validation_alias=to_camel),
)
