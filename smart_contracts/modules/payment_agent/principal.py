from algopy import Account, Bytes, Global, UInt64, arc4

from smart_contracts import abi_types as typ

from .common import PaymentAgentCommonMixin


class PrincipalPaymentAgentMixin(PaymentAgentCommonMixin):
    """Executes principal cashflows computed by the core financial module."""

    @arc4.abimethod
    def pay_principal(
        self, *, holding_address: Account, payment_info: Bytes
    ) -> typ.PaymentResult:
        """
        Pay the outstanding principal to an account

        Args:
            holding_address: Account Holding Address
            payment_info: Additional payment information (Optional)

        Returns:
            Paid principal amount in denomination asset, Payment timestamp, Payment context

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            NO_UNITS: No D-ASA units
            NOT_MATURE: Not mature
        """
        self.assert_payment_authorization(holding_address)
        payment_amount = self.core_prepare_principal_payment(holding_address)
        # The reference implementation does not assert if there is enough liquidity to pay the principal to all

        if self.is_payment_executable(holding_address):
            # The reference implementation has on-chain payment agent
            self.assert_enough_funds(payment_amount)
            # The reference implementation has the same asset for denomination and settlement, no conversion needed
            self.pay(self.account[holding_address].payment_address, payment_amount)
        else:
            # Accounts suspended or not opted in at the time of payments must not stall the D-ASA
            payment_amount = UInt64()

        self.core_apply_principal_payment(holding_address)
        return typ.PaymentResult(
            amount=payment_amount,
            timestamp=Global.latest_timestamp,
            context=payment_info,  # TODO: Add info on failed payment
        )
