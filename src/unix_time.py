from datetime import datetime, timezone
from typing import TypeAlias

UTCTimeStamp: TypeAlias = int


def timestamp_to_datetime(timestamp: UTCTimeStamp) -> datetime:
    """Convert a UTC UNIX timestamp into a timezone-aware datetime."""

    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def datetime_to_timestamp(value: datetime) -> UTCTimeStamp:
    """Convert a datetime into a UTC UNIX timestamp."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return UTCTimeStamp(value.timestamp())
