"""ACTUS Contract Attributes: Basic Fixed-Income Maturities"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .day_count import (
    BusinessDayConvention,
    Calendar,
    DayCountConvention,
    EndOfMonthConvention,
)
from .errors import UnsupportedActusFeatureError
from .registry import DAY_COUNT_CONVENTION_IDS, REJECTED_BDC, SUPPORTED_CONTRACT_TYPES
from .schedule import Cycle
from .unix_time import UTCTimeStamp


@dataclass(frozen=True, slots=True)
class ContractAttributes:
    """
    D-ASA Contract attributes.

    Note: D-ASA supports a subset of ACTUS contract attributes.
    """

    # Contract
    contract_id: int
    contract_type: str

    # Time
    status_date: UTCTimeStamp
    initial_exchange_date: UTCTimeStamp
    maturity_date: UTCTimeStamp | None

    # Principal
    notional_principal: int | float | Decimal
    premium_discount_at_ied: int | float | Decimal
    next_principal_redemption_amount: int | float | Decimal | None = None
    principal_redemption_cycle: Cycle | None = None
    principal_redemption_anchor: UTCTimeStamp | None = None
    amortization_date: UTCTimeStamp | None = None

    # Interest
    nominal_interest_rate: int | float | Decimal = 0
    interest_payment_anchor: UTCTimeStamp | None = None
    interest_payment_cycle: Cycle | None = None
    interest_calculation_base_anchor: UTCTimeStamp | None = None
    interest_calculation_base_cycle: Cycle | None = None
    rate_reset_anchor: UTCTimeStamp | None = None
    rate_reset_cycle: Cycle | None = None
    rate_reset_spread: int | float | Decimal = 0
    rate_reset_multiplier: int | float | Decimal = 1
    rate_reset_floor: int | float | Decimal = 0
    rate_reset_cap: int | float | Decimal = 0
    rate_reset_next: int | float | Decimal | None = None

    # Day Count Convention
    day_count_convention: DayCountConvention = DayCountConvention.A360
    business_day_convention: BusinessDayConvention = BusinessDayConvention.NOS
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD
    calendar: Calendar = Calendar.NC

    # Arrays
    array_pr_anchor: list[UTCTimeStamp] | None = None
    array_pr_cycle: list[Cycle] | None = None
    array_pr_next: list[int | float | Decimal] | None = None
    array_increase_decrease: list[Literal["INC", "DEC"]] | None = None

    def __post_init__(self) -> None:
        """Validate contract attributes."""
        # Extract base contract type (e.g., "PAM" from "PAM:ZCB")
        base_contract_type = (
            self.contract_type.split(":")[0]
            if ":" in self.contract_type
            else self.contract_type
        )

        if base_contract_type not in SUPPORTED_CONTRACT_TYPES:
            raise UnsupportedActusFeatureError(
                f"Unsupported ACTUS contract type: {self.contract_type}"
            )

        if (
            self.day_count_convention is not None
            and self.day_count_convention not in DAY_COUNT_CONVENTION_IDS.values()
        ):
            raise UnsupportedActusFeatureError(
                f"Unsupported day count convention: {self.day_count_convention}"
            )

        if self.business_day_convention in REJECTED_BDC:
            raise UnsupportedActusFeatureError(
                f"Unsupported business day convention {self.business_day_convention.name}. "
            )


def make_pam_zero_coupon_bond(
    *,
    contract_id: int,
    status_date: UTCTimeStamp,
    initial_exchange_date: UTCTimeStamp,
    maturity_date: UTCTimeStamp,
    notional_principal: int | float | Decimal,
    premium_discount_at_ied: int | float | Decimal,
    day_count_convention: DayCountConvention | None = DayCountConvention.A360,
    business_day_convention: BusinessDayConvention | None = BusinessDayConvention.NOS,
    end_of_month_convention: EndOfMonthConvention | None = EndOfMonthConvention.SD,
    calendar: Calendar | None = Calendar.NC,
) -> ContractAttributes:
    """Build a PAM Zero Coupon Bond (ZCB) profile."""
    return ContractAttributes(
        contract_id=contract_id,
        contract_type="PAM:ZCB",
        status_date=status_date,
        initial_exchange_date=initial_exchange_date,
        maturity_date=maturity_date,
        notional_principal=notional_principal,
        premium_discount_at_ied=premium_discount_at_ied,
        nominal_interest_rate=0,
        day_count_convention=day_count_convention,
        business_day_convention=business_day_convention,
        end_of_month_convention=end_of_month_convention,
        calendar=calendar,
    )


def make_pam_fixed_coupon_bond_profile(
    *,
    contract_id: int,
    status_date: UTCTimeStamp,
    initial_exchange_date: UTCTimeStamp,
    maturity_date: UTCTimeStamp,
    notional_principal: int | float | Decimal,
    nominal_interest_rate: int | float | Decimal,
    day_count_convention: DayCountConvention | None = DayCountConvention.A360,
    business_day_convention: BusinessDayConvention | None = BusinessDayConvention.NOS,
    end_of_month_convention: EndOfMonthConvention | None = EndOfMonthConvention.SD,
    calendar: Calendar | None = Calendar.NC,
    interest_payment_cycle: Cycle,
    interest_payment_anchor: UTCTimeStamp,
) -> ContractAttributes:
    """Build a PAM Fixed Coupon Bond (FCB) with a fixed interest rate profile."""
    return ContractAttributes(
        contract_id=contract_id,
        contract_type="PAM:FCB",
        status_date=status_date,
        initial_exchange_date=initial_exchange_date,
        maturity_date=maturity_date,
        notional_principal=notional_principal,
        premium_discount_at_ied=0,
        nominal_interest_rate=nominal_interest_rate,
        day_count_convention=day_count_convention,
        business_day_convention=business_day_convention,
        end_of_month_convention=end_of_month_convention,
        calendar=calendar,
        interest_payment_cycle=interest_payment_cycle,
        interest_payment_anchor=interest_payment_anchor,
    )
