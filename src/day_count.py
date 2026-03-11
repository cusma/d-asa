from calendar import monthrange
from datetime import datetime
from enum import IntEnum

from smart_contracts import constants as cst
from smart_contracts import enums

from .errors import ActusNormalizationError
from .unix_time import UTCTimeStamp, timestamp_to_datetime


class DayCountConvention(IntEnum):
    """
    Day Count Convention (DCC).

    Method defining how days are counted between two dates. This defines the
    year fraction in accrual calculations for interest and other computations.

    The day count convention affects how interest accrues over time by defining:
    - How many days are in a month
    - How many days are in a year
    - Special rules for month-end dates
    """

    ACTUAL_ACTUAL = enums.DCC_AA
    """Actual/Actual (AA): Year fractions accrue on the basis of the actual
    number of days per month and per year in the respective period."""

    ACTUAL_360 = enums.DCC_A360
    """Actual/360 (A360): Year fractions accrue on the basis of the actual
    number of days per month and 360 days per year in the respective period."""

    ACTUAL_365 = enums.DCC_A365
    """Actual/365 (A365): Year fractions accrue on the basis of the actual
    number of days per month and 365 days per year in the respective period."""

    THIRTY_E_360_ISDA = enums.DCC_30E360ISDA
    """30E/360 ISDA (30E360ISDA): Year fractions accrue on the basis of 30 days
    per month and 360 days per year in the respective period (ISDA method)."""

    THIRTY_E_360 = enums.DCC_30E360
    """30E/360 (30E360): Year fractions accrue on the basis of 30 days per month
    and 360 days per year in the respective period."""

    # Aliases for convenience
    AA = ACTUAL_ACTUAL
    A360 = ACTUAL_360
    A365 = ACTUAL_365
    E30_360_ISDA = THIRTY_E_360_ISDA
    E30_360 = THIRTY_E_360


class Calendar(IntEnum):
    """
    Calendar (CLDR).

    Calendar defines the non-working days which affect the dates of contract
    events (CDE's) in combination with EOMC and BDC. Custom calendars can be
    added as additional enum options.
    """

    NO_CALENDAR = enums.CLDR_NC
    """No holidays defined."""

    MONDAY_TO_FRIDAY = enums.CLDR_MF
    """Saturdays and Sundays are holidays."""

    # Aliases for convenience
    NC = NO_CALENDAR
    MF = MONDAY_TO_FRIDAY


class EndOfMonthConvention(IntEnum):
    """
    End of Month Convention (EOMC).

    When computing schedules a special problem arises if an anchor date is at
    the end of a month and a cycle of monthly or quarterly is applied (yearly
    in the case of leap years only). How do we have to interpret an anchor date
    April 30 plus 1M cycles?

    - EOM: Will jump to the 31st of May, then June 30, July 31 and so on.
    - SD: Will jump to the 30th always with an exception in February.

    This logic applies for all months having 30 or less days and an anchor date
    at the last day. Months with 31 days will at any rate jump to the last of
    the month if anchor date is on the last day.
    """

    SAME_DAY = enums.EOMC_SD
    """Schedule times always fall on the schedule anchor date day of the month."""

    END_OF_MONTH = enums.EOMC_EOM
    """Schedule times fall on the end of every month if the anchor date represents
    the last day of the respective month."""

    # Aliases for convenience
    SD = SAME_DAY
    EOM = END_OF_MONTH


def is_end_of_month(value: datetime) -> bool:
    """Return whether the datetime falls on its month's final day."""

    return value.day == monthrange(value.year, value.month)[1]


def is_business_day(timestamp: UTCTimeStamp, calendar: Calendar = Calendar.NC) -> bool:
    """Return whether a UTC UNIX timestamp falls on a business day for a named calendar."""

    if calendar == Calendar.NO_CALENDAR:
        return True

    return timestamp_to_datetime(timestamp).weekday() < 5


class BusinessDayConvention(IntEnum):
    """
    Business Day Convention (BDC).

    BDC's are linked to a calendar. Calendars have working and non-working days.
    A BDC value other than N means that cash flows cannot fall on non-working
    days, they must be shifted to the next business day (following) or the
    previous one (preceding).

    These two simple rules get refined twofold:
    - Following modified (preceding modified): Same like following (preceding),
      however if a cash flow gets shifted into a new month, then it is shifted
      to preceding (following) business day.
    - Shift/calculate (SC) and calculate/shift (CS). Accrual, principal, and
      possibly other calculations are affected by this choice. In the case of
      SC first the dates are shifted and after the shift cash flows are
      calculated. In the case of CS it is the other way round.

    Note: Does not affect non-cyclical dates such as PRD, MD, TD, IPCED since
    they can be set to the correct date directly.
    """

    NO_SHIFT = enums.BDC_NOS
    """No shift applied to non-business days."""

    SHIFT_CALCULATE_FOLLOWING = enums.BDC_SCF
    """Shift event dates first then calculate accruals etc. Strictly shift to
    the next following business day."""

    SHIFT_CALCULATE_MODIFIED_FOLLOWING = enums.BDC_SCMF
    """Shift event dates first then calculate accruals etc. Shift to the next
    following business day if this falls in the same month. Shift to the most
    recent preceding business day otherwise."""

    CALCULATE_SHIFT_FOLLOWING = enums.BDC_CSF
    """Calculate accruals etc. first then shift event dates. Strictly shift to
    the next following business day."""

    CALCULATE_SHIFT_MODIFIED_FOLLOWING = enums.BDC_CSMF
    """Calculate accruals etc. first then shift event dates. Shift to the next
    following business day if this falls in the same month. Shift to the most
    recent preceding business day otherwise."""

    SHIFT_CALCULATE_PRECEDING = enums.BDC_SCP
    """Shift event dates first then calculate accruals etc. Strictly shift to
    the most recent preceding business day."""

    SHIFT_CALCULATE_MODIFIED_PRECEDING = enums.BDC_SCMP
    """Shift event dates first then calculate accruals etc. Shift to the most
    recent preceding business day if this falls in the same month. Shift to the
    next following business day otherwise."""

    CALCULATE_SHIFT_PRECEDING = enums.BDC_CSP
    """Calculate accruals etc. first then shift event dates. Strictly shift to
    the most recent preceding business day."""

    CALCULATE_SHIFT_MODIFIED_PRECEDING = enums.BDC_CSMP
    """Calculate accruals etc. first then shift event dates. Shift to the most
    recent preceding business day if this falls in the same month. Shift to the
    next following business day otherwise."""

    # Aliases for convenience
    NOS = NO_SHIFT
    SCF = SHIFT_CALCULATE_FOLLOWING
    SCMF = SHIFT_CALCULATE_MODIFIED_FOLLOWING
    CSF = CALCULATE_SHIFT_FOLLOWING
    CSMF = CALCULATE_SHIFT_MODIFIED_FOLLOWING
    SCP = SHIFT_CALCULATE_PRECEDING
    SCMP = SHIFT_CALCULATE_MODIFIED_PRECEDING
    CSP = CALCULATE_SHIFT_PRECEDING
    CSMP = CALCULATE_SHIFT_MODIFIED_PRECEDING


def adjust_to_business_day(
    timestamp: UTCTimeStamp,
    *,
    business_day_convention: BusinessDayConvention,
    calendar: Calendar = Calendar.NC,
) -> UTCTimeStamp:
    """Adjust a UTC UNIX timestamp according to an ACTUS business-day convention."""

    # No shift convention - return timestamp as-is
    if business_day_convention == BusinessDayConvention.NO_SHIFT:
        return timestamp

    # If already a business day, no adjustment needed
    if is_business_day(timestamp, calendar):
        return timestamp

    current = timestamp
    original = timestamp
    original_month = timestamp_to_datetime(timestamp).month

    # Following conventions (shift forward)
    if business_day_convention in (
        BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
        BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
        BusinessDayConvention.CALCULATE_SHIFT_FOLLOWING,
        BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_FOLLOWING,
    ):
        while not is_business_day(current, calendar):
            current += cst.DAY_2_SEC
        # Modified following: if shifted to next month, shift back to preceding
        if (
            business_day_convention
            in (
                BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
                BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_FOLLOWING,
            )
            and timestamp_to_datetime(current).month != original_month
        ):
            current = original
            while not is_business_day(current, calendar):
                current -= cst.DAY_2_SEC

    # Preceding conventions (shift backward)
    elif business_day_convention in (
        BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
        BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
        BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
        BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_PRECEDING,
    ):
        while not is_business_day(current, calendar):
            current -= cst.DAY_2_SEC
        # Modified preceding: if shifted to previous month, shift forward to following
        if (
            business_day_convention
            in (
                BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
                BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_PRECEDING,
            )
            and timestamp_to_datetime(current).month != original_month
        ):
            current = original
            while not is_business_day(current, calendar):
                current += cst.DAY_2_SEC

    return current


def is_calculate_shift(business_day_convention: BusinessDayConvention) -> bool:
    """Return whether the BDC is calculate-then-shift."""

    return business_day_convention in (
        BusinessDayConvention.CALCULATE_SHIFT_FOLLOWING,
        BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_FOLLOWING,
        BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
        BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_PRECEDING,
    )


def is_shift_calculate(business_day_convention: BusinessDayConvention) -> bool:
    """Return whether the BDC is shift-then-calculate."""

    return business_day_convention in (
        BusinessDayConvention.SHIFT_CALCULATE_FOLLOWING,
        BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_FOLLOWING,
        BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
        BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
    )


def year_fraction_fixed(
    start_ts: UTCTimeStamp,
    end_ts: UTCTimeStamp,
    *,
    day_count_convention: int,
    maturity_date: UTCTimeStamp | None,
) -> int:
    """Return a fixed-point year fraction for a supported day-count convention."""
    if end_ts <= start_ts:
        return 0

    if day_count_convention == DayCountConvention.A360:
        return _days_between(start_ts, end_ts) * cst.FIXED_POINT_SCALE // 360
    if day_count_convention == DayCountConvention.A365:
        return _days_between(start_ts, end_ts) * cst.FIXED_POINT_SCALE // 365
    if day_count_convention == DayCountConvention.AA:
        return _year_fraction_actual_actual(start_ts, end_ts)
    if day_count_convention == DayCountConvention.E30_360:
        return _days_30e_360(start_ts, end_ts) * cst.FIXED_POINT_SCALE // 360
    if day_count_convention == DayCountConvention.E30_360_ISDA:
        if maturity_date is None:
            raise ActusNormalizationError("30E/360 ISDA requires maturity_date")
        return (
            _days_30e_360_isda(start_ts, end_ts, maturity_date)
            * cst.FIXED_POINT_SCALE
            // 360
        )
    raise ActusNormalizationError("Unsupported day-count convention")


def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a Gregorian month."""
    return monthrange(year, month)[1]


def _year_fraction_actual_actual(start_ts: UTCTimeStamp, end_ts: UTCTimeStamp) -> int:
    """Return the Actual/Actual year fraction in fixed-point form."""
    start_year, start_month, start_day = _date_parts(start_ts)
    end_year, end_month, end_day = _date_parts(end_ts)
    if start_year == end_year:
        return (
            _days_between(start_ts, end_ts)
            * cst.FIXED_POINT_SCALE
            // _days_in_year(start_year)
        )

    start_day_of_year = _day_of_year(start_year, start_month, start_day)
    end_day_of_year = _day_of_year(end_year, end_month, end_day)
    start_fraction = (
        (_days_in_year(start_year) - (start_day_of_year - 1))
        * cst.FIXED_POINT_SCALE
        // _days_in_year(start_year)
    )
    full_years = max(end_year - start_year - 1, 0) * cst.FIXED_POINT_SCALE
    end_fraction = (
        (end_day_of_year - 1) * cst.FIXED_POINT_SCALE // _days_in_year(end_year)
    )
    return start_fraction + full_years + end_fraction


def _days_between(start_ts: UTCTimeStamp, end_ts: UTCTimeStamp) -> int:
    """Return whole UTC days between two timestamps."""
    if end_ts <= start_ts:
        return 0
    return (end_ts - start_ts) // cst.DAY_2_SEC


def _days_30e_360(start_ts: UTCTimeStamp, end_ts: UTCTimeStamp) -> int:
    """Return the 30E/360 day-count numerator between two timestamps."""
    y1, m1, d1 = _date_parts(start_ts)
    y2, m2, d2 = _date_parts(end_ts)
    if d1 == 31:
        d1 = 30
    if d2 == 31:
        d2 = 30
    return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)


def _days_30e_360_isda(
    start_ts: UTCTimeStamp, end_ts: UTCTimeStamp, maturity_ts: UTCTimeStamp
) -> int:
    """Return the 30E/360 ISDA day-count numerator between two timestamps."""
    y1, m1, d1 = _date_parts(start_ts)
    y2, m2, d2 = _date_parts(end_ts)
    maturity_parts = _date_parts(maturity_ts)
    if _is_last_day_of_feb(y1, m1, d1) or d1 == 31:
        d1 = 30
    if (_is_last_day_of_feb(y2, m2, d2) and (y2, m2, d2) != maturity_parts) or d2 == 31:
        d2 = 30
    return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)


def _days_30_360(start_ts: UTCTimeStamp, end_ts: UTCTimeStamp) -> int:
    """Return the 30/360 bond-basis day-count numerator between two timestamps."""
    y1, m1, d1 = _date_parts(start_ts)
    y2, m2, d2 = _date_parts(end_ts)
    if d1 == 31:
        d1 = 30
    if d1 >= 30 and d2 == 31:
        d2 = 30
    return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)


def _date_parts(timestamp: UTCTimeStamp) -> tuple[int, int, int]:
    """Return the UTC year, month, and day for a timestamp."""
    current = timestamp_to_datetime(timestamp)
    return current.year, current.month, current.day


def _day_of_year(year: int, month: int, day: int) -> int:
    """Return the ordinal day number within a year."""
    month_offsets = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    value = month_offsets[month - 1] + day
    if month > 2 and _is_leap_year(year):
        value += 1
    return value


def _days_in_year(year: int) -> int:
    """Return the number of days in a Gregorian year."""
    return 366 if _is_leap_year(year) else 365


def _is_leap_year(year: int) -> bool:
    """Return whether a Gregorian year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _is_last_day_of_feb(year: int, month: int, day: int) -> bool:
    """Return whether a date is the last day of February."""
    if month != 2:
        return False
    return day == (29 if _is_leap_year(year) else 28)
