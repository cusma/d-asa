"""Tests for src.day_count module."""

from __future__ import annotations

from datetime import datetime, timezone

from src.day_count import (
    BusinessDayConvention,
    Calendar,
    EndOfMonthConvention,
    adjust_to_business_day,
    is_business_day,
    is_calculate_shift,
    is_end_of_month,
    is_shift_calculate,
)
from src.unix_time import datetime_to_timestamp


class TestCalendarEnum:
    """Test Calendar enum."""

    def test_has_no_calendar_value(self) -> None:
        """Test NO_CALENDAR constant exists."""
        assert Calendar.NO_CALENDAR is not None
        assert Calendar.NC == Calendar.NO_CALENDAR

    def test_has_monday_to_friday_value(self) -> None:
        """Test MONDAY_TO_FRIDAY constant exists."""
        assert Calendar.MONDAY_TO_FRIDAY is not None
        assert Calendar.MF == Calendar.MONDAY_TO_FRIDAY

    def test_enum_values_are_integers(self) -> None:
        """Test Calendar enum values are integers."""
        assert isinstance(Calendar.NO_CALENDAR, int)
        assert isinstance(Calendar.MONDAY_TO_FRIDAY, int)


class TestEndOfMonthConventionEnum:
    """Test EndOfMonthConvention enum."""

    def test_has_same_day_value(self) -> None:
        """Test SAME_DAY constant exists."""
        assert EndOfMonthConvention.SAME_DAY is not None
        assert EndOfMonthConvention.SD == EndOfMonthConvention.SAME_DAY

    def test_has_end_of_month_value(self) -> None:
        """Test END_OF_MONTH constant exists."""
        assert EndOfMonthConvention.END_OF_MONTH is not None
        assert EndOfMonthConvention.EOM == EndOfMonthConvention.END_OF_MONTH

    def test_enum_values_are_integers(self) -> None:
        """Test EndOfMonthConvention enum values are integers."""
        assert isinstance(EndOfMonthConvention.SAME_DAY, int)
        assert isinstance(EndOfMonthConvention.END_OF_MONTH, int)


class TestBusinessDayConventionEnum:
    """Test BusinessDayConvention enum."""

    def test_has_no_shift_value(self) -> None:
        """Test NO_SHIFT constant exists."""
        assert BusinessDayConvention.NO_SHIFT is not None
        assert BusinessDayConvention.NOS == BusinessDayConvention.NO_SHIFT

    def test_has_all_conventions(self) -> None:
        """Test all business day conventions exist."""
        expected = [
            "NO_SHIFT",
            "SHIFT_CALCULATE_FOLLOWING",
            "SHIFT_CALCULATE_MODIFIED_FOLLOWING",
            "CALCULATE_SHIFT_FOLLOWING",
            "CALCULATE_SHIFT_MODIFIED_FOLLOWING",
            "SHIFT_CALCULATE_PRECEDING",
            "SHIFT_CALCULATE_MODIFIED_PRECEDING",
            "CALCULATE_SHIFT_PRECEDING",
            "CALCULATE_SHIFT_MODIFIED_PRECEDING",
        ]
        for name in expected:
            assert hasattr(BusinessDayConvention, name)

    def test_aliases_match_full_names(self) -> None:
        """Test that aliases match full names."""
        aliases = {
            "NOS": "NO_SHIFT",
            "SCF": "SHIFT_CALCULATE_FOLLOWING",
            "SCMF": "SHIFT_CALCULATE_MODIFIED_FOLLOWING",
            "CSF": "CALCULATE_SHIFT_FOLLOWING",
            "CSMF": "CALCULATE_SHIFT_MODIFIED_FOLLOWING",
            "SCP": "SHIFT_CALCULATE_PRECEDING",
            "SCMP": "SHIFT_CALCULATE_MODIFIED_PRECEDING",
            "CSP": "CALCULATE_SHIFT_PRECEDING",
            "CSMP": "CALCULATE_SHIFT_MODIFIED_PRECEDING",
        }
        for alias, full_name in aliases.items():
            assert getattr(BusinessDayConvention, alias) == getattr(
                BusinessDayConvention, full_name
            )


class TestIsEndOfMonth:
    """Test is_end_of_month function."""

    def test_recognizes_january_31(self) -> None:
        """Test January 31 is end of month."""
        dt = datetime(2024, 1, 31, 12, 0, 0)
        assert is_end_of_month(dt) is True

    def test_recognizes_february_29_leap_year(self) -> None:
        """Test Feb 29 is end of month in leap year."""
        dt = datetime(2024, 2, 29, 12, 0, 0)
        assert is_end_of_month(dt) is True

    def test_recognizes_february_28_non_leap_year(self) -> None:
        """Test Feb 28 is end of month in non-leap year."""
        dt = datetime(2023, 2, 28, 12, 0, 0)
        assert is_end_of_month(dt) is True

    def test_february_28_not_end_in_leap_year(self) -> None:
        """Test Feb 28 is NOT end of month in leap year."""
        dt = datetime(2024, 2, 28, 12, 0, 0)
        assert is_end_of_month(dt) is False

    def test_recognizes_april_30(self) -> None:
        """Test April 30 is end of month (30-day month)."""
        dt = datetime(2024, 4, 30, 12, 0, 0)
        assert is_end_of_month(dt) is True

    def test_april_29_not_end_of_month(self) -> None:
        """Test April 29 is not end of month."""
        dt = datetime(2024, 4, 29, 12, 0, 0)
        assert is_end_of_month(dt) is False

    def test_recognizes_december_31(self) -> None:
        """Test December 31 is end of month."""
        dt = datetime(2024, 12, 31, 12, 0, 0)
        assert is_end_of_month(dt) is True

    def test_january_15_not_end_of_month(self) -> None:
        """Test mid-month date is not end of month."""
        dt = datetime(2024, 1, 15, 12, 0, 0)
        assert is_end_of_month(dt) is False

    def test_all_months_last_days(self) -> None:
        """Test last day detection for all months."""
        # 2024 is a leap year
        month_last_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        for month, last_day in enumerate(month_last_days, start=1):
            dt = datetime(2024, month, last_day, 12, 0, 0)
            assert is_end_of_month(dt) is True, f"Failed for month {month}"


class TestIsBusinessDay:
    """Test is_business_day function."""

    def test_no_calendar_all_days_are_business_days(self) -> None:
        """Test with NO_CALENDAR, all days are business days."""
        # Monday 2024-01-15
        monday = datetime_to_timestamp(
            datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Sunday 2024-01-21
        sunday = datetime_to_timestamp(
            datetime(2024, 1, 21, 12, 0, 0, tzinfo=timezone.utc)
        )

        assert is_business_day(monday, Calendar.NO_CALENDAR) is True
        assert is_business_day(saturday, Calendar.NO_CALENDAR) is True
        assert is_business_day(sunday, Calendar.NO_CALENDAR) is True

    def test_monday_to_friday_weekdays_are_business_days(self) -> None:
        """Test with MONDAY_TO_FRIDAY, weekdays are business days."""
        # Week of 2024-01-15 (Monday) to 2024-01-19 (Friday)
        for day in range(15, 20):
            timestamp = datetime_to_timestamp(
                datetime(2024, 1, day, 12, 0, 0, tzinfo=timezone.utc)
            )
            assert is_business_day(timestamp, Calendar.MONDAY_TO_FRIDAY) is True

    def test_monday_to_friday_weekends_are_not_business_days(self) -> None:
        """Test with MONDAY_TO_FRIDAY, weekends are not business days."""
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Sunday 2024-01-21
        sunday = datetime_to_timestamp(
            datetime(2024, 1, 21, 12, 0, 0, tzinfo=timezone.utc)
        )

        assert is_business_day(saturday, Calendar.MONDAY_TO_FRIDAY) is False
        assert is_business_day(sunday, Calendar.MONDAY_TO_FRIDAY) is False

    def test_default_calendar_is_no_calendar(self) -> None:
        """Test default calendar parameter is NO_CALENDAR."""
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        assert is_business_day(saturday) is True


class TestAdjustToBusinessDay:
    """Test adjust_to_business_day function."""

    def test_no_shift_returns_original(self) -> None:
        """Test NO_SHIFT returns timestamp unchanged."""
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        result = adjust_to_business_day(
            saturday,
            business_day_convention=BusinessDayConvention.NO_SHIFT,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == saturday

    def test_business_day_unchanged(self) -> None:
        """Test business day returns unchanged for any convention."""
        # Monday 2024-01-15
        monday = datetime_to_timestamp(
            datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
        conventions = [
            BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
            BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
            BusinessDayConvention.CALCULATE_SHIFT_FOLLOWING,
            BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
        ]
        for convention in conventions:
            result = adjust_to_business_day(
                monday,
                business_day_convention=convention,
                calendar=Calendar.MONDAY_TO_FRIDAY,
            )
            assert result == monday

    def test_shift_calculate_following_shifts_forward(self) -> None:
        """Test SCF shifts Saturday to next Monday."""
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Expected: Monday 2024-01-22
        expected_monday = datetime_to_timestamp(
            datetime(2024, 1, 22, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            saturday,
            business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected_monday

    def test_calculate_shift_following_shifts_forward(self) -> None:
        """Test CSF shifts Saturday to next Monday."""
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Expected: Monday 2024-01-22
        expected_monday = datetime_to_timestamp(
            datetime(2024, 1, 22, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            saturday,
            business_day_convention=BusinessDayConvention.CALCULATE_SHIFT_FOLLOWING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected_monday

    def test_shift_calculate_preceding_shifts_backward(self) -> None:
        """Test SCP shifts Saturday to previous Friday."""
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Expected: Friday 2024-01-19
        expected_friday = datetime_to_timestamp(
            datetime(2024, 1, 19, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            saturday,
            business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected_friday

    def test_calculate_shift_preceding_shifts_backward(self) -> None:
        """Test CSP shifts Saturday to previous Friday."""
        # Saturday 2024-01-20
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Expected: Friday 2024-01-19
        expected_friday = datetime_to_timestamp(
            datetime(2024, 1, 19, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            saturday,
            business_day_convention=BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected_friday

    def test_modified_following_shifts_back_if_next_month(self) -> None:
        """Test SCMF shifts back to preceding if following goes to next month."""
        # Saturday 2024-01-27 (last Saturday of January)
        saturday = datetime_to_timestamp(
            datetime(2024, 1, 27, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Following would be Monday 2024-01-29 (same month, so should follow)
        expected = datetime_to_timestamp(
            datetime(2024, 1, 29, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            saturday,
            business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected

        # Sunday 2024-03-31 (last day of March)
        # Following would be Monday 2024-04-01 (next month)
        # Should shift back to Friday 2024-03-29
        sunday = datetime_to_timestamp(
            datetime(2024, 3, 31, 12, 0, 0, tzinfo=timezone.utc)
        )
        expected_friday = datetime_to_timestamp(
            datetime(2024, 3, 29, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            sunday,
            business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected_friday

    def test_modified_preceding_shifts_forward_if_previous_month(self) -> None:
        """Test SCMP shifts forward to following if preceding goes to previous month."""
        # Sunday 2024-09-01 (first day of September)
        # Preceding would be Friday 2024-08-30 (previous month)
        # Should shift forward to Monday 2024-09-02
        sunday = datetime_to_timestamp(
            datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        expected_monday = datetime_to_timestamp(
            datetime(2024, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
        )

        result = adjust_to_business_day(
            sunday,
            business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
            calendar=Calendar.MONDAY_TO_FRIDAY,
        )
        assert result == expected_monday


class TestIsCalculateShift:
    """Test is_calculate_shift function."""

    def test_returns_true_for_calculate_shift_conventions(self) -> None:
        """Test returns True for all CS* conventions."""
        cs_conventions = [
            BusinessDayConvention.CALCULATE_SHIFT_FOLLOWING,
            BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_FOLLOWING,
            BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
            BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_PRECEDING,
        ]
        for convention in cs_conventions:
            assert is_calculate_shift(convention) is True

    def test_returns_false_for_shift_calculate_conventions(self) -> None:
        """Test returns False for all SC* conventions."""
        sc_conventions = [
            BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
            BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
            BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
            BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
        ]
        for convention in sc_conventions:
            assert is_calculate_shift(convention) is False

    def test_returns_false_for_no_shift(self) -> None:
        """Test returns False for NO_SHIFT."""
        assert is_calculate_shift(BusinessDayConvention.NO_SHIFT) is False


class TestIsShiftCalculate:
    """Test is_shift_calculate function."""

    def test_returns_true_for_shift_calculate_conventions(self) -> None:
        """Test returns True for all SC* conventions."""
        sc_conventions = [
            BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
            BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
            BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
            BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
        ]
        for convention in sc_conventions:
            assert is_shift_calculate(convention) is True

    def test_returns_false_for_calculate_shift_conventions(self) -> None:
        """Test returns False for all CS* conventions."""
        cs_conventions = [
            BusinessDayConvention.CALCULATE_SHIFT_FOLLOWING,
            BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_FOLLOWING,
            BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
            BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_PRECEDING,
        ]
        for convention in cs_conventions:
            assert is_shift_calculate(convention) is False

    def test_returns_false_for_no_shift(self) -> None:
        """Test returns False for NO_SHIFT."""
        assert is_shift_calculate(BusinessDayConvention.NO_SHIFT) is False
