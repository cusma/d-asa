from algopy import Account, Global, UInt64, arc4

from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import errors as err

from .common import CoreFinancialCommonMixin


class NoCouponCashflowMixin(CoreFinancialCommonMixin):
    """Cashflow computation for products without coupons."""

    def assert_interest_rate(self, interest_rate: UInt64) -> None:
        # This subroutine must be used after the principal discount has been set
        assert interest_rate == UInt64(0), err.INVALID_INTEREST_RATE

    def day_count_factor(self) -> typ.DayCountFactor:
        # The reference implementation supports only the Actual/Actual and Continuous day-count conventions
        accrued_period = Global.latest_timestamp - self.issuance_date
        principal_period = self.maturity_date - self.issuance_date
        if self.day_count_convention == UInt64(cst.DCC_A_A):
            accrued_period = self.days_in(accrued_period)
            principal_period = self.days_in(principal_period)
        return typ.DayCountFactor(
            numerator=accrued_period,
            denominator=principal_period,
        )

    def is_accruing_interest(self) -> bool:
        # The check on maturity date ensures D-ASA has been configured as block timestamp cannot be less than 0 (init).
        return self.issuance_date <= Global.latest_timestamp < self.maturity_date

    def accrued_interest_amount(
        self, holding_address: Account, units: UInt64
    ) -> UInt64:
        day_count_factor = self.day_count_factor()
        accrued_period = day_count_factor.numerator
        principal_period = day_count_factor.denominator
        return (
            self.account_units_value(holding_address, units)
            * self.principal_discount
            * accrued_period
            // (cst.BPS * principal_period)
        )  # div-by-zero: principal_period != 0 due to assert_time_events_sorted checks

    def core_prepare_transfer_no_coupon(
        self, sender_holding_address: Account, units: UInt64
    ) -> UInt64:
        return self.accrued_interest_amount(sender_holding_address, units)

    def core_prepare_principal_payment(self, holding_address: Account) -> UInt64:
        self.assert_pay_principal_authorization(holding_address)
        return self.account_total_units_value(holding_address)

    def core_apply_principal_payment(self, holding_address: Account) -> None:
        self.update_supply_after_principal_payment(holding_address)

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
        """
        assert (
            self.primary_distribution_opening_date
            and Global.latest_timestamp >= self.primary_distribution_opening_date
        ), err.NO_PRIMARY_DISTRIBUTION
        self.assert_valid_holding_address(holding_address)
        assert 0 < units <= self.account[holding_address].units, err.INVALID_UNITS

        account_units_nominal_value = self.account_units_value(holding_address, units)
        account_units_discount = (
            account_units_nominal_value * self.principal_discount // cst.BPS
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
        if self.is_accruing_interest():
            day_count_factor = self.day_count_factor()
            accrued_interest = self.accrued_interest_amount(holding_address, units)
            numerator = day_count_factor.numerator
            denominator = day_count_factor.denominator

        # Value at maturity
        if Global.latest_timestamp >= self.maturity_date:
            account_units_current_value = account_units_nominal_value

        return typ.CurrentUnitsValue(
            units_value=account_units_current_value,
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
            INVALID_PAYMENT_INDEX: Invalid 1-based payment index
        """
        self.assert_valid_holding_address(holding_address)
        principal_amount = UInt64()
        if self.status_is_active():
            principal_amount = self.account_total_units_value(holding_address)
        return typ.PaymentAmounts(interest=UInt64(0), principal=principal_amount)
