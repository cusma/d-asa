from algopy import Account, Bytes, Global, UInt64, arc4

from smart_contracts import abi_types as typ

from .common import PaymentAgentCommonMixin


class CouponPaymentAgentMixin(PaymentAgentCommonMixin):
    """Executes coupon cashflows computed by the core financial module."""

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
        payment_amount, units = self.core_prepare_coupon_payment(holding_address)
        # The reference implementation does not assert if there is enough liquidity to pay current due coupon to all

        if self.is_payment_executable(holding_address):
            # The reference implementation has on-chain payment agent
            self.assert_enough_funds(payment_amount)
            # The reference implementation has the same asset for denomination and settlement, no conversion needed
            self.pay(self.account[holding_address].payment_address, payment_amount)
        else:
            # Accounts suspended or not opted in at the time of payments must not stall the D-ASA
            payment_amount = UInt64()

        self.core_apply_coupon_payment(holding_address, units)
        return typ.PaymentResult(
            amount=payment_amount,
            timestamp=Global.latest_timestamp,
            context=payment_info,  # TODO: Add info on failed payment
        )
