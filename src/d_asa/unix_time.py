from datetime import UTC, datetime

type UTCTimeStamp = int


def timestamp_to_datetime(timestamp: UTCTimeStamp) -> datetime:
    """Convert a UTC UNIX timestamp into a timezone-aware datetime."""

    return datetime.fromtimestamp(timestamp, tz=UTC)


def datetime_to_timestamp(value: datetime) -> UTCTimeStamp:
    """Convert a datetime into a UTC UNIX timestamp."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())
