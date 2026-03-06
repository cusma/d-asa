from algopy import Account, Bytes, Global, String, UInt64, arc4

from smart_contracts import abi_types as typ
from smart_contracts import enums
from smart_contracts.events import Event

from .common import PaymentAgentCommonMixin


class CouponPaymentAgentMixin(PaymentAgentCommonMixin):
    """Executes coupon cashflows computed by the core financial module."""

    def _emit_ip(self, *, payoff: UInt64) -> None:
        """Emit Interest Payment (IP) event."""
        arc4.emit(
            Event(
                contract_id=Global.current_application_id.id,
                type=arc4.UInt8(enums.EVT_TYPE_IP),
                type_name=String("IP"),
                time=Global.latest_timestamp,
                payoff=payoff,
                currency_id=self.denomination_asset_id.id,
                currency_unit=self.denomination_asset_id.unit_name,
                nominal_value=self.total_units * self.unit_value,
                nominal_rate_bps=arc4.UInt16(0),  # TODO: Add interest rate
                nominal_accrued=UInt64(0),
            )
        )

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
            SUSPENDED: Suspended operations
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            NO_UNITS: No D-ASA units
            NO_DUE_COUPON: No due coupon to pay
            PENDING_COUPON_PAYMENT: Pending due coupon payment
        """
        payment_amount, units = self.core_prepare_coupon_payment(holding_address)
        self.assert_payment_authorization(holding_address)
        # The reference implementation does not assert if there is enough liquidity to pay current due coupon to all

        if self.is_payment_executable(holding_address):
            # The reference implementation has on-chain payment agent
            self.assert_enough_funds(payment_amount)
            # The reference implementation has the same asset for denomination and settlement, no conversion needed
            self.pay(self.account[holding_address].payment_address, payment_amount)
            self._emit_ip(payoff=payment_amount)
        else:
            # Accounts suspended or not opted in at the time of payments must not stall the D-ASA
            payment_amount = UInt64()

        self.core_apply_coupon_payment(holding_address, units)
        return typ.PaymentResult(
            amount=payment_amount,
            timestamp=Global.latest_timestamp,
            context=payment_info,  # TODO: Add info on failed payment
        )
