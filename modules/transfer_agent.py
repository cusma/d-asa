from algopy import Account, Global, Txn, UInt64, arc4

from smart_contracts import errors as err

from .accounting import AccountingModule


class TransferAgent(AccountingModule):
    """Provide primary distribution and secondary transfer mechanics."""

    def _assert_transfer_is_open(self) -> None:
        """Require transfers to happen within the configured secondary market window."""
        if self.transfer_opening_date:
            assert (
                self.transfer_opening_date <= Global.latest_timestamp
            ), err.CLOSED_TRANSFER
        if self.transfer_closure_date:
            assert (
                Global.latest_timestamp < self.transfer_closure_date
            ), err.CLOSED_TRANSFER

    @arc4.abimethod
    def transfer_set_schedule(
        self, *, open_date: UInt64, closure_date: UInt64
    ) -> UInt64:
        """
        Configure the secondary-market transfer window.

        Args:
            open_date: Inclusive UNIX timestamp at which transfers may start.
            closure_date: Exclusive UNIX timestamp at which transfers stop.

        Returns:
            UNIX timestamp of the schedule update.

        Raises:
            UNAUTHORIZED: Caller is not the arranger.
            INVALID_SORTING: The opening date is not earlier than the closure date.
            INVALID_TRANSFER_OPENING: The opening date is before the contract IED.
        """
        self._assert_caller_is_arranger()
        self._assert_configured()
        assert (
            self.initial_exchange_date <= open_date < closure_date
        ), err.INVALID_SORTING

        self.transfer_opening_date = open_date
        self.transfer_closure_date = closure_date
        return Global.latest_timestamp

    @arc4.abimethod
    def primary_distribution(
        self,
        *,
        holding_address: Account,
        units: UInt64,
    ) -> UInt64:
        """
        Reserve units for a holder before the initial exchange activates issuance.

        Args:
            holding_address: Account receiving the reserved units.
            units: Number of units to reserve.

        Returns:
            Remaining undistributed unit balance.

        Raises:
            NOT_CONFIGURED: Contract terms and schedule are not fully configured.
            UNAUTHORIZED: Caller is not an active primary dealer.
            DEFAULTED: Asset is defaulted.
            SUSPENDED: Asset or account operations are suspended.
            PRIMARY_DISTRIBUTION_CLOSED: Issuance is no longer accepting allocations.
            INVALID_HOLDING_ADDRESS: Holding address has no opened account.
            ZERO_UNITS: Requested distribution amount is zero.
            OVER_DISTRIBUTION: Requested units exceed the remaining supply.
        """
        self._assert_configured()
        self._assert_caller_is_primary_dealer()
        self._assert_is_not_contract_defaulted()
        self._assert_is_not_contract_suspended()
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
        """
        Transfer active units after settling both counterparties to the current cursor.

        Returns the number of units moved. The ACTUS kernel no longer persists a
        nominal per-unit value on-chain, so transfer results are unit-based.

        Args:
            sender_holding_address: Account debited for the transfer.
            receiver_holding_address: Account credited for the transfer.
            units: Number of active units to move.

        Returns:
            Number of units transferred.

        Raises:
            NOT_CONFIGURED: Contract terms and schedule are not fully configured.
            DEFAULTED: Asset is defaulted.
            SUSPENDED: Asset or account operations are suspended.
            PENDING_IED: Initial exchange has not executed yet.
            CLOSED_TRANSFER: Transfer window is closed.
            UNAUTHORIZED: Caller is not the sender holding address.
            INVALID_HOLDING_ADDRESS: Sender or receiver account does not exist.
            SELF_TRANSFER: Sender and receiver are the same address.
            NULL_TRANSFER: Requested transfer amount is zero.
            OVER_TRANSFER: Sender does not hold enough active units.
            PENDING_ACTUS_EVENT: A due ACTUS event must be processed before transfer.
        """
        self._assert_configured()
        self._assert_is_not_contract_defaulted()
        self._assert_is_not_contract_suspended()
        self._assert_initial_exchange_executed()
        self._assert_transfer_is_open()

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
