from algopy import (
    Global,
    OpUpFeeSource,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    ensure_budget,
    subroutine,
)

from smart_contracts.base_d_asa.contract import BaseDAsa

from .. import constants as cst
from .. import errors as err
from .. import types as typ
from . import config as cfg


class FixedCouponBond(
    BaseDAsa,
    state_totals=StateTotals(
        global_bytes=cfg.GLOBAL_BYTES,
        global_uints=cfg.GLOBAL_UINTS,
        local_bytes=cfg.LOCAL_BYTES,
        local_uints=cfg.LOCAL_UINTS,
    ),
):
    """
    Fixed Coupon Bond, placed at nominal value, fixed coupon rates and payment time schedule, principal at maturity.
    """

    def __init__(self) -> None:
        super().__init__()

        # State schema validation
        assert Txn.global_num_byte_slice == cfg.GLOBAL_BYTES, err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

        # Coupons
        self.due_coupons_watermark = UInt64()
        self.paid_coupon_units = UInt64()

    @subroutine
    def assert_coupon_rates(self, coupon_rates: typ.CouponRates) -> None:
        assert coupon_rates.length, err.INVALID_COUPON_RATES

    @subroutine
    def count_due_coupons(self) -> UInt64:
        current_ts = Global.latest_timestamp
        due_coupons = self.due_coupons_watermark
        if current_ts >= self.maturity_date:
            due_coupons = self.total_coupons
        elif current_ts > self.issuance_date:
            coupon_idx = UInt64(cfg.FIRST_COUPON_DATE_IDX) + self.due_coupons_watermark
            coupon_due_date = self.time_events.value[coupon_idx].native
            while current_ts >= coupon_due_date:
                ensure_budget(
                    required_budget=UInt64(cfg.OP_UP_COUPON_DUE_COUNTING),
                    fee_source=OpUpFeeSource.GroupCredit,
                )
                coupon_idx += 1
                coupon_due_date = self.time_events.value[coupon_idx].native
            due_coupons = coupon_idx - cfg.FIRST_COUPON_DATE_IDX
        self.due_coupons_watermark = due_coupons
        return due_coupons

    @subroutine
    def coupon_due_date(self, coupon: UInt64) -> UInt64:
        return self.time_events.value[cfg.FIRST_COUPON_DATE_IDX + coupon - 1].native

    @subroutine
    def latest_coupon_due_date(self, due_coupons: UInt64) -> UInt64:
        coupon_due_date = UInt64()
        if due_coupons >= UInt64(1):
            coupon_due_date = self.coupon_due_date(due_coupons)
        return coupon_due_date

    @subroutine
    def next_coupon_due_date(self, due_coupons: UInt64) -> UInt64:
        coupon_due_date = UInt64()
        if due_coupons < self.total_coupons:
            coupon_due_date = self.coupon_due_date(due_coupons + 1)
        return coupon_due_date

    @subroutine
    def all_due_coupons_paid(self, due_coupons: UInt64) -> bool:
        return self.paid_coupon_units >= self.circulating_units * due_coupons

    @subroutine
    def coupon_interest_amount(
        self, principal_amount: UInt64, coupon: UInt64
    ) -> UInt64:
        coupon_rate_bps = self.coupon_rates.value[coupon - 1].native
        return principal_amount * coupon_rate_bps // cst.BPS

    @subroutine
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
            numerator=arc4.UInt64(coupon_accrued_period),
            denominator=arc4.UInt64(coupon_period),
        )

    @subroutine
    def is_accruing_interest(self, due_coupons: UInt64) -> bool:
        return (
            Global.latest_timestamp > self.issuance_date
            and due_coupons < self.total_coupons
        )

    @subroutine
    def accrued_interest_amount(
        self, holding_address: arc4.Address, units: UInt64, due_coupons: UInt64
    ) -> UInt64:
        assert (
            self.account[holding_address].paid_coupons == due_coupons
        ), err.PENDING_COUPON_PAYMENT
        day_count_factor = self.day_count_factor(due_coupons)
        coupon_accrued_period = day_count_factor.numerator.native
        coupon_period = day_count_factor.denominator.native
        next_coupon_rate_bps = self.coupon_rates.value[
            due_coupons
        ].native  # due_coupons is equal to the 0-base idx of next coupon
        return (
            self.account_units_value(holding_address, units)
            * next_coupon_rate_bps
            * coupon_accrued_period
            // (
                cst.BPS * coupon_period
            )  # div-by-zero: coupon_period != 0 due to assert_time_events_sorted checks
        )

    @arc4.abimethod
    def asset_transfer(
        self,
        sender_holding_address: arc4.Address,
        receiver_holding_address: arc4.Address,
        units: arc4.UInt64,
    ) -> arc4.UInt64:
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
            units.native,
        )

        # Transferred units value (must be computed before the transfer)
        sender_unit_value = self.account[sender_holding_address].unit_value
        due_coupons = self.count_due_coupons()
        # Transfers is forbidden in case of pending coupon payments, checked in the accrued interest calculation
        accrued_interest = self.accrued_interest_amount(
            sender_holding_address, units.native, due_coupons
        )

        self.transfer_units(
            sender_holding_address, receiver_holding_address, units.native
        )
        return arc4.UInt64(units.native * sender_unit_value.native + accrued_interest)

    @arc4.abimethod
    def pay_coupon(
        self, holding_address: arc4.Address, payment_info: arc4.DynamicBytes
    ) -> typ.PaymentResult:
        """
        Pay due coupon to an account

        Args:
            holding_address: Account Holding Address
            payment_info: Additional payment information (Optional)

        Returns:
            Paid coupon amount, Payment timestamp, Payment context

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
        units = self.account[holding_address].units.native
        assert units > 0, err.NO_UNITS
        due_coupons = self.count_due_coupons()
        account_paid_coupons = self.account[holding_address].paid_coupons.native
        assert due_coupons > account_paid_coupons, err.NO_DUE_COUPON
        # The following conditions verify if other accounts are still waiting for the payment of previous coupons
        assert self.all_due_coupons_paid(
            account_paid_coupons
        ), err.PENDING_COUPON_PAYMENT
        # The reference implementation does not assert if there is enough liquidity to pay current due coupon to all

        if self.is_payment_executable(holding_address):
            payment_amount = self.coupon_interest_amount(
                self.account_total_units_value(holding_address),
                account_paid_coupons + 1,
            )
            # The reference implementation has on-chain payment agent
            self.assert_enough_funds(payment_amount)
            self.pay(self.account[holding_address].payment_address, payment_amount)
        else:
            # Accounts suspended or not opted in at the time of payments must not stall the D-ASA
            payment_amount = UInt64()

        self.account[holding_address].paid_coupons = arc4.UInt64(
            self.account[holding_address].paid_coupons.native + 1
        )
        self.paid_coupon_units += units
        return typ.PaymentResult(
            amount=arc4.UInt64(payment_amount),
            timestamp=arc4.UInt64(Global.latest_timestamp),
            context=payment_info.copy(),  # TODO: Add info on failed payment
        )

    @arc4.abimethod
    def pay_principal(
        self, holding_address: arc4.Address, payment_info: arc4.DynamicBytes
    ) -> typ.PaymentResult:
        """
        Pay the outstanding principal to an account

        Args:
            holding_address: Account Holding Address
            payment_info: Additional payment information (Optional)

        Returns:
            Paid principal amount, Payment timestamp, Payment context

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            NO_UNITS: No D-ASA units
            NOT_MATURE: Not mature
            PENDING_COUPON_PAYMENT: Pending due coupon payment
        """
        self.assert_pay_principal_authorization(holding_address)

        # Principal payment is forbidden in case of pending coupon payments
        assert self.all_due_coupons_paid(
            self.count_due_coupons()
        ), err.PENDING_COUPON_PAYMENT
        # The reference implementation does not assert if there is enough liquidity to pay the principal to all

        if self.is_payment_executable(holding_address):
            payment_amount = self.account_total_units_value(holding_address)
            # The reference implementation has on-chain payment agent
            self.assert_enough_funds(payment_amount)
            self.pay(self.account[holding_address].payment_address, payment_amount)
        else:
            # Accounts suspended or not opted in at the time of payments must not stall the D-ASA
            payment_amount = UInt64()

        self.update_supply_after_principal_payment(holding_address)
        return typ.PaymentResult(
            amount=arc4.UInt64(payment_amount),
            timestamp=arc4.UInt64(Global.latest_timestamp),
            context=payment_info.copy(),  # TODO: Add info on failed payment
        )

    @arc4.abimethod(readonly=True)
    def get_account_units_current_value(
        self, holding_address: arc4.Address, units: arc4.UInt64
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
        assert (
            0 < units <= self.account[holding_address].units.native
        ), err.INVALID_UNITS

        # Value during primary distribution and at maturity
        account_units_nominal_value = self.account_units_value(
            holding_address, units.native
        )
        # Accruing interest during primary distribution and at maturity
        accrued_interest = UInt64()
        numerator = UInt64()
        denominator = UInt64()

        # Accruing interest
        due_coupons = self.count_due_coupons()
        if self.is_accruing_interest(due_coupons):
            day_count_factor = self.day_count_factor(due_coupons)
            # Account units current value calculation fails in case of pending coupon payments, checked in the accrued
            # interest calculation
            accrued_interest = self.accrued_interest_amount(
                holding_address, units.native, due_coupons
            )
            numerator = day_count_factor.numerator.native
            denominator = day_count_factor.denominator.native
        return typ.CurrentUnitsValue(
            units_value=arc4.UInt64(account_units_nominal_value),
            accrued_interest=arc4.UInt64(accrued_interest),
            day_count_factor=typ.DayCountFactor(
                numerator=arc4.UInt64(numerator),
                denominator=arc4.UInt64(denominator),
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
    def get_payment_amount(self, holding_address: arc4.Address) -> typ.PaymentAmounts:
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
            paid_coupons = self.account[holding_address].paid_coupons.native
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
            interest=arc4.UInt64(interest_amount),
            principal=arc4.UInt64(principal_amount),
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
            numerator = day_count_factor.numerator.native
            denominator = day_count_factor.denominator.native
        return typ.CouponsInfo(
            total_coupons=arc4.UInt64(self.total_coupons),
            due_coupons=arc4.UInt64(due_coupons),
            next_coupon_due_date=arc4.UInt64(next_coupon_due_date),
            day_count_factor=typ.DayCountFactor(
                numerator=arc4.UInt64(numerator),
                denominator=arc4.UInt64(denominator),
            ),
            all_due_coupons_paid=arc4.Bool(all_due_coupons_paid),
        )
