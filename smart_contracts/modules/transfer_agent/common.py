from algopy import Account, UInt64

from smart_contracts.modules.core_financial.common import (
    CoreFinancialCommonMixin,
)


class TransferAgentCommonMixin(CoreFinancialCommonMixin):
    """Ownership transfer helpers shared across transfer-agent variants."""

    # Hook defaults, implemented by core cashflow mixins.
    def core_prepare_transfer_no_coupon(
        self, _sender_holding_address: Account, _units: UInt64
    ) -> UInt64:
        return UInt64()

    def core_prepare_transfer_with_coupon(
        self, _sender_holding_address: Account, _units: UInt64
    ) -> UInt64:
        return UInt64()
