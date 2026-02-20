# pyright: reportMissingModuleSource=false
from algopy import (
    Account,
    Bytes,
    Global,
    StateTotals,
    Txn,
    UInt64,
    arc4,
)

from smart_contracts.base_d_asa.contract import BaseDAsa

from .. import abi_types as typ
from .. import constants as cst
from .. import errors as err
from . import config as cfg


class PerpetualBond(
    BaseDAsa,
    state_totals=StateTotals(
        global_bytes=cfg.GLOBAL_BYTES,
        global_uints=cfg.GLOBAL_UINTS,
        local_bytes=cfg.LOCAL_BYTES,
        local_uints=cfg.LOCAL_UINTS,
    ),
):
    """
    Perpetual Bond, variable interest rate, not callable.
    """

    def __init__(self) -> None:
        super().__init__()

        # State schema validation
        assert Txn.global_num_byte_slice == cfg.GLOBAL_BYTES, err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

        # Coupons
        self.coupon_period = UInt64()
        self.paid_coupon_units = UInt64()

    def assert_time_schedule_limits(self, time_events: typ.TimeEvents) -> None:
        # The perpetual bond has undefined coupons (total_coupons = 0) and no maturity date
        assert (
            time_events.length == self.total_coupons + cfg.TIME_SCHEDULE_LIMITS
        ), err.INVALID_TIME_EVENTS_LENGTH

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

    def all_due_coupons_paid(self, due_coupons: UInt64) -> bool:
        return self.paid_coupon_units >= self.circulating_units * due_coupons

    def assert_no_pending_coupon_payment(
        self, holding_address: Account, due_coupons: UInt64
    ) -> None:
        assert (
            self.account[holding_address].paid_coupons == due_coupons
        ), err.PENDING_COUPON_PAYMENT

    def coupon_interest_amount(self, principal_amount: UInt64) -> UInt64:
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

    def is_accruing_interest(self) -> bool:
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
            // (
                cst.BPS * coupon_period
            )  # div-by-zero: coupon_period != 0 due to assert_time_periods checks
        )

    @arc4.abimethod
    def asset_transfer(
        self,
        *,
        sender_holding_address: Account,
        receiver_holding_address: Account,
        units: UInt64,
    ) -> UInt64:
        """
        Transfer D-ASA units between accounts

        Args:
            sender_holding_address: Sender Account Holding Address
            receiver_holding_address: Receiver Account Holding Address
            units: Amount of D-ASA units to transfer

        Returns:
            Transferred actualized value in denomination asset

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            SECONDARY_MARKET_CLOSED: Secondary market is closed
            OVER_TRANSFER: Insufficient sender units to transfer
            NON_FUNGIBLE_UNITS: Sender and receiver units are not fungible
            PENDING_COUPON_PAYMENT: Pending due coupon payment
        """
        self.assert_asset_transfer_preconditions(
            sender_holding_address,
            receiver_holding_address,
            units,
        )

        # Transfer is forbidden in case of pending coupon payments
        due_coupons = self.count_due_coupons()
        self.assert_no_pending_coupon_payment(sender_holding_address, due_coupons)

        # Transferred units value (must be computed before the transfer)
        sender_unit_value = self.account[sender_holding_address].unit_value
        accrued_interest = self.accrued_interest_amount(
            sender_holding_address, units, due_coupons
        )

        self.transfer_units(sender_holding_address, receiver_holding_address, units)
        return units * sender_unit_value + accrued_interest

    @arc4.abimethod
    def pay_coupon(
        self, *, holding_address: Account, payment_info: Bytes
    ) -> typ.PaymentResult:
        """
        Pay due coupon to an account

        Args:
            holding_address: Account Holding Address
            payment_info: Additional payment information (Optional)

        Returns:
            Paid coupon amount in denomination asset, Payment timestamp, Payment context

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            NO_UNITS: No D-ASA units
            NO_DUE_COUPON: No due coupon to pay
            PENDING_COUPON_PAYMENT: Pending due coupon payment
        """
        # The reference implementation does not restrict caller authorization
        assert self.status_is_active(), err.UNAUTHORIZED
        self.assert_is_not_defaulted()
        self.assert_is_not_suspended()
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
        # The reference implementation does not assert if there is enough liquidity to pay current due coupon to all

        if self.is_payment_executable(holding_address):
            payment_amount = self.coupon_interest_amount(
                self.account_total_units_value(holding_address)
            )
            # The reference implementation has on-chain payment agent
            self.assert_enough_funds(payment_amount)
            # The reference implementation has the same asset for denomination and settlement, no conversion needed
            self.pay(self.account[holding_address].payment_address, payment_amount)
        else:
            # Accounts suspended or not opted in at the time of payments must not stall the D-ASA
            payment_amount = UInt64()

        self.account[holding_address].paid_coupons += 1
        self.paid_coupon_units += units
        return typ.PaymentResult(
            amount=payment_amount,
            timestamp=Global.latest_timestamp,
            context=payment_info,  # TODO: Add info on failed payment
        )

    @arc4.abimethod
    def update_interest_rate(self, *, interest_rate: arc4.UInt16) -> UInt64:
        """
        Update variable interest rates in bps

        Args:
            interest_rate: Interest rate in bps

        Returns:
            Timestamp of the update

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            PENDING_COUPON_PAYMENT: Pending due coupon payment
        """
        self.assert_caller_is_interest_oracle()
        self.assert_is_not_defaulted()
        self.assert_is_not_suspended()
        due_coupons = self.count_due_coupons()
        assert self.all_due_coupons_paid(due_coupons), err.PENDING_COUPON_PAYMENT

        # Update interest rate
        self.interest_rate = interest_rate.as_uint64()
        return Global.latest_timestamp

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
        if self.is_accruing_interest():
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
        if self.is_accruing_interest():
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
