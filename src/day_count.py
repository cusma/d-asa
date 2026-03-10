from calendar import monthrange
from datetime import datetime
from enum import IntEnum

from smart_contracts import enums
from smart_contracts.constants import DAY_2_SEC

from .unix_time import UTCTimeStamp, timestamp_to_datetime


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
            current += DAY_2_SEC
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
                current -= DAY_2_SEC

    # Preceding conventions (shift backward)
    elif business_day_convention in (
        BusinessDayConvention.SHIFT_CALCULATE_PRECEDING,
        BusinessDayConvention.SHIFT_CALCULATE_MODIFIED_PRECEDING,
        BusinessDayConvention.CALCULATE_SHIFT_PRECEDING,
        BusinessDayConvention.CALCULATE_SHIFT_MODIFIED_PRECEDING,
    ):
        while not is_business_day(current, calendar):
            current -= DAY_2_SEC
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
                current += DAY_2_SEC

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
