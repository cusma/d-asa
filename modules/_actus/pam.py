# pyright: reportMissingModuleSource=false
from algopy import Account, Asset, Global, UInt64, arc4

from modules._core_financial.common import CoreFinancialCommonMixin
from smart_contracts import abi_types as typ
from smart_contracts import errors as err


class PAMCoreMixin(CoreFinancialCommonMixin):
    """Principal at Maturity (PAM) core."""

    def __init__(self) -> None:
        super().__init__()

    def assert_pay_principal_authorization(self, holding_address: Account) -> None:
        # The reference implementation does not restrict caller authorization
        assert self.status_is_active(), err.UNAUTHORIZED
        self.assert_is_not_asset_defaulted()
        self.assert_is_not_asset_suspended()
        self.assert_valid_holding_address(holding_address)
        units = self.account[holding_address].units
        assert units > 0, err.NO_UNITS
        assert Global.latest_timestamp >= self.maturity_date, err.NOT_MATURE
        # The reference implementation does not assert if there is enough liquidity to repay the principal to all

    @arc4.abimethod
    def asset_config(
        self,
        *,
        denomination_asset_id: Asset,
        settlement_asset_id: Asset,
        principal: UInt64,
        principal_discount: UInt64,
        minimum_denomination: UInt64,
        day_count_convention: arc4.UInt8,
        interest_rate: arc4.UInt16,
        coupon_rates: typ.CouponRates,
        time_events: typ.TimeEvents,
        time_periods: typ.TimePeriods,
    ) -> None:
        """
        Configure the Debt Algorand Standard Application

        Args:
            denomination_asset_id: Denomination asset identifier
            settlement_asset_id: Settlement asset identifier
            principal: Principal, expressed in denomination asset
            principal_discount: Principal discount in bps
            minimum_denomination: Minimum denomination, expressed in denomination asset
            day_count_convention: Day-count convention for interests calculation
            interest_rate: Interest rate in bps
            coupon_rates: Coupon interest rates in bps
            time_events: Time events (strictly ascending order)
            time_periods: Time periods of recurring time events

        Raises:
            UNAUTHORIZED: Not authorized
            ALREADY_CONFIGURED: D-ASA already configured
            INVALID_MINIMUM_DENOMINATION: Minimum denomination is not a divisor of principal
            INVALID_DAY_COUNT_CONVENTION: Invalid day-count convention ID
            INVALID_TIME_EVENTS_LENGTH: Time events length is invalid
            INVALID_TIME: Time events must be set in the future
            INVALID_SORTING: Time events are not sorted correctly
            INVALID_TIME_PERIOD_DURATION: Time period durations must be greater than zero
            INVALID_SETTLEMENT_ASSET: Different settlement asset not supported, must be equal to denomination asset
            INVALID_TIME_PERIODS: Time periods not properly set
            INVALID_TIME_PERIOD_REPETITIONS: Time period repetitions not properly set
            INVALID_COUPON_RATES: Coupon rates not properly set
        """
        self._configure_asset_terms(
            denomination_asset_id=denomination_asset_id,
            settlement_asset_id=settlement_asset_id,
            principal=principal,
            principal_discount=principal_discount,
            minimum_denomination=minimum_denomination,
            day_count_convention=day_count_convention,
            interest_rate=interest_rate,
            coupon_rates=coupon_rates,
            time_events=time_events,
            time_periods=time_periods,
        )
