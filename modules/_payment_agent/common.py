from algopy import Account, Global, Txn, UInt64, itxn, op

from modules._core_financial.common import (
    CoreFinancialCommonMixin,
)
from smart_contracts import errors as err


class PaymentAgentCommonMixin(CoreFinancialCommonMixin):
    """Settlement execution helpers used by payment methods."""

    def assert_payment_authorization(self, holding_address: Account) -> None:
        if self.op_daemon.value != Global.zero_address:
            assert (
                Txn.sender == self.op_daemon.value
                or Txn.sender == holding_address
                or Txn.sender == self.account[holding_address].payment_address
            ), err.UNAUTHORIZED

    def is_payment_executable(self, holding_address: Account) -> bool:
        return (
            self.account[holding_address].payment_address.is_opted_in(
                self.settlement_asset_id
            )
            and not self.account[holding_address].suspended
        )

    def assert_enough_funds(self, payment_amount: UInt64) -> None:
        assert (
            self.settlement_asset_id.balance(Global.current_application_address)
            >= payment_amount
        ), err.NOT_ENOUGH_FUNDS

    def pay(self, receiver: Account, amount: UInt64) -> None:
        itxn.AssetTransfer(
            xfer_asset=self.settlement_asset_id,
            asset_receiver=receiver,
            asset_amount=amount,
            fee=Global.min_txn_fee,
        ).submit()

    # Hook defaults, implemented by core cashflow mixins.
    def core_prepare_coupon_payment(
        self, _holding_address: Account
    ) -> tuple[UInt64, UInt64]:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def core_apply_coupon_payment(
        self, _holding_address: Account, _units: UInt64
    ) -> None:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def core_prepare_principal_payment(self, _holding_address: Account) -> UInt64:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def core_apply_principal_payment(self, _holding_address: Account) -> None:
        op.err(err.INVALID_MIXIN_COMPOSITION)
