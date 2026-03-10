from __future__ import annotations

from calendar import monthrange
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from smart_contracts.constants import DAY_2_SEC

from .day_count import (
    BusinessDayConvention,
    Calendar,
    EndOfMonthConvention,
    is_end_of_month,
)
from .errors import UnsupportedActusFeatureError
from .unix_time import UTCTimeStamp, datetime_to_timestamp, timestamp_to_datetime


@dataclass(frozen=True, slots=True)
class Cycle:
    """
    ACTUS cycle object representing a time period for schedule generation.

    Attributes:
        count: The number of units in the cycle (e.g., 3 for "3M")
        unit: The time unit - D (days), W (weeks), M (months), Q (quarters),
              H (half-years), Y (years)
        stub: Optional stub period marker ("+" or "-") for short/long stubs

    ACTUS string notation examples:
        - "90D" = 90 days
        - "12W" = 12 weeks
        - "3M" = 3 months
        - "1Q" = 1 quarter (3 months)
        - "1H" = 1 half-year (6 months)
        - "2Y" = 2 years
        - "3M+" = 3 months with long stub marker
        - "1Q-" = 1 quarter with short stub marker
    """

    count: int
    unit: Literal["D", "W", "M", "Q", "H", "Y"]
    stub: str = ""

    @classmethod
    def parse_cycle(cls, raw_cycle: object) -> Cycle:
        """
        Parse an ACTUS cycle string into a Cycle object.

        Args:
            raw_cycle: String representation of the cycle (e.g., "3M", "1Q+")

        Returns:
            Cycle object with parsed count, unit, and optional stub marker

        Raises:
            TypeError: If raw_cycle is not convertible to string
            ValueError: If cycle format is invalid or unit is not recognized

        Examples:
            >>> Cycle.parse_cycle("3M")
            Cycle(count=3, unit='M', stub='')
            >>> Cycle.parse_cycle("1Q+")
            Cycle(count=1, unit='Q', stub='+')
        """

        # If already a Cycle object, return it as-is
        if isinstance(raw_cycle, Cycle):
            return raw_cycle

        try:
            cycle_str = str(raw_cycle).strip().upper()
        except Exception as exc:
            raise TypeError(
                f"Cannot convert cycle to string: {type(raw_cycle).__name__}"
            ) from exc

        if not cycle_str:
            raise ValueError("Cycle string cannot be empty")

        stub = ""
        if cycle_str.endswith(("+", "-")):
            # Sanitize cycle removing markers. Example: "3M+" -> cycle="3M", stub="+"
            stub = cycle_str[-1]
            cycle_str = cycle_str[:-1]

        if len(cycle_str) < 2 or not cycle_str[:-1].isdigit():
            raise ValueError(
                f"Unsupported ACTUS cycle: {raw_cycle!r} (expected format: <number><unit>[+|-])"
            )

        count_str = cycle_str[:-1]
        unit = cycle_str[-1]

        if unit not in ("D", "W", "M", "Q", "H", "Y"):
            raise ValueError(
                f"Invalid cycle unit '{unit}'. Must be one of: D, W, M, Q, H, Y"
            )

        count = int(count_str)
        if count <= 0:
            raise ValueError(f"Cycle count must be positive, got: {count}")

        return Cycle(count=count, unit=unit, stub=stub)


def _add_month_cycle_from_anchor(
    anchor_timestamp: UTCTimeStamp,
    *,
    cycle: Cycle,
    occurrence_index: int,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
) -> UTCTimeStamp:
    """
    Advance a month-based cycle from a fixed anchor UTC UNIX timestamp.

    This function calculates the timestamp for a specific occurrence of a
    month-based cycle (M, Q, H, Y) by adding the appropriate number of months
    to the anchor date. It handles month-end dates according to the specified
    end-of-month convention.

    Args:
        anchor_timestamp: The starting point (UTC UNIX timestamp) from which to calculate
        cycle: Cycle object with unit in {"M", "Q", "H", "Y"}
        occurrence_index: Which occurrence to calculate (0 = anchor, 1 = first, etc.)
        end_of_month_convention: How to handle month-end dates:
            - SD (Same Day): Always use the same day of month (capped to valid days)
            - EOM (End of Month): If anchor is month-end, result is also month-end

    Returns:
        UTC UNIX timestamp for the specified occurrence

    Raises:
        ValueError: If cycle.unit is not a month-based unit (M, Q, H, Y)
        ValueError: If occurrence_index is negative

    Examples:
        For anchor = Jan 31 2024 (month-end), cycle = "1M":
        - With SD: Feb 29, Mar 31, Apr 30, May 31, ...
        - With EOM: Feb 29, Mar 31, Apr 30, May 31, ...
        (Both produce month-ends since Jan 31 is a month-end)

        For anchor = Feb 29 2024 (month-end in leap year), cycle = "1M":
        - With SD: Mar 29, Apr 29, May 29, Jun 29, ...
        - With EOM: Mar 31, Apr 30, May 31, Jun 30, ...
        (EOM sticks to month-ends; SD uses day 29)
    """

    if occurrence_index < 0:
        raise ValueError(
            f"occurrence_index must be non-negative, got: {occurrence_index}"
        )

    month_delta_map = {"M": 1, "Q": 3, "H": 6, "Y": 12}
    if cycle.unit not in month_delta_map:
        raise ValueError(
            f"Unsupported cycle unit for month-based calculation: {cycle.unit}"
        )

    current = timestamp_to_datetime(anchor_timestamp)
    total_months = occurrence_index * cycle.count * month_delta_map[cycle.unit]
    month_index = (current.month - 1) + total_months
    year = current.year + month_index // 12
    month = (month_index % 12) + 1
    day = min(current.day, monthrange(year, month)[1])

    if end_of_month_convention == EndOfMonthConvention.EOM and is_end_of_month(current):
        day = monthrange(year, month)[1]

    return datetime_to_timestamp(current.replace(year=year, month=month, day=day))


def _add_cycle_chained(
    timestamp: UTCTimeStamp,
    cycle: Cycle,
    *,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
) -> UTCTimeStamp:
    """
    Advance one chained cycle from the current UTC UNIX timestamp.

    This function adds exactly one cycle period to the given timestamp.
    For day and week cycles, it performs simple arithmetic addition.
    For month-based cycles, it delegates to _add_month_cycle_from_anchor
    with occurrence_index=1.

    Args:
        timestamp: Current UTC UNIX timestamp to advance from
        cycle: Cycle object defining the period to add
        end_of_month_convention: How to handle month-end dates (used for month-based cycles)

    Returns:
        UTC UNIX timestamp advanced by one cycle period

    Raises:
        ValueError: If cycle.unit is not a recognized unit

    Note:
        This is used for iterative schedule generation where each date is
        calculated from the previous one, rather than from a fixed anchor.
    """

    if cycle.unit == "D":
        return timestamp + cycle.count * DAY_2_SEC
    if cycle.unit == "W":
        return timestamp + cycle.count * 7 * DAY_2_SEC
    if cycle.unit in {"M", "Q", "H", "Y"}:
        return _add_month_cycle_from_anchor(
            timestamp,
            cycle=cycle,
            occurrence_index=1,
            end_of_month_convention=end_of_month_convention,
        )

    raise ValueError(f"Unsupported cycle unit: {cycle.unit}")


def add_cycle(
    timestamp: UTCTimeStamp,
    raw_cycle: object,
    *,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
    anchor_timestamp: UTCTimeStamp | None = None,
    occurrence_index: int | None = None,
) -> UTCTimeStamp:
    """
    Advance a UTC UNIX timestamp by one ACTUS cycle occurrence.

    This function supports two calculation modes:
    1. Anchor-based: When both anchor_timestamp and occurrence_index are provided,
       calculates the Nth occurrence from the anchor (more accurate for long schedules)
    2. Chained: When anchor parameters are None, adds one cycle to timestamp
       (simple iteration from previous date)

    Args:
        timestamp: UTC UNIX timestamp to advance (used in chained mode)
        raw_cycle: ACTUS cycle string (e.g., "3M", "1Q", "90D") or Cycle object
        end_of_month_convention: How to handle month-end dates for month-based cycles
        anchor_timestamp: Optional fixed starting point for anchor-based calculation
        occurrence_index: Optional occurrence number (0 = anchor, 1 = first, etc.)

    Returns:
        UTC UNIX timestamp advanced by the cycle

    Note:
        Anchor-based mode is preferred for generating full schedules as it prevents
        error accumulation. Chained mode is simpler but can accumulate rounding errors
        over many iterations.
    """

    cycle = Cycle.parse_cycle(raw_cycle)

    # Anchor-based mode: calculate from fixed anchor
    if anchor_timestamp is not None and occurrence_index is not None:
        if cycle.unit in {"M", "Q", "H", "Y"}:
            return _add_month_cycle_from_anchor(
                anchor_timestamp,
                cycle=cycle,
                occurrence_index=occurrence_index,
                end_of_month_convention=end_of_month_convention,
            )
        if cycle.unit == "D":
            return anchor_timestamp + occurrence_index * cycle.count * DAY_2_SEC
        if cycle.unit == "W":
            return anchor_timestamp + occurrence_index * cycle.count * 7 * DAY_2_SEC

    # Chained mode: calculate from previous timestamp
    return _add_cycle_chained(
        timestamp, cycle, end_of_month_convention=end_of_month_convention
    )


def generate_schedule(
    start: UTCTimeStamp,
    raw_cycle: object,
    end: UTCTimeStamp,
    *,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
) -> tuple[UTCTimeStamp, ...]:
    """
    Generate raw cycle dates from a start anchor up to an inclusive end date.

    This function creates a sequence of timestamps by repeatedly applying
    the cycle from the start anchor. The start date is always included as
    the first element. All dates are calculated from the anchor to prevent
    error accumulation.

    Args:
        start: UTC UNIX timestamp anchor (first date in schedule)
        raw_cycle: ACTUS cycle string (e.g., "3M", "1Q", "90D")
        end: UTC UNIX timestamp upper bound (inclusive)
        end_of_month_convention: How to handle month-end dates for month-based cycles

    Returns:
        Tuple of UTC UNIX timestamps from start up to (but not exceeding) end.
        Returns empty tuple if start <= 0, end <= 0, or start > end.

    Examples:
        >>> # For timestamps representing 2024-01-15, 2024-04-15
        >>> generate_schedule(
        ...     start=1705276800,  # 2024-01-15 00:00:00 UTC
        ...     raw_cycle="1M",
        ...     end=1713139200     # 2024-04-15 00:00:00 UTC
        ... )
        (1705276800, 1707955200, 1710547200, 1713139200)
    """

    if start <= 0 or end <= 0 or start > end:
        return ()

    cycle = Cycle.parse_cycle(raw_cycle)
    schedule: list[int] = []
    occurrence_index = 0

    # Safety check: prevent infinite loops (max 100 years worth of daily cycles)
    max_iterations = 100 * 365 + 25  # ~36,525 iterations

    while occurrence_index < max_iterations:
        current = add_cycle(
            start,
            cycle,
            end_of_month_convention=end_of_month_convention,
            anchor_timestamp=start,
            occurrence_index=occurrence_index,
        )
        if current > end:
            break
        schedule.append(current)
        occurrence_index += 1

    return tuple(schedule)


def generate_array_schedule(
    anchors: Sequence[UTCTimeStamp],
    cycles: Sequence[object],
    end: UTCTimeStamp,
    *,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
) -> tuple[UTCTimeStamp, ...]:
    """
    Generate a flattened schedule from parallel anchor and cycle arrays.

    This function supports piecewise schedule generation where different
    cycles apply to different time periods. Each anchor/cycle pair defines
    a sub-schedule, and all sub-schedules are merged, sorted, and deduplicated.

    The algorithm:
    1. For each (anchor, cycle) pair, generate dates up to the next anchor
       (or the final end date for the last pair)
    2. Exclude dates that equal or exceed the next anchor (except for last segment)
    3. Merge all dates, add the final end date, sort, and remove duplicates

    Args:
        anchors: Sequence of UTC UNIX timestamps marking schedule segment starts
        cycles: Sequence of ACTUS cycle strings, parallel to anchors
        end: UTC UNIX timestamp upper bound (inclusive, always included in result)
        end_of_month_convention: How to handle month-end dates for month-based cycles

    Returns:
        Tuple of sorted, unique UTC UNIX timestamps covering all segments.
        Returns empty tuple if anchors is empty.

    Raises:
        ValueError: If anchors and cycles have different lengths

    Examples:
        >>> # Generate piecewise schedule with different cycles per segment
        >>> generate_array_schedule(
        ...     anchors=[1704067200, 1711929600],  # 2024-01-01, 2024-04-01 UTC
        ...     cycles=["1M", "3M"],
        ...     end=1735603200  # 2024-12-31 UTC
        ... )
        # Returns monthly timestamps for Jan-Mar, quarterly for Apr-Dec, plus Dec 31
    """

    if len(anchors) != len(cycles):
        raise ValueError("anchors and cycles must have same length")
    if not anchors:
        return ()

    # Use a set for efficient deduplication
    all_dates_set: set[int] = set()

    for index, (anchor, cycle) in enumerate(zip(anchors, cycles, strict=True)):
        sub_end = end if index + 1 == len(anchors) else anchors[index + 1]
        sub_schedule = generate_schedule(
            anchor,
            cycle,
            sub_end,
            end_of_month_convention=end_of_month_convention,
        )

        if index + 1 < len(anchors):
            # Exclude dates that equal or exceed the next anchor
            all_dates_set.update(date for date in sub_schedule if date < sub_end)
        else:
            all_dates_set.update(sub_schedule)

    # Always include the end date
    all_dates_set.add(end)

    return tuple(sorted(all_dates_set))


def resolve_cycle_schedule(
    start: UTCTimeStamp,
    raw_cycle: object,
    end: UTCTimeStamp,
    *,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
    business_day_convention: BusinessDayConvention = BusinessDayConvention.NOS,
    calendar_name: Calendar = Calendar.NC,
) -> tuple[UTCTimeStamp, ...]:
    """
    Generate and business-day-adjust a cycle-based ACTUS schedule.

    This is the high-level function for creating a complete schedule from
    a single anchor and cycle. It generates the base schedule and applies
    business day adjustments according to the specified convention and calendar.

    Args:
        start: UTC UNIX timestamp anchor (first date in schedule)
        raw_cycle: ACTUS cycle string (e.g., "3M", "1Q", "90D")
        end: UTC UNIX timestamp upper bound (inclusive)
        end_of_month_convention: How to handle month-end dates for month-based cycles
        business_day_convention: How to adjust dates that fall on non-business days
        calendar_name: Which calendar defines business days vs. holidays

    Returns:
        Tuple of UTC UNIX timestamps with business day adjustments applied

    Raises:
        UnsupportedActusFeatureError: If business_day_convention is not NO_SHIFT
        UnsupportedActusFeatureError: If calendar_name is not NO_CALENDAR

    Note:
        V1 implementation only supports:
        - BusinessDayConvention: NO_SHIFT (no adjustments)
        - Calendar: NO_CALENDAR (all days are business days)
    """

    if business_day_convention != BusinessDayConvention.NOS:
        raise UnsupportedActusFeatureError(
            "Supported Business Day Convention: NO_SHIFT"
        )
    if calendar_name != Calendar.NC:
        raise UnsupportedActusFeatureError("Supported Calendar: NO_CALENDAR")

    base_dates = generate_schedule(
        start,
        raw_cycle,
        end,
        end_of_month_convention=end_of_month_convention,
    )
    return tuple(base_date for base_date in base_dates)


def resolve_array_schedule(
    anchors: Sequence[UTCTimeStamp],
    cycles: Sequence[object],
    end: int,
    *,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
    business_day_convention: BusinessDayConvention = BusinessDayConvention.NOS,
    calendar_name: Calendar = Calendar.NC,
) -> tuple[UTCTimeStamp, ...]:
    """
    Generate and business-day-adjust an array-based ACTUS schedule.

    This is the high-level function for creating a piecewise schedule from
    multiple anchors and cycles. It generates the base schedule using array
    logic and applies business day adjustments according to the specified
    convention and calendar.

    Args:
        anchors: Sequence of UTC UNIX timestamps marking schedule segment starts
        cycles: Sequence of ACTUS cycle strings, parallel to anchors
        end: UTC UNIX timestamp upper bound (inclusive)
        end_of_month_convention: How to handle month-end dates for month-based cycles
        business_day_convention: How to adjust dates that fall on non-business days
        calendar_name: Which calendar defines business days vs. holidays

    Returns:
        Tuple of UTC UNIX timestamps with business day adjustments applied

    Raises:
        UnsupportedActusFeatureError: If business_day_convention is not NO_SHIFT
        UnsupportedActusFeatureError: If calendar_name is not NO_CALENDAR
        ValueError: If anchors and cycles have different lengths

    Note:
        V1 implementation only supports:
        - BusinessDayConvention: NO_SHIFT (no adjustments)
        - Calendar: NO_CALENDAR (all days are business days)
    """

    if business_day_convention != BusinessDayConvention.NOS:
        raise UnsupportedActusFeatureError(
            "Supported Business Day Convention: NO_SHIFT"
        )
    if calendar_name != Calendar.NC:
        raise UnsupportedActusFeatureError("Supported Calendar: NO_CALENDAR")

    base_dates = generate_array_schedule(
        anchors,
        cycles,
        end,
        end_of_month_convention=end_of_month_convention,
    )
    return tuple(base_date for base_date in base_dates)
