from algopy import Account, Box, Global, OpUpFeeSource, UInt64, arc4, ensure_budget

from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import errors as err
from smart_contracts import config as fixed_cfg

from .common import CoreFinancialCommonMixin


class CouponCashflowMixin(CoreFinancialCommonMixin):
    """Coupon cashflow primitives shared by PAM+coupon and PBN+coupon products."""

    def __init__(self) -> None:
        super().__init__()
        self.paid_coupon_units = UInt64()

    def all_due_coupons_paid(self, due_coupons: UInt64) -> bool:
        return self.paid_coupon_units >= self.circulating_units * due_coupons

    def assert_no_pending_coupon_payment(
        self, holding_address: Account, due_coupons: UInt64
    ) -> None:
        assert (
            self.account[holding_address].paid_coupons == due_coupons
        ), err.PENDING_COUPON_PAYMENT

    def core_prepare_coupon_payment(
        self, holding_address: Account
    ) -> tuple[UInt64, UInt64]:
        assert self.status_is_active(), err.UNAUTHORIZED
        self.assert_is_not_asset_defaulted()
        self.assert_is_not_asset_suspended()
        self.assert_valid_holding_address(holding_address)

        units = self.account[holding_address].units
        assert units > 0, err.NO_UNITS

        due_coupons = self.count_due_coupons()
        account_paid_coupons = self.account[holding_address].paid_coupons
        assert due_coupons > account_paid_coupons, err.NO_DUE_COUPON
        # The following conditions verify if other accounts are still waiting for the payment of previous coupons
        assert self.all_due_coupons_paid(
            account_paid_coupons
        ), err.PENDING_COUPON_PAYMENT

        payment_amount = self._compute_coupon_payment_amount(
            holding_address, account_paid_coupons
        )
        return payment_amount, units

    def core_apply_coupon_payment(
        self, holding_address: Account, units: UInt64
    ) -> None:
        self.account[holding_address].paid_coupons += 1
        self.paid_coupon_units += units

    def core_prepare_transfer_with_coupon(
        self, sender_holding_address: Account, units: UInt64
    ) -> UInt64:
        # Transfer is forbidden in case of pending coupon payments
        due_coupons = self.count_due_coupons()
        self.assert_no_pending_coupon_payment(sender_holding_address, due_coupons)
        return self.accrued_interest_amount(sender_holding_address, units, due_coupons)

    def core_prepare_principal_payment(self, holding_address: Account) -> UInt64:
        self.assert_pay_principal_authorization(holding_address)
        # Principal payment is forbidden in case of pending coupon payments
        assert self.all_due_coupons_paid(
            self.count_due_coupons()
        ), err.PENDING_COUPON_PAYMENT
        return self.account_total_units_value(holding_address)

    def core_apply_principal_payment(self, holding_address: Account) -> None:
        self.update_supply_after_principal_payment(holding_address)

    def _compute_coupon_payment_amount(
        self, _holding_address: Account, _account_paid_coupons: UInt64
    ) -> UInt64:
        return UInt64()

    def accrued_interest_amount(
        self, _holding_address: Account, _units: UInt64, _due_coupons: UInt64
    ) -> UInt64:
        return UInt64()


class FixedCouponCashflowMixin(CouponCashflowMixin):
    """Coupon cashflow formulas and getters for PAM+coupon (fixed coupon bond)."""

    def __init__(self) -> None:
        super().__init__()
        self.coupon_rates = Box(typ.CouponRates, key=cst.BOX_ID_COUPON_RATES)
        self.due_coupons_watermark = UInt64()

    def assert_coupon_rates(self, coupon_rates: typ.CouponRates) -> None:
        assert coupon_rates.length, err.INVALID_COUPON_RATES

    def set_coupon_rates(self, coupon_rates: typ.CouponRates) -> None:
        self.total_coupons = coupon_rates.length
        self.coupon_rates.value = coupon_rates.copy()

    def count_due_coupons(self) -> UInt64:
        current_ts = Global.latest_timestamp
        due_coupons = self.due_coupons_watermark
        if current_ts >= self.maturity_date:
            due_coupons = self.total_coupons
        elif current_ts > self.issuance_date:
            coupon_idx = (
                UInt64(fixed_cfg.FIRST_COUPON_DATE_IDX) + self.due_coupons_watermark
            )
            coupon_due_date = self.time_events.value[coupon_idx]
            while current_ts >= coupon_due_date:
                ensure_budget(
                    required_budget=UInt64(fixed_cfg.OP_UP_COUPON_DUE_COUNTING),
                    fee_source=OpUpFeeSource.GroupCredit,
                )
                coupon_idx += 1
                coupon_due_date = self.time_events.value[coupon_idx]
            due_coupons = coupon_idx - fixed_cfg.FIRST_COUPON_DATE_IDX
        self.due_coupons_watermark = due_coupons
        return due_coupons

    def coupon_due_date(self, coupon: UInt64) -> UInt64:
        return self.time_events.value[fixed_cfg.FIRST_COUPON_DATE_IDX + coupon - 1]

    def latest_coupon_due_date(self, due_coupons: UInt64) -> UInt64:
        coupon_due_date = UInt64()
        if due_coupons >= UInt64(1):
            coupon_due_date = self.coupon_due_date(due_coupons)
        return coupon_due_date

    def next_coupon_due_date(self, due_coupons: UInt64) -> UInt64:
        coupon_due_date = UInt64()
        if due_coupons < self.total_coupons:
            coupon_due_date = self.coupon_due_date(due_coupons + 1)
        return coupon_due_date

    def coupon_interest_amount(
        self, principal_amount: UInt64, coupon: UInt64
    ) -> UInt64:
        coupon_rate_bps = self.coupon_rates.value[coupon - 1].as_uint64()
        return principal_amount * coupon_rate_bps // cst.BPS

    def day_count_factor(self, due_coupons: UInt64) -> typ.DayCountFactor:
        # The reference implementation supports only the Actual/Actual and Continuous day-count conventions
        if not due_coupons:
            accruing_start_time = self.issuance_date
        else:
            accruing_start_time = self.latest_coupon_due_date(due_coupons)
        coupon_accrued_period = Global.latest_timestamp - accruing_start_time
        coupon_period = self.next_coupon_due_date(due_coupons) - accruing_start_time
        if self.day_count_convention == UInt64(cst.DCC_A_A):
            coupon_accrued_period = self.days_in(coupon_accrued_period)
            coupon_period = self.days_in(coupon_period)
        return typ.DayCountFactor(
            numerator=coupon_accrued_period,
            denominator=coupon_period,
        )

    def is_accruing_interest(self, due_coupons: UInt64) -> bool:
        return (
            self.issuance_date != 0
            and Global.latest_timestamp >= self.issuance_date
            and due_coupons < self.total_coupons
        )

    def accrued_interest_amount(
        self, holding_address: Account, units: UInt64, due_coupons: UInt64
    ) -> UInt64:
        # The following assert safeguards the subroutine from forbidden invocations
        self.assert_no_pending_coupon_payment(holding_address, due_coupons)
        day_count_factor = self.day_count_factor(due_coupons)
        coupon_accrued_period = day_count_factor.numerator
        coupon_period = day_count_factor.denominator
        next_coupon_rate_bps = self.coupon_rates.value[due_coupons].as_uint64()
        # due_coupons is equal to the 0-base idx of next coupon
        return (
            self.account_units_value(holding_address, units)
            * next_coupon_rate_bps
            * coupon_accrued_period
            // (cst.BPS * coupon_period)
        )  # div-by-zero: coupon_period != 0 due to assert_time_events_sorted checks

    def _compute_coupon_payment_amount(
        self, holding_address: Account, account_paid_coupons: UInt64
    ) -> UInt64:
        return self.coupon_interest_amount(
            self.account_total_units_value(holding_address),
            account_paid_coupons + 1,
        )

    @arc4.abimethod(readonly=True)
    def get_account_units_current_value(
        self, *, holding_address: Account, units: UInt64
    ) -> typ.CurrentUnitsValue:
        """
        Get account's units current value and accrued interest

        Args:
            holding_address: Account Holding Address
            units: Account's units for the current value calculation

        Returns:
            Units current value in denomination asset, Accrued interest in denomination asset

        Raises:
            NO_PRIMARY_DISTRIBUTION: Primary distribution not yet executed
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            INVALID_UNITS: Invalid amount of units for the account
            PENDING_COUPON_PAYMENT: Pending due coupon payment for the account
        """
        assert (
            self.primary_distribution_opening_date
            and Global.latest_timestamp >= self.primary_distribution_opening_date
        ), err.NO_PRIMARY_DISTRIBUTION
        self.assert_valid_holding_address(holding_address)
        assert 0 < units <= self.account[holding_address].units, err.INVALID_UNITS

        # Value during primary distribution and at maturity
        account_units_nominal_value = self.account_units_value(holding_address, units)
        # Accruing interest during primary distribution and at maturity
        accrued_interest = UInt64()
        numerator = UInt64()
        denominator = UInt64()

        # Accruing interest
        due_coupons = self.count_due_coupons()
        self.assert_no_pending_coupon_payment(holding_address, due_coupons)
        if self.is_accruing_interest(due_coupons):
            day_count_factor = self.day_count_factor(due_coupons)
            accrued_interest = self.accrued_interest_amount(
                holding_address, units, due_coupons
            )
            numerator = day_count_factor.numerator
            denominator = day_count_factor.denominator

        return typ.CurrentUnitsValue(
            units_value=account_units_nominal_value,
            accrued_interest=accrued_interest,
            day_count_factor=typ.DayCountFactor(
                numerator=numerator,
                denominator=denominator,
            ),
        )

    @arc4.abimethod(readonly=True)
    def get_coupon_rates(self) -> typ.CouponRates:
        """
        Get D-ASA coupon rates

        Returns:
            Coupon rates
        """
        coupon_rates = typ.CouponRates()
        if self.status_is_active():
            coupon_rates = self.coupon_rates.value.copy()
        return coupon_rates

    @arc4.abimethod(readonly=True)
    def get_payment_amount(self, *, holding_address: Account) -> typ.PaymentAmounts:
        """
        Get the next payment amount

        Args:
            holding_address: Account Holding Address

        Returns:
            Interest amount in denomination asset, Principal amount in denomination asset

        Raises:
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_valid_holding_address(holding_address)
        interest_amount = UInt64()
        principal_amount = UInt64()
        if self.status_is_active():
            paid_coupons = self.account[holding_address].paid_coupons
            if paid_coupons < self.total_coupons:
                # Coupon Payment
                interest_amount = self.coupon_interest_amount(
                    self.account_total_units_value(holding_address),
                    paid_coupons + 1,
                )
            else:
                # Principal Payment
                principal_amount = self.account_total_units_value(holding_address)
        return typ.PaymentAmounts(
            interest=interest_amount,
            principal=principal_amount,
        )

    @arc4.abimethod(readonly=True)
    def get_coupons_status(self) -> typ.CouponsInfo:
        """
        Get D-ASA coupons status

        Returns:
            Total coupons, Due coupons, Next coupon due date, (Day count factor numerator,
            Day count factor denominator), All due coupons paid
        """
        due_coupons = self.count_due_coupons()
        next_coupon_due_date = self.next_coupon_due_date(due_coupons)
        all_due_coupons_paid = self.all_due_coupons_paid(due_coupons)
        numerator = UInt64()
        denominator = UInt64()
        if self.is_accruing_interest(due_coupons):
            day_count_factor = self.day_count_factor(due_coupons)
            numerator = day_count_factor.numerator
            denominator = day_count_factor.denominator
        return typ.CouponsInfo(
            total_coupons=self.total_coupons,
            due_coupons=due_coupons,
            next_coupon_due_date=next_coupon_due_date,
            day_count_factor=typ.DayCountFactor(
                numerator=numerator,
                denominator=denominator,
            ),
            all_due_coupons_paid=all_due_coupons_paid,
        )


class PerpetualCouponCashflowMixin(CouponCashflowMixin):
    """Coupon cashflow formulas and getters for PBN+coupon (perpetual bond)."""

    def __init__(self) -> None:
        super().__init__()
        self.time_periods = Box(typ.TimePeriods, key=cst.BOX_ID_TIME_PERIODS)
        self.coupon_period = UInt64()

    def assert_time_periods(self, time_periods: typ.TimePeriods) -> None:
        # The perpetual bond defines a single time period for the coupon duration with unlimited repetitions
        assert time_periods.length == UInt64(1), err.INVALID_TIME_PERIODS
        coupon_period_duration = time_periods[0][0]
        repetitions = time_periods[0][1]
        assert coupon_period_duration > UInt64(0), err.INVALID_TIME_PERIOD_DURATION
        assert repetitions == UInt64(0), err.INVALID_TIME_PERIOD_REPETITIONS

    def set_time_periods(self, time_periods: typ.TimePeriods) -> None:
        self.time_periods.value = time_periods.copy()
        self.coupon_period = self.time_periods.value[0][0]

    def count_due_coupons(self) -> UInt64:
        due_coupons = UInt64(0)
        current_ts = Global.latest_timestamp
        if current_ts > self.issuance_date:
            due_coupons = (current_ts - self.issuance_date) // self.coupon_period
            # div-by-zero: coupon_period != 0 due to assert_time_periods checks
        return due_coupons

    def coupon_due_date(self, coupon: UInt64) -> UInt64:
        return self.issuance_date + coupon * self.coupon_period

    def latest_coupon_due_date(self, due_coupons: UInt64) -> UInt64:
        coupon_due_date = UInt64()
        if due_coupons >= UInt64(1):
            coupon_due_date = self.coupon_due_date(due_coupons)
        return coupon_due_date

    def next_coupon_due_date(self, due_coupons: UInt64) -> UInt64:
        return self.coupon_due_date(due_coupons + 1)

    def coupon_interest_amount(
        self, principal_amount: UInt64, _coupon: UInt64
    ) -> UInt64:
        return principal_amount * self.interest_rate // cst.BPS

    def day_count_factor(self, due_coupons: UInt64) -> typ.DayCountFactor:
        # The reference implementation supports only the Actual/Actual and Continuous day-count conventions
        if not due_coupons:
            accruing_start_time = self.issuance_date
        else:
            accruing_start_time = self.latest_coupon_due_date(due_coupons)
        coupon_accrued_period = Global.latest_timestamp - accruing_start_time
        coupon_period = self.coupon_period
        if self.day_count_convention == UInt64(cst.DCC_A_A):
            coupon_accrued_period = self.days_in(coupon_accrued_period)
            coupon_period = self.days_in(coupon_period)
        return typ.DayCountFactor(
            numerator=coupon_accrued_period,
            denominator=coupon_period,
        )

    def is_accruing_interest(self, _due_coupons: UInt64) -> bool:
        return self.issuance_date != 0 and Global.latest_timestamp > self.issuance_date

    def accrued_interest_amount(
        self, holding_address: Account, units: UInt64, due_coupons: UInt64
    ) -> UInt64:
        # The following assert safeguards the subroutine from forbidden invocations
        self.assert_no_pending_coupon_payment(holding_address, due_coupons)
        day_count_factor = self.day_count_factor(due_coupons)
        coupon_accrued_period = day_count_factor.numerator
        coupon_period = day_count_factor.denominator
        return (
            self.account_units_value(holding_address, units)
            * self.interest_rate
            * coupon_accrued_period
            // (cst.BPS * coupon_period)
        )  # div-by-zero: coupon_period != 0 due to assert_time_periods checks

    def _compute_coupon_payment_amount(
        self, holding_address: Account, _account_paid_coupons: UInt64
    ) -> UInt64:
        return self.coupon_interest_amount(
            self.account_total_units_value(holding_address), UInt64(1)
        )

    @arc4.abimethod(readonly=True)
    def get_account_units_current_value(
        self, *, holding_address: Account, units: UInt64
    ) -> typ.CurrentUnitsValue:
        """
        Get account's units current value and accrued interest

        Args:
            holding_address: Account Holding Address
            units: Account's units for the current value calculation

        Returns:
            Units current value in denomination asset, Accrued interest in denomination asset

        Raises:
            NO_PRIMARY_DISTRIBUTION: Primary distribution not yet executed
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            INVALID_UNITS: Invalid amount of units for the account
            PENDING_COUPON_PAYMENT: Pending due coupon payment for the account
        """
        assert (
            self.primary_distribution_opening_date
            and Global.latest_timestamp >= self.primary_distribution_opening_date
        ), err.NO_PRIMARY_DISTRIBUTION
        self.assert_valid_holding_address(holding_address)
        assert 0 < units <= self.account[holding_address].units, err.INVALID_UNITS

        # Value during primary distribution
        account_units_nominal_value = self.account_units_value(holding_address, units)
        # Accruing interest during primary distribution
        accrued_interest = UInt64()
        numerator = UInt64()
        denominator = UInt64()

        # Accruing interest
        due_coupons = self.count_due_coupons()
        self.assert_no_pending_coupon_payment(holding_address, due_coupons)
        if self.is_accruing_interest(due_coupons):
            day_count_factor = self.day_count_factor(due_coupons)
            accrued_interest = self.accrued_interest_amount(
                holding_address, units, due_coupons
            )
            numerator = day_count_factor.numerator
            denominator = day_count_factor.denominator

        return typ.CurrentUnitsValue(
            units_value=account_units_nominal_value,
            accrued_interest=accrued_interest,
            day_count_factor=typ.DayCountFactor(
                numerator=numerator,
                denominator=denominator,
            ),
        )

    @arc4.abimethod(readonly=True)
    def get_payment_amount(self, *, holding_address: Account) -> typ.PaymentAmounts:
        """
        Get the next payment amount

        Args:
            holding_address: Account Holding Address

        Returns:
            Interest amount in denomination asset, Principal amount in denomination asset

        Raises:
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_valid_holding_address(holding_address)
        interest_amount = (
            self.account_total_units_value(holding_address)
            * self.interest_rate
            // cst.BPS
        )
        return typ.PaymentAmounts(
            interest=interest_amount,
            principal=UInt64(0),
        )

    @arc4.abimethod(readonly=True)
    def get_coupons_status(self) -> typ.CouponsInfo:
        """
        Get D-ASA coupons status

        Returns:
            Total coupons, Due coupons, Next coupon due date, (Day count factor numerator,
            Day count factor denominator), All due coupons paid
        """
        due_coupons = self.count_due_coupons() if self.status_is_active() else UInt64()
        next_coupon_due_date = self.next_coupon_due_date(due_coupons)
        all_due_coupons_paid = self.all_due_coupons_paid(due_coupons)
        numerator = UInt64()
        denominator = UInt64()
        if self.is_accruing_interest(due_coupons):
            day_count_factor = self.day_count_factor(due_coupons)
            numerator = day_count_factor.numerator
            denominator = day_count_factor.denominator
        return typ.CouponsInfo(
            total_coupons=self.total_coupons,
            due_coupons=due_coupons,
            next_coupon_due_date=next_coupon_due_date,
            day_count_factor=typ.DayCountFactor(
                numerator=numerator,
                denominator=denominator,
            ),
            all_due_coupons_paid=all_due_coupons_paid,
        )

    @arc4.abimethod(readonly=True)
    def get_time_periods(self) -> typ.TimePeriods:
        """
        Get D-ASA time periods

        Returns:
            Time periods
        """
        time_periods = typ.TimePeriods()
        if self.status_is_active():
            time_periods = self.time_periods.value.copy()
        return time_periods
