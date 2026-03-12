from algopy import Account, Global, Txn, UInt64, arc4

from smart_contracts import errors as err

from .accounting import AccountingModule


class TransferAgent(AccountingModule):
    """Provide primary distribution and secondary transfer mechanics."""

    @arc4.abimethod
    def primary_distribution(
        self,
        *,
        holding_address: Account,
        units: UInt64,
    ) -> UInt64:
        """Reserve units for a holder before IED finalizes issuance."""
        self._assert_configured()
        self._assert_caller_is_primary_dealer()
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()
        assert self._status_is_pending_ied(), err.PRIMARY_DISTRIBUTION_CLOSED
        self._assert_valid_holding_address(holding_address)
        self._assert_is_not_account_suspended(holding_address)
        assert units > UInt64(0), err.ZERO_UNITS
        assert (
            self.reserved_units_total + units <= self.total_units
        ), err.OVER_DISTRIBUTION
        if self.initial_exchange_date:
            assert (
                Global.latest_timestamp <= self.initial_exchange_date
            ), err.PRIMARY_DISTRIBUTION_CLOSED

        self._credit_reserved_units(holding_address, units)
        self.reserved_units_total += units
        return self.total_units - self.reserved_units_total

    @arc4.abimethod
    def transfer(
        self,
        *,
        sender_holding_address: Account,
        receiver_holding_address: Account,
        units: UInt64,
    ) -> UInt64:
        """Transfer active units after settling both counterparties to the current cursor.

        Returns the number of units moved. The ACTUS kernel no longer persists a
        nominal per-unit value on-chain, so transfer results are unit-based.
        """
        self._assert_configured()
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()
        self._assert_initial_exchange_executed()
        self._assert_transfer_window()

        assert Txn.sender == sender_holding_address, err.UNAUTHORIZED
        self._assert_valid_holding_address(sender_holding_address)
        self._assert_valid_holding_address(receiver_holding_address)
        self._assert_is_not_account_suspended(sender_holding_address)
        self._assert_is_not_account_suspended(receiver_holding_address)
        assert sender_holding_address != receiver_holding_address, err.SELF_TRANSFER
        assert units > UInt64(0), err.NULL_TRANSFER
        assert units <= self.account[sender_holding_address].units, err.OVER_TRANSFER

        self._assert_no_due_event_pending()
        self._ensure_units_activated(sender_holding_address)
        self._ensure_units_activated(receiver_holding_address)
        self._settle_position(sender_holding_address)
        self._settle_position(receiver_holding_address)
        self._apply_transfer(
            sender_holding_address,
            receiver_holding_address,
            units,
        )
        return units
