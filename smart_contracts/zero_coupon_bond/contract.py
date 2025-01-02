# pyright: reportMissingModuleSource=false
from algopy import (
    Global,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    subroutine,
)

from smart_contracts.base_d_asa.contract import BaseDAsa

from .. import constants as cst
from .. import errors as err
from .. import types as typ
from . import config as cfg


class ZeroCouponBond(
    BaseDAsa,
    state_totals=StateTotals(
        global_bytes=cfg.GLOBAL_BYTES,
        global_uints=cfg.GLOBAL_UINTS,
        local_bytes=cfg.LOCAL_BYTES,
        local_uints=cfg.LOCAL_UINTS,
    ),
):
    """
    Zero Coupon Bond, placed at discount, fixed interest rate, principal at maturity.
    """

    def __init__(self) -> None:
        super().__init__()

        # State schema validation
        assert Txn.global_num_byte_slice == cfg.GLOBAL_BYTES, err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

    @subroutine
    def day_count_factor(self) -> typ.DayCountFactor:
        # The reference implementation supports only the Actual/Actual and Continuous day-count conventions
        accrued_period = Global.latest_timestamp - self.issuance_date
        principal_period = self.maturity_date - self.issuance_date
        if self.day_count_convention == UInt64(cst.DCC_A_A):
            accrued_period = self.days_in(accrued_period)
            principal_period = self.days_in(principal_period)
        return typ.DayCountFactor(
            numerator=arc4.UInt64(accrued_period),
            denominator=arc4.UInt64(principal_period),
        )

    @subroutine
    def accrued_interest_amount(
        self, holding_address: arc4.Address, units: UInt64
    ) -> UInt64:
        day_count_factor = self.day_count_factor()
        accrued_period = day_count_factor.numerator.native
        principal_period = day_count_factor.denominator.native
        return (
            self.account_units_value(holding_address, units)
            * self.interest_rate
            * accrued_period
            // (
                cst.BPS * principal_period
            )  # div-by-zero: principal_period != 0 due to assert_time_events_sorted checks
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
        """
        self.assert_asset_transfer_preconditions(
            sender_holding_address,
            receiver_holding_address,
            units.native,
        )

        # Transferred units value (must be computed before the transfer)
        sender_unit_value = self.account[sender_holding_address].unit_value
        accrued_interest = self.accrued_interest_amount(
            sender_holding_address, units.native
        )

        self.transfer_units(
            sender_holding_address, receiver_holding_address, units.native
        )
        return arc4.UInt64(units.native * sender_unit_value.native + accrued_interest)

    @arc4.abimethod
    def pay_principal(
        self, holding_address: arc4.Address, payment_info: arc4.DynamicBytes
    ) -> typ.PaymentResult:
        """
        Pay the outstanding principal and interest to an account

        Args:
            holding_address: Account Holding Address
            payment_info: Additional payment information (Optional)

        Returns:
            Paid amount, Payment timestamp, Payment context

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            NO_UNITS: No D-ASA units
            NOT_MATURE: Not mature
        """
        self.assert_pay_principal_authorization(holding_address)
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
        """
        assert (
            self.primary_distribution_opening_date
            and Global.latest_timestamp >= self.primary_distribution_opening_date
        ), err.NO_PRIMARY_DISTRIBUTION
        self.assert_valid_holding_address(holding_address)
        assert (
            0 < units <= self.account[holding_address].units.native
        ), err.INVALID_UNITS

        account_units_nominal_value = self.account_units_value(
            holding_address, units.native
        )
        account_units_discount = (
            account_units_nominal_value * self.interest_rate // cst.BPS
        )

        # Value during primary distribution
        account_units_current_value = (
            account_units_nominal_value - account_units_discount
        )

        # Accruing interest during primary distribution and at maturity
        accrued_interest = UInt64()
        numerator = UInt64()
        denominator = UInt64()

        # Accruing interest
        if self.issuance_date <= Global.latest_timestamp < self.maturity_date:
            day_count_factor = self.day_count_factor()
            accrued_interest = self.accrued_interest_amount(
                holding_address, units.native
            )
            numerator = day_count_factor.numerator.native
            denominator = day_count_factor.denominator.native

        # Value at maturity
        if Global.latest_timestamp >= self.maturity_date:
            account_units_current_value = account_units_nominal_value

        return typ.CurrentUnitsValue(
            units_value=arc4.UInt64(account_units_current_value),
            accrued_interest=arc4.UInt64(accrued_interest),
            day_count_factor=typ.DayCountFactor(
                numerator=arc4.UInt64(numerator),
                denominator=arc4.UInt64(denominator),
            ),
        )

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
            INVALID_PAYMENT_INDEX: Invalid 1-based payment index
        """
        self.assert_valid_holding_address(holding_address)
        interest_amount = UInt64()
        principal_amount = UInt64()
        if self.status_is_active():
            principal_amount = self.account_total_units_value(holding_address)
            interest_amount = principal_amount * self.interest_rate // cst.BPS
        return typ.PaymentAmounts(
            interest=arc4.UInt64(interest_amount),
            principal=arc4.UInt64(principal_amount),
        )
