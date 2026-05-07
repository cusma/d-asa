from algopy import Account, BoxMap, Global, Txn, UInt64, arc4

from modules.actus_kernel import ActusKernelModule
from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import errors as err


class AccountingModule(ActusKernelModule):
    """Contract Account ledger state and per-account settlement helpers."""

    def __init__(self) -> None:
        super().__init__()

        self.account = BoxMap(
            Account,
            typ.AccountPosition,
            key_prefix=cst.PREFIX_ID_ACCOUNT,
        )

    def _assert_valid_holding_address(self, holding_address: Account) -> None:
        """Require the holding address to have an opened a contract account."""
        assert holding_address in self.account, err.INVALID_HOLDING_ADDRESS

    def _assert_is_not_account_suspended(self, holding_address: Account) -> None:
        """Require the account not to be suspended."""
        assert not self.account[holding_address].suspended, err.SUSPENDED

    def _new_account_position(self, payment_address: Account) -> typ.AccountPosition:
        """Create an empty contract account position."""
        return typ.AccountPosition(
            payment_address=payment_address,
            units=UInt64(0),
            reserved_units=UInt64(0),
            suspended=False,
            settled_cursor=UInt64(0),
            interest_checkpoint=UInt64(0),
            principal_checkpoint=UInt64(0),
            claimable_interest=UInt64(0),
            claimable_principal=UInt64(0),
        )

    def _settle_position(self, holding_address: Account) -> tuple[UInt64, UInt64]:
        """
        Settle an account to the latest funded global cashflow indices.

        Computes the per-unit fixed-point interest and principal index growth since the
        account's last checkpoints, converts those deltas into absolute claimable
        amounts using the account's active units, accrues them to the position, and
        advances the account checkpoints to the current global indices and event cursor.

        Args:
            holding_address: Account to settle.

        Returns:
            Tuple of newly accrued `(claimable_interest, claimable_principal)` amounts.
        """

        self._assert_valid_holding_address(holding_address)
        position = self.account[holding_address].copy()

        # Compute the incremental per-unit fixed-point interest and principal accrued
        # since this account's last checkpoint.
        interest_delta = self.cumulative_interest_index - position.interest_checkpoint
        principal_delta = (
            self.cumulative_principal_index - position.principal_checkpoint
        )

        # Convert the per-unit fixed-point deltas into absolute claimable amounts
        # using the account's active units.
        claimable_interest = self._scaled_mul_div(
            interest_delta, position.units, self.fixed_point_scale
        )
        claimable_principal = self._scaled_mul_div(
            principal_delta, position.units, self.fixed_point_scale
        )

        # Accrue the claimable amounts to the account position and make them available
        # for withdrawal.
        position.claimable_interest += claimable_interest
        position.claimable_principal += claimable_principal

        # Advance the account's per-unit fixed-point checkpoints to the current global
        # per-unit fixed-point global indices.
        position.interest_checkpoint = self.cumulative_interest_index
        position.principal_checkpoint = self.cumulative_principal_index

        # Advance the account's event cursor to the current global event cursor.
        position.settled_cursor = self.event_cursor

        # Update the account position and return the newly accrued claimable amounts
        # added to the total position's claimable amounts.
        self.account[holding_address] = position.copy()
        return claimable_interest, claimable_principal

    def _ensure_units_activated(self, holding_address: Account) -> None:
        """Move reserved pre-IED units into active units once IED has executed."""
        self._assert_valid_holding_address(holding_address)
        if self._status_is_pending_ied():
            return

        position = self.account[holding_address].copy()
        if position.reserved_units == UInt64(0):
            return

        activated_units = position.reserved_units
        position.units += activated_units
        position.reserved_units = UInt64(0)
        self.account[holding_address] = position.copy()
        assert self.reserved_units_total >= activated_units, err.OVER_DISTRIBUTION
        self.reserved_units_total -= activated_units

    def _claimable_total(self, holding_address: Account) -> UInt64:
        """Return the total currently claimable amount for an account."""
        return (
            self.account[holding_address].claimable_interest
            + self.account[holding_address].claimable_principal
        )

    def _reset_claimable(self, holding_address: Account) -> tuple[UInt64, UInt64]:
        """Clear claimable balances after a successful withdrawal."""
        position = self.account[holding_address].copy()

        # Get the claimable amounts before reset
        interest_amount = position.claimable_interest
        principal_amount = position.claimable_principal

        # Reset the position's claimable amounts
        position.claimable_interest = UInt64(0)
        position.claimable_principal = UInt64(0)
        self.account[holding_address] = position.copy()

        assert self.reserved_interest >= interest_amount, err.NOT_ENOUGH_FUNDS
        assert self.reserved_principal >= principal_amount, err.NOT_ENOUGH_FUNDS

        # Update the global reserved interest and principal amounts
        self.reserved_interest -= interest_amount
        self.reserved_principal -= principal_amount
        return interest_amount, principal_amount

    def _credit_units(self, holding_address: Account, units: UInt64) -> None:
        """Increase an account's active unit balance."""
        self.account[holding_address].units += units

    def _credit_reserved_units(self, holding_address: Account, units: UInt64) -> None:
        """Increase an account's reserved pre-IED unit balance."""
        self.account[holding_address].reserved_units += units

    def _debit_units(self, holding_address: Account, units: UInt64) -> None:
        """Decrease an account's active unit balance."""
        assert units <= self.account[holding_address].units, err.OVER_TRANSFER
        self.account[holding_address].units -= units

    def _apply_transfer(
        self,
        sender_holding_address: Account,
        receiver_holding_address: Account,
        units: UInt64,
    ) -> None:
        """Move active units between two settled account positions."""
        self._debit_units(sender_holding_address, units)
        self._credit_units(receiver_holding_address, units)

    @arc4.abimethod
    def account_suspension(
        self, *, holding_address: Account, suspended: bool
    ) -> UInt64:
        """
        Set the suspension status of one account.

        Args:
            holding_address: Account holding address.
            suspended: Suspension status to apply.

        Returns:
            UNIX timestamp of the suspension update.

        Raises:
            UNAUTHORIZED: Caller is not an active authority.
            INVALID_HOLDING_ADDRESS: Holding address does not exist.
        """
        self._assert_caller_is_authority()
        self._assert_valid_holding_address(holding_address)
        self.account[holding_address].suspended = suspended
        return Global.latest_timestamp

    @arc4.abimethod
    def account_open(
        self, *, holding_address: Account, payment_address: Account
    ) -> UInt64:
        """
        Open a contract account with a new position and register its payment address.

        Args:
            holding_address: Account holding address.
            payment_address: Account payment address.

        Returns:
            UNIX timestamp of the account opening.

        Raises:
            UNAUTHORIZED: Caller is not an active account manager or contract already ended.
            DEFAULTED: Asset is defaulted.
            SUSPENDED: Asset operations are suspended.
            INVALID_HOLDING_ADDRESS: Holding address already exists.
        """

        self._assert_caller_is_account_manager()
        assert not self._status_is_ended(), err.UNAUTHORIZED
        self._assert_is_not_contract_defaulted()
        self._assert_is_not_contract_suspended()
        assert holding_address not in self.account, err.INVALID_HOLDING_ADDRESS
        self.account[holding_address] = self._new_account_position(payment_address)
        return Global.latest_timestamp

    @arc4.abimethod
    def account_update_payment_address(
        self, *, holding_address: Account, payment_address: Account
    ) -> UInt64:
        """
        Update the payment address of an account.

        Args:
            holding_address: Account holding address.
            payment_address: New account payment address.

        Returns:
            UNIX timestamp of the account update.

        Raises:
            UNAUTHORIZED: Caller is not the holding address owner.
            DEFAULTED: Asset is defaulted.
            SUSPENDED: Asset operations are suspended.
            INVALID_HOLDING_ADDRESS: Holding address does not exist.
        """
        self._assert_valid_holding_address(holding_address)
        assert Txn.sender == holding_address, err.UNAUTHORIZED
        self._assert_is_not_contract_defaulted()
        self._assert_is_not_contract_suspended()
        self.account[holding_address].payment_address = payment_address
        return Global.latest_timestamp

    @arc4.abimethod(readonly=True)
    def account_get_position(self, *, holding_address: Account) -> typ.AccountPosition:
        """
        Get the full accounting position for one holder.

        Args:
            holding_address: Account holding address.

        Returns:
            Account position record.

        Raises:
            INVALID_HOLDING_ADDRESS: Holding address does not exist.
        """
        self._assert_valid_holding_address(holding_address)
        return self.account[holding_address]
