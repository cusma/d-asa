from algopy import Account, UInt64, arc4

from .common import TransferAgentCommonMixin


class CouponTransferAgentMixin(TransferAgentCommonMixin):
    """Transfers ownership for products with coupon payment ordering constraints."""

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

        # Transferred units value (must be computed before the transfer)
        sender_unit_value = self.account[sender_holding_address].unit_value
        accrued_interest = self.core_prepare_transfer_with_coupon(
            sender_holding_address, units
        )

        self.transfer_units(sender_holding_address, receiver_holding_address, units)
        return units * sender_unit_value + accrued_interest
