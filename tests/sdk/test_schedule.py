"""Tests for d_asa.schedule module."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from d_asa.day_count import (
    BusinessDayConvention,
    Calendar,
    EndOfMonthConvention,
)
from d_asa.errors import UnsupportedActusFeatureError
from d_asa.schedule import (
    Cycle,
    add_cycle,
    generate_array_schedule,
    generate_schedule,
    resolve_array_schedule,
    resolve_cycle_schedule,
)
from d_asa.unix_time import datetime_to_timestamp


class TestCycle:
    """Test Cycle dataclass."""

    def test_create_cycle_with_defaults(self) -> None:
        """Test creating Cycle with default stub."""
        cycle = Cycle(count=3, unit="M")
        assert cycle.count == 3
        assert cycle.unit == "M"
        assert cycle.stub == ""

    def test_create_cycle_with_stub(self) -> None:
        """Test creating Cycle with stub marker."""
        cycle = Cycle(count=1, unit="Q", stub="+")
        assert cycle.count == 1
        assert cycle.unit == "Q"
        assert cycle.stub == "+"


class TestCycleParseCycle:
    """Test Cycle.parse_cycle class method."""

    def test_parse_simple_day_cycle(self) -> None:
        """Test parsing day cycle."""
        cycle = Cycle.parse_cycle("90D")
        assert cycle.count == 90
        assert cycle.unit == "D"
        assert cycle.stub == ""

    def test_parse_simple_week_cycle(self) -> None:
        """Test parsing week cycle."""
        cycle = Cycle.parse_cycle("12W")
        assert cycle.count == 12
        assert cycle.unit == "W"
        assert cycle.stub == ""

    def test_parse_simple_month_cycle(self) -> None:
        """Test parsing month cycle."""
        cycle = Cycle.parse_cycle("3M")
        assert cycle.count == 3
        assert cycle.unit == "M"
        assert cycle.stub == ""

    def test_parse_simple_quarter_cycle(self) -> None:
        """Test parsing quarter cycle."""
        cycle = Cycle.parse_cycle("1Q")
        assert cycle.count == 1
        assert cycle.unit == "Q"
        assert cycle.stub == ""

    def test_parse_simple_half_year_cycle(self) -> None:
        """Test parsing half-year cycle."""
        cycle = Cycle.parse_cycle("1H")
        assert cycle.count == 1
        assert cycle.unit == "H"
        assert cycle.stub == ""

    def test_parse_simple_year_cycle(self) -> None:
        """Test parsing year cycle."""
        cycle = Cycle.parse_cycle("2Y")
        assert cycle.count == 2
        assert cycle.unit == "Y"
        assert cycle.stub == ""

    def test_parse_cycle_with_long_stub(self) -> None:
        """Test parsing cycle with long stub marker."""
        cycle = Cycle.parse_cycle("3M+")
        assert cycle.count == 3
        assert cycle.unit == "M"
        assert cycle.stub == "+"

    def test_parse_cycle_with_short_stub(self) -> None:
        """Test parsing cycle with short stub marker."""
        cycle = Cycle.parse_cycle("1Q-")
        assert cycle.count == 1
        assert cycle.unit == "Q"
        assert cycle.stub == "-"

    def test_parse_cycle_case_insensitive(self) -> None:
        """Test parsing is case-insensitive."""
        cycle = Cycle.parse_cycle("3m")
        assert cycle.count == 3
        assert cycle.unit == "M"

    def test_parse_cycle_strips_whitespace(self) -> None:
        """Test parsing strips whitespace."""
        cycle = Cycle.parse_cycle("  3M  ")
        assert cycle.count == 3
        assert cycle.unit == "M"

    def test_parse_multi_digit_count(self) -> None:
        """Test parsing cycles with multi-digit counts."""
        cycle = Cycle.parse_cycle("365D")
        assert cycle.count == 365
        assert cycle.unit == "D"

    def test_parse_invalid_format_raises_error(self) -> None:
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported ACTUS cycle"):
            Cycle.parse_cycle("M")  # Missing count

        with pytest.raises(ValueError, match="Unsupported ACTUS cycle"):
            Cycle.parse_cycle("XYZ")

    def test_parse_invalid_unit_raises_error(self) -> None:
        """Test parsing invalid unit raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cycle unit"):
            Cycle.parse_cycle("3X")


class TestAddCycle:
    """Test add_cycle function."""

    def test_add_day_cycle(self) -> None:
        """Test adding day cycles."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start,
            "30D",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
        )
        expected = datetime_to_timestamp(datetime(2024, 2, 14, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_week_cycle(self) -> None:
        """Test adding week cycles."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start,
            "2W",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
        )
        expected = datetime_to_timestamp(datetime(2024, 1, 29, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_month_cycle(self) -> None:
        """Test adding month cycles."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start,
            "1M",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
        )
        expected = datetime_to_timestamp(datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_quarter_cycle(self) -> None:
        """Test adding quarter cycles."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start,
            "1Q",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
        )
        expected = datetime_to_timestamp(datetime(2024, 4, 15, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_half_year_cycle(self) -> None:
        """Test adding half-year cycles."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start,
            "1H",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
        )
        expected = datetime_to_timestamp(datetime(2024, 7, 15, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_year_cycle(self) -> None:
        """Test adding year cycles."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start,
            "1Y",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
        )
        expected = datetime_to_timestamp(datetime(2025, 1, 15, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_month_cycle_with_same_day_convention(self) -> None:
        """Test adding month cycle with SAME_DAY convention."""
        # Jan 31 + 1M = Feb 29 (capped to last day of Feb in leap year)
        start = datetime_to_timestamp(datetime(2024, 1, 31, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start, "1M", end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )
        expected = datetime_to_timestamp(datetime(2024, 2, 29, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_month_cycle_with_eom_convention(self) -> None:
        """Test adding month cycle with END_OF_MONTH convention."""
        # Jan 31 (end of month) + 1M = Feb 29 (end of month in leap year)
        start = datetime_to_timestamp(datetime(2024, 1, 31, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start, "1M", end_of_month_convention=EndOfMonthConvention.END_OF_MONTH
        )
        expected = datetime_to_timestamp(datetime(2024, 2, 29, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_cycle_with_anchor_and_occurrence(self) -> None:
        """Test adding cycle with anchor and occurrence index."""
        anchor = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            anchor,
            "1M",
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            anchor_timestamp=anchor,
            occurrence_index=3,
        )
        expected = datetime_to_timestamp(datetime(2024, 4, 15, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_month_cycle_handles_short_months(self) -> None:
        """Test month cycle handles months with different days."""
        # Jan 31 + 3M = Apr 30 (April has only 30 days)
        start = datetime_to_timestamp(datetime(2024, 1, 31, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start, "3M", end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )
        expected = datetime_to_timestamp(datetime(2024, 4, 30, 0, 0, 0, tzinfo=UTC))
        assert result == expected

    def test_add_cycle_leap_year_february(self) -> None:
        """Test adding cycles around leap year February."""
        # Feb 29 2024 (leap year) + 1Y = Feb 28 2025 (non-leap year)
        start = datetime_to_timestamp(datetime(2024, 2, 29, 0, 0, 0, tzinfo=UTC))
        result = add_cycle(
            start, "1Y", end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )
        expected = datetime_to_timestamp(datetime(2025, 2, 28, 0, 0, 0, tzinfo=UTC))
        assert result == expected


class TestGenerateSchedule:
    """Test generate_schedule function."""

    def test_generate_monthly_schedule(self) -> None:
        """Test generating monthly schedule."""
        start = datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 4, 15, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1M", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        expected = (
            datetime_to_timestamp(datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 3, 15, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 15, 0, 0, 0, tzinfo=UTC)),
        )
        assert schedule == expected

    def test_generate_quarterly_schedule(self) -> None:
        """Test generating quarterly schedule."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1Q", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        expected = (
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 7, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 10, 1, 0, 0, 0, tzinfo=UTC)),
        )
        assert schedule == expected

    def test_generate_daily_schedule(self) -> None:
        """Test generating daily schedule."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 1, 5, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1D", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        assert len(schedule) == 5
        assert schedule[0] == start
        assert schedule[-1] == end

    def test_generate_yearly_schedule(self) -> None:
        """Test generating yearly schedule."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1Y", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        expected = (
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC)),
        )
        assert schedule == expected

    def test_generate_schedule_stops_at_end(self) -> None:
        """Test schedule generation stops at end date."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 3, 15, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1M", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        # Should have Jan 1, Feb 1, Mar 1 but not Apr 1
        assert len(schedule) == 3
        assert schedule[-1] < end

    def test_generate_schedule_includes_end_if_exact_match(self) -> None:
        """Test schedule includes end if it matches exactly."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1M", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        assert schedule[-1] == end

    def test_generate_schedule_with_eom_convention(self) -> None:
        """Test schedule generation with END_OF_MONTH convention."""
        # Jan 31 (end of month)
        start = datetime_to_timestamp(datetime(2024, 1, 31, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start,
            "1M",
            end,
            end_of_month_convention=EndOfMonthConvention.END_OF_MONTH,
        )

        # Should generate: Jan 31, Feb 29, Mar 31, Apr 30
        expected = (
            datetime_to_timestamp(datetime(2024, 1, 31, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 2, 29, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 3, 31, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 30, 0, 0, 0, tzinfo=UTC)),
        )
        assert schedule == expected

    def test_generate_schedule_empty_if_start_after_end(self) -> None:
        """Test empty schedule if start > end."""
        start = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_schedule(
            start, "1M", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        assert schedule == ()

    def test_generate_schedule_empty_if_start_zero_or_negative(self) -> None:
        """Test empty schedule if start <= 0."""
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))

        assert (
            generate_schedule(
                0, "1M", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
            )
            == ()
        )
        assert (
            generate_schedule(
                -1, "1M", end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
            )
            == ()
        )

    def test_generate_schedule_empty_if_end_zero_or_negative(self) -> None:
        """Test empty schedule if end <= 0."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))

        assert (
            generate_schedule(
                start, "1M", 0, end_of_month_convention=EndOfMonthConvention.SAME_DAY
            )
            == ()
        )
        assert (
            generate_schedule(
                start, "1M", -1, end_of_month_convention=EndOfMonthConvention.SAME_DAY
            )
            == ()
        )


class TestGenerateArraySchedule:
    """Test generate_array_schedule function."""

    def test_generate_single_segment_schedule(self) -> None:
        """Test array schedule with single anchor/cycle."""
        anchors = [datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))]
        cycles = ["1M"]
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_array_schedule(
            anchors, cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        expected = (
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
        )
        assert schedule == expected

    def test_generate_multi_segment_schedule(self) -> None:
        """Test array schedule with multiple anchor/cycle pairs."""
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        cycles = ["1M", "3M"]
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))

        schedule = generate_array_schedule(
            anchors, cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        # First segment: monthly Jan 1, Feb 1, Mar 1 (stops before Apr 1)
        # Second segment: quarterly Apr 1, Jul 1, Oct 1
        # Plus end date Dec 31
        expected_dates = [
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 7, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 10, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC),
        ]
        expected = tuple(datetime_to_timestamp(dt) for dt in expected_dates)
        assert schedule == expected

    def test_generate_array_schedule_deduplicates(self) -> None:
        """Test array schedule removes duplicates."""
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        cycles = ["1M", "1M"]
        end = datetime_to_timestamp(datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_array_schedule(
            anchors, cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        # Should have unique dates: Jan 1, Feb 1, Mar 1, Apr 1, May 1
        assert len(schedule) == len(set(schedule))

    def test_generate_array_schedule_sorts_dates(self) -> None:
        """Test array schedule returns sorted dates."""
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        cycles = ["1M", "1M"]
        end = datetime_to_timestamp(datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC))

        schedule = generate_array_schedule(
            anchors, cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        # Should be sorted
        assert schedule == tuple(sorted(schedule))

    def test_generate_array_schedule_includes_end(self) -> None:
        """Test array schedule always includes end date."""
        anchors = [datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))]
        cycles = ["1M"]
        end = datetime_to_timestamp(datetime(2024, 3, 15, 0, 0, 0, tzinfo=UTC))

        schedule = generate_array_schedule(
            anchors, cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )

        assert schedule[-1] == end

    def test_generate_array_schedule_empty_anchors(self) -> None:
        """Test array schedule with empty anchors returns empty."""
        schedule = generate_array_schedule(
            [], [], 1000000, end_of_month_convention=EndOfMonthConvention.SAME_DAY
        )
        assert schedule == ()

    def test_generate_array_schedule_raises_if_length_mismatch(self) -> None:
        """Test array schedule raises if anchors and cycles have different lengths."""
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        cycles = ["1M"]  # Only one cycle for two anchors
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))

        with pytest.raises(
            ValueError, match="anchors and cycles must have same length"
        ):
            generate_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )

    def test_generate_array_schedule_empty_if_end_zero_or_negative(self) -> None:
        """Test array schedule returns empty tuple if end <= 0."""
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        cycles = ["1M"]

        assert (
            generate_array_schedule(
                anchors,
                cycles,
                0,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )
            == ()
        )
        assert (
            generate_array_schedule(
                anchors,
                cycles,
                -1,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )
            == ()
        )

    def test_generate_array_schedule_empty_if_anchor_invalid(self) -> None:
        """Test array schedule returns empty tuple if any anchor is invalid."""
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))
        cycles = ["1M"]

        # Test anchor <= 0
        assert (
            generate_array_schedule(
                [0], cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
            )
            == ()
        )
        assert (
            generate_array_schedule(
                [-1], cycles, end, end_of_month_convention=EndOfMonthConvention.SAME_DAY
            )
            == ()
        )

        # Test anchor > end
        anchors = [end + 1000]
        assert (
            generate_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )
            == ()
        )

    def test_generate_array_schedule_raises_if_anchors_descending(self) -> None:
        """Test array schedule raises if anchors are in descending order."""
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))
        cycles = ["1M", "1M"]

        # Test descending order
        anchors = [
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        with pytest.raises(
            ValueError, match="anchors must be in strictly ascending order"
        ):
            generate_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )

    def test_generate_array_schedule_raises_if_anchors_equal(self) -> None:
        """Test array schedule raises if anchors are equal (not strictly ascending)."""
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))
        cycles = ["1M", "1M"]

        # Test equal anchors (not strictly ascending)
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        with pytest.raises(
            ValueError, match="anchors must be in strictly ascending order"
        ):
            generate_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )

    def test_generate_array_schedule_raises_if_anchors_partially_unsorted(
        self,
    ) -> None:
        """Test array schedule raises if anchors are partially unsorted."""
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))
        cycles = ["1M", "1M", "1M"]

        # First two in order, but third is out of order
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        with pytest.raises(
            ValueError, match="anchors must be in strictly ascending order"
        ):
            generate_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            )


class TestResolveCycleSchedule:
    """Test resolve_cycle_schedule function."""

    def test_resolve_cycle_schedule_no_adjustment(self) -> None:
        """Test resolve_cycle_schedule with NO_SHIFT convention."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        schedule = resolve_cycle_schedule(
            start,
            "1M",
            end,
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            business_day_convention=BusinessDayConvention.NO_SHIFT,
            calendar=Calendar.NO_CALENDAR,
        )

        expected = (
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
        )
        assert schedule == expected

    def test_resolve_cycle_schedule_raises_for_unsupported_bdc(self) -> None:
        """Test raises error for unsupported business day convention."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        with pytest.raises(
            UnsupportedActusFeatureError, match="Business Day Convention"
        ):
            resolve_cycle_schedule(
                start,
                "1M",
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
                business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
                calendar=Calendar.NO_CALENDAR,
            )

    def test_resolve_cycle_schedule_raises_for_unsupported_calendar(self) -> None:
        """Test raises error for unsupported calendar."""
        start = datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        with pytest.raises(UnsupportedActusFeatureError, match="Calendar"):
            resolve_cycle_schedule(
                start,
                "1M",
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
                business_day_convention=BusinessDayConvention.NO_SHIFT,
                calendar=Calendar.MONDAY_TO_FRIDAY,
            )


class TestResolveArraySchedule:
    """Test resolve_array_schedule function."""

    def test_resolve_array_schedule_no_adjustment(self) -> None:
        """Test resolve_array_schedule with NO_SHIFT convention."""
        anchors = [
            datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
            datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC)),
        ]
        cycles = ["1M", "3M"]
        end = datetime_to_timestamp(datetime(2024, 12, 31, 0, 0, 0, tzinfo=UTC))

        schedule = resolve_array_schedule(
            anchors,
            cycles,
            end,
            end_of_month_convention=EndOfMonthConvention.SAME_DAY,
            business_day_convention=BusinessDayConvention.NO_SHIFT,
            calendar=Calendar.NO_CALENDAR,
        )

        # Should have dates from both segments plus end
        assert len(schedule) > 0
        assert schedule[-1] == end

    def test_resolve_array_schedule_raises_for_unsupported_bdc(self) -> None:
        """Test raises error for unsupported business day convention."""
        anchors = [datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))]
        cycles = ["1M"]
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        with pytest.raises(
            UnsupportedActusFeatureError, match="Business Day Convention"
        ):
            resolve_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
                business_day_convention=BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
                calendar=Calendar.NO_CALENDAR,
            )

    def test_resolve_array_schedule_raises_for_unsupported_calendar(self) -> None:
        """Test raises error for unsupported calendar."""
        anchors = [datetime_to_timestamp(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))]
        cycles = ["1M"]
        end = datetime_to_timestamp(datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC))

        with pytest.raises(UnsupportedActusFeatureError, match="Calendar"):
            resolve_array_schedule(
                anchors,
                cycles,
                end,
                end_of_month_convention=EndOfMonthConvention.SAME_DAY,
                business_day_convention=BusinessDayConvention.NO_SHIFT,
                calendar=Calendar.MONDAY_TO_FRIDAY,
            )
