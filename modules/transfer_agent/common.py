from algopy import Account, UInt64, op

from modules.core_financial.common import (
    CoreFinancialCommonMixin,
)
from smart_contracts import errors as err


class TransferAgentCommonMixin(CoreFinancialCommonMixin):
    """Ownership transfer helpers shared across transfer-agent variants."""

    # Hook defaults, implemented by core cashflow mixins.
    def core_prepare_transfer_no_coupon(
        self, _sender_holding_address: Account, _units: UInt64
    ) -> UInt64:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def core_prepare_transfer_with_coupon(
        self, _sender_holding_address: Account, _units: UInt64
    ) -> UInt64:
        op.err(err.INVALID_MIXIN_COMPOSITION)
