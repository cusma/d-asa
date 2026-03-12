from algopy import Account, Bytes, Global, Txn, UInt64, arc4, ensure_budget, itxn

from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import errors as err

from .accounting import AccountingModule


class PaymentAgent(AccountingModule):
    """Provide ACTUS cashflow funding and holder withdrawal behavior."""

    def _assert_payment_authorization(self, holding_address: Account) -> None:
        """Require the caller to be allowed to trigger a holder payment."""
        if self.op_daemon.value != Global.zero_address:
            assert (
                Txn.sender == self.op_daemon.value
                or Txn.sender == holding_address
                or Txn.sender == self.account[holding_address].payment_address
            ), err.UNAUTHORIZED

    def _is_payment_executable(self, holding_address: Account) -> bool:
        """Return whether a holder can currently receive an on-chain asset transfer."""
        return (
            self.account[holding_address].payment_address.is_opted_in(
                self.settlement_asset_id
            )
            and not self.account[holding_address].suspended
        )

    def _assert_enough_funds(self, payment_amount: UInt64) -> None:
        """Require the contract to hold at least the requested settlement amount."""
        assert (
            self.settlement_asset_id.balance(Global.current_application_address)
            >= payment_amount
        ), err.NOT_ENOUGH_FUNDS

    def _pay(self, receiver: Account, amount: UInt64) -> None:
        """Send settlement ASA from the app account to a receiver."""
        itxn.AssetTransfer(
            xfer_asset=self.settlement_asset_id,
            asset_receiver=receiver,
            asset_amount=amount,
            fee=Global.min_txn_fee,
        ).submit()

    @arc4.abimethod
    def fund_due_cashflows(self, *, max_event_count: UInt64) -> typ.CashFundingResult:
        """Reserve due ACTUS cash events into the escrow-style claim ledger."""
        self._assert_configured()
        self._assert_caller_is_arranger()
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()
        self._assert_initial_exchange_executed()
        if self._is_dynamic_annuity():
            ensure_budget(
                required_budget=(
                    UInt64(cst.OP_UP_FUND_DUE_CASHFLOWS_BASE_BUDGET)
                    + max_event_count
                    * UInt64(cst.OP_UP_FUND_DUE_CASHFLOWS_PER_EVENT_BUDGET)
                ),
            )

        processed_events = UInt64(0)
        funded_interest = UInt64(0)
        funded_principal = UInt64(0)

        while (
            processed_events < max_event_count
            and self.event_cursor < self.schedule_entry_count
        ):
            entry = self._get_schedule_entry(self.event_cursor)
            if entry.scheduled_time > Global.latest_timestamp:
                break
            if not self._event_is_cash(entry.event_type.as_uint64()):
                break

            interest_amount, principal_amount = self._apply_cash_entry(entry)
            funded_interest += interest_amount
            funded_principal += principal_amount
            processed_events += UInt64(1)

        assert processed_events > UInt64(0), err.NO_DUE_CASHFLOW
        return typ.CashFundingResult(
            funded_interest=funded_interest,
            funded_principal=funded_principal,
            total_funded=funded_interest + funded_principal,
            processed_events=processed_events,
            timestamp=Global.latest_timestamp,
        )

    @arc4.abimethod
    def claim_due_cashflows(
        self,
        *,
        holding_address: Account,
        payment_info: Bytes,
    ) -> typ.CashClaimResult:
        """Withdraw the holder's already funded ACTUS cash entitlements."""
        self._assert_configured()
        self._assert_valid_holding_address(holding_address)
        self._assert_payment_authorization(holding_address)
        self._assert_is_not_asset_defaulted()
        self._assert_is_not_asset_suspended()
        self._assert_initial_exchange_executed()

        self._ensure_units_activated(holding_address)
        self._settle_position(holding_address)
        total_amount = self._claimable_total(holding_address)
        assert total_amount > UInt64(0), err.NO_DUE_CASHFLOW

        interest_amount = self.account[holding_address].claimable_interest
        principal_amount = self.account[holding_address].claimable_principal

        if self._is_payment_executable(holding_address):
            self._assert_enough_funds(total_amount)
            self._pay(self.account[holding_address].payment_address, total_amount)
            interest_amount, principal_amount = self._reset_claimable(holding_address)

        return typ.CashClaimResult(
            interest_amount=interest_amount,
            principal_amount=principal_amount,
            total_amount=interest_amount + principal_amount,
            timestamp=Global.latest_timestamp,
            context=payment_info,
        )
