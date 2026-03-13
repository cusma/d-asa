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
    ACTUS contract attributes for fixed-income instruments.

    Represents the complete specification of a financial contract following
    ACTUS standards. D-ASA supports a subset of ACTUS contract types including
    PAM, LAM, NAM, ANN, LAX, and CLM.

    Attributes:
        contract_id: Unique identifier for the contract.
        contract_type: ACTUS contract type (e.g., "PAM", "PAM:ZCB", "LAM").

        status_date: Reference date for contract state (must precede IED).
        initial_exchange_date: Date when principal is initially exchanged.
        maturity_date: Final maturity date when contract terminates.

        notional_principal: Principal amount of the contract.
        premium_discount_at_ied: Premium/discount adjustment at IED
            (positive for discount, negative for premium).
        next_principal_redemption_amount: Fixed payment amount per period.
        principal_redemption_cycle: Frequency of principal payments.
        principal_redemption_anchor: Anchor date for principal schedule.
        amortization_date: Start date for amortization (ANN contracts).

        nominal_interest_rate: Annual interest rate (e.g., 0.05 for 5%).
        interest_payment_anchor: Anchor date for interest payment schedule.
        interest_payment_cycle: Frequency of interest payments.
        interest_calculation_base_anchor: Anchor for interest calculation base.
        interest_calculation_base_cycle: Cycle for calculation base adjustments.
        rate_reset_anchor: Anchor date for rate reset schedule.
        rate_reset_cycle: Frequency of interest rate resets.
        rate_reset_spread: Spread added to reset rate.
        rate_reset_multiplier: Multiplier applied to reset rate.
        rate_reset_floor: Minimum rate after reset.
        rate_reset_cap: Maximum rate after reset.
        rate_reset_next: Next known reset rate value.

        day_count_convention: Method for calculating year fractions (default: A360).
        business_day_convention: How to handle non-business days (default: NOS).
        end_of_month_convention: End-of-month adjustment rules (default: SD).
        calendar: Calendar for business day calculations (default: NC).

        array_pr_anchor: Array of principal redemption anchor dates (LAX).
        array_pr_cycle: Array of principal redemption cycles (LAX).
        array_pr_next: Array of principal redemption amounts (LAX).
        array_increase_decrease: Array indicating principal direction (LAX).

    Example:
        >>> from decimal import Decimal
        >>> contract = ContractAttributes(
        ...     contract_id=1,
        ...     contract_type="PAM:ZCB",
        ...     status_date=1609459200,  # 2021-01-01
        ...     initial_exchange_date=1612137600,  # 2021-02-01
        ...     maturity_date=1643673600,  # 2022-02-01
        ...     notional_principal=Decimal("100000"),
        ...     premium_discount_at_ied=Decimal("0"),
        ... )

    Note:
        D-ASA supports a subset of ACTUS contract attributes.
        Contract subtypes use colon notation (e.g., "PAM:ZCB" for zero coupon bond).
    """

    # Contract
    contract_id: int
    contract_type: str

    # Time
    status_date: UTCTimeStamp
    initial_exchange_date: UTCTimeStamp
    maturity_date: UTCTimeStamp | None

    # Day Count Convention
    day_count_convention: DayCountConvention
    business_day_convention: BusinessDayConvention
    end_of_month_convention: EndOfMonthConvention
    calendar: Calendar

    # Principal
    notional_principal: int | float | Decimal
    premium_discount_at_ied: int | float | Decimal
    next_principal_redemption_amount: int | float | Decimal = 0
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

    # Arrays
    array_pr_anchor: list[UTCTimeStamp] | None = None
    array_pr_cycle: list[Cycle] | None = None
    array_pr_next: list[int | float | Decimal] | None = None
    array_increase_decrease: list[Literal["INC", "DEC"]] | None = None

    def __post_init__(self) -> None:
        """
        Validate contract attributes after initialization.

        Ensures contract type is supported, day count convention is valid,
        and business day convention is compatible with D-ASA.

        Raises:
            UnsupportedActusFeatureError: If contract_type, day_count_convention,
                or business_day_convention are not supported by D-ASA.
        """
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
                f"Unsupported business day convention {self.business_day_convention.name}"
            )


def make_pam_zero_coupon_bond(
    *,
    contract_id: int,
    status_date: UTCTimeStamp,
    initial_exchange_date: UTCTimeStamp,
    maturity_date: UTCTimeStamp,
    notional_principal: int | float | Decimal,
    premium_discount_at_ied: int | float | Decimal,
    day_count_convention: DayCountConvention = DayCountConvention.A360,
    business_day_convention: BusinessDayConvention = BusinessDayConvention.NOS,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
    calendar: Calendar = Calendar.NC,
) -> ContractAttributes:
    """
    Build a PAM Zero Coupon Bond (ZCB) contract.

    Zero coupon bonds pay no periodic interest and return the full principal
    at maturity. The contract_type is set to "PAM:ZCB" with zero interest rate.

    Args:
        contract_id: Unique identifier for the contract.
        status_date: Contract status reference date (must precede IED).
        initial_exchange_date: Date when bond is issued and principal exchanged.
        maturity_date: Date when principal is repaid.
        notional_principal: Face value of the bond.
        premium_discount_at_ied: Premium or discount adjustment at issuance
            (positive for discount, negative for premium).
        day_count_convention: Year fraction calculation method (default: A360).
        business_day_convention: Non-business day handling (default: NOS).
        end_of_month_convention: End-of-month adjustment rules (default: SD).
        calendar: Business calendar for date calculations (default: NC).

    Returns:
        ContractAttributes configured as a zero coupon bond.

    Example:
        >>> from decimal import Decimal
        >>> zcb = make_pam_zero_coupon_bond(
        ...     contract_id=1,
        ...     status_date=1609459200,  # 2021-01-01
        ...     initial_exchange_date=1612137600,  # 2021-02-01
        ...     maturity_date=1643673600,  # 2022-02-01
        ...     notional_principal=Decimal("100000"),
        ...     premium_discount_at_ied=Decimal("0"),
        ... )
        >>> zcb.contract_type
        'PAM:ZCB'
        >>> zcb.nominal_interest_rate
        0
    """
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
    day_count_convention: DayCountConvention = DayCountConvention.A360,
    business_day_convention: BusinessDayConvention = BusinessDayConvention.NOS,
    end_of_month_convention: EndOfMonthConvention = EndOfMonthConvention.SD,
    calendar: Calendar = Calendar.NC,
    interest_payment_cycle: Cycle,
    interest_payment_anchor: UTCTimeStamp,
) -> ContractAttributes:
    """
    Build a PAM Fixed Coupon Bond (FCB) contract.

    Fixed coupon bonds pay periodic interest at a fixed rate and return the
    principal at maturity. The contract_type is set to "PAM:FCB".

    Args:
        contract_id: Unique identifier for the contract.
        status_date: Contract status reference date (must precede IED).
        initial_exchange_date: Date when bond is issued and principal exchanged.
        maturity_date: Date when principal is repaid.
        notional_principal: Face value of the bond.
        nominal_interest_rate: Annual interest rate (e.g., 0.05 for 5%).
        day_count_convention: Year fraction calculation method (default: A360).
        business_day_convention: Non-business day handling (default: NOS).
        end_of_month_convention: End-of-month adjustment rules (default: SD).
        calendar: Business calendar for date calculations (default: NC).
        interest_payment_cycle: Frequency of interest payments (e.g., 6M for semi-annual).
        interest_payment_anchor: Starting date for interest payment schedule.

    Returns:
        ContractAttributes configured as a fixed coupon bond.

    Example:
        >>> from decimal import Decimal
        >>> from d_asa.schedule import Cycle
        >>> fcb = make_pam_fixed_coupon_bond_profile(
        ...     contract_id=2,
        ...     status_date=1609459200,  # 2021-01-01
        ...     initial_exchange_date=1612137600,  # 2021-02-01
        ...     maturity_date=1675209600,  # 2023-02-01
        ...     notional_principal=Decimal("100000"),
        ...     nominal_interest_rate=Decimal("0.05"),  # 5% annual
        ...     interest_payment_cycle=Cycle(count=6, unit="M"),  # Semi-annual
        ...     interest_payment_anchor=1620009600,  # First payment date
        ... )
        >>> fcb.contract_type
        'PAM:FCB'
        >>> fcb.nominal_interest_rate
        Decimal('0.05')
    """
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
