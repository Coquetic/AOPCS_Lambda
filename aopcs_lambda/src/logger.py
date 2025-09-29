import contextvars
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict


request_id_contextvar = contextvars.ContextVar("request_id", default=str(uuid.uuid4()))
request_ts_contextvar = contextvars.ContextVar("request_ts", default=datetime.now(tz=timezone.utc))


def serialize_datetime(obj: Any) -> str | Any:
    """Serialize timestamps for JSON objects.

    Args:
        obj (Any): Object to serialize.

    Returns:
        Union[str, Any]: Serialized object.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


class JSONLogFormatter(logging.Formatter):
    """Format all log records as json objects."""

    def format_record_dict(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format log record as json object.

        Args:
            record (logging.LogRecord): Record to log.

        Returns:
            Dict[str, Any]: Log record formatted as a json object.
        """
        return {
            "level": record.levelname,
            "module": record.module,
            "lineno": record.lineno,
            "request_ts": request_ts_contextvar.get(),
            "request_id": request_id_contextvar.get(),
            "message": record.getMessage(),
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format all log records as json objects

        Args:
            record (logging.LogRecord): Record to log.

        Returns:
            str: String representation of json object.
        """
        record_dict = self.format_record_dict(record)
        return json.dumps(record_dict, default=serialize_datetime)


def setup_logger(logger_name: str, verbosity: str = "INFO") -> logging.Logger:
    if not isinstance(verbosity, str):
        logging.info("The --verbosity type isn't correct : Verbosity set to INFO.")
        verbosity_level = "INFO"
    else:
        verbosity_level = verbosity.upper()
    try:
        logger = logging.getLogger(logger_name)
        logger.setLevel(verbosity_level)

        # Reseting handlers before recreating it
        if len(logging.getLogger().handlers) > 0:
            logging.getLogger().removeHandler(logging.getLogger().handlers[0])

        handler_stdout = logging.StreamHandler()
        handler_stdout.setFormatter(JSONLogFormatter())
        logger.addHandler(handler_stdout)

    except Exception as ex:
        raise ValueError(f"Exception occured during the logger creation: {ex}") from ex

    return logger
