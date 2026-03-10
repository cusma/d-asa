"""Tests for src.unix_time module."""

from __future__ import annotations

from datetime import datetime, timezone

from src.unix_time import datetime_to_timestamp, timestamp_to_datetime


class TestTimestampToDatetime:
    """Test timestamp_to_datetime function."""

    def test_converts_epoch_zero(self) -> None:
        """Test conversion of epoch 0 (1970-01-01 00:00:00 UTC)."""
        result = timestamp_to_datetime(0)
        expected = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_converts_positive_timestamp(self) -> None:
        """Test conversion of a positive timestamp."""
        # 2024-01-15 12:30:45 UTC
        timestamp = 1705321845
        result = timestamp_to_datetime(timestamp)
        expected = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        assert result == expected

    def test_converts_negative_timestamp(self) -> None:
        """Test conversion of a negative timestamp (before epoch)."""
        # 1969-12-31 23:59:59 UTC
        timestamp = -1
        result = timestamp_to_datetime(timestamp)
        expected = datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert result == expected

    def test_result_is_utc_aware(self) -> None:
        """Test that result has UTC timezone info."""
        result = timestamp_to_datetime(1705321845)
        assert result.tzinfo is timezone.utc
        assert result.utcoffset() == timezone.utc.utcoffset(None)

    def test_converts_leap_year_date(self) -> None:
        """Test conversion on leap year Feb 29."""
        # 2024-02-29 00:00:00 UTC (leap year)
        timestamp = 1709164800
        result = timestamp_to_datetime(timestamp)
        expected = datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_converts_various_dates(self) -> None:
        """Test conversion of various important dates."""
        test_cases = [
            (1672531200, datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
            (1704067200, datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
            (1735689600, datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
        ]
        for timestamp, expected in test_cases:
            result = timestamp_to_datetime(timestamp)
            assert result == expected


class TestDatetimeToTimestamp:
    """Test datetime_to_timestamp function."""

    def test_converts_epoch_zero(self) -> None:
        """Test conversion of epoch datetime."""
        dt = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = datetime_to_timestamp(dt)
        assert result == 0

    def test_converts_aware_datetime(self) -> None:
        """Test conversion of timezone-aware datetime."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        result = datetime_to_timestamp(dt)
        assert result == 1705321845

    def test_converts_naive_datetime_as_utc(self) -> None:
        """Test conversion of naive datetime (treated as UTC)."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        result = datetime_to_timestamp(dt)
        assert result == 1705321845

    def test_converts_leap_year_date(self) -> None:
        """Test conversion on leap year Feb 29."""
        dt = datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)
        result = datetime_to_timestamp(dt)
        assert result == 1709164800

    def test_converts_various_dates(self) -> None:
        """Test conversion of various important dates."""
        test_cases = [
            (datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc), 1672531200),
            (datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc), 1704067200),
            (datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc), 1735689600),
        ]
        for dt, expected in test_cases:
            result = datetime_to_timestamp(dt)
            assert result == expected


class TestRoundTrip:
    """Test round-trip conversions between timestamp and datetime."""

    def test_timestamp_to_datetime_to_timestamp(self) -> None:
        """Test converting timestamp -> datetime -> timestamp preserves value."""
        original = 1705324245
        dt = timestamp_to_datetime(original)
        result = datetime_to_timestamp(dt)
        assert result == original

    def test_datetime_to_timestamp_to_datetime(self) -> None:
        """Test converting datetime -> timestamp -> datetime preserves value."""
        original = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        timestamp = datetime_to_timestamp(original)
        result = timestamp_to_datetime(timestamp)
        assert result == original

    def test_roundtrip_multiple_values(self) -> None:
        """Test round-trip conversion for multiple timestamps."""
        timestamps = [0, 1, 1000000, 1705321845, 1735689600, -1]
        for original in timestamps:
            dt = timestamp_to_datetime(original)
            result = datetime_to_timestamp(dt)
            assert result == original

    def test_roundtrip_naive_datetime_becomes_aware(self) -> None:
        """Test naive datetime becomes aware after round-trip."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 45)
        timestamp = datetime_to_timestamp(naive_dt)
        result_dt = timestamp_to_datetime(timestamp)
        assert result_dt.tzinfo is timezone.utc
        # Values should be equal ignoring timezone
        assert result_dt.replace(tzinfo=None) == naive_dt
