# Role Wrappers

`DAsa` binds signer accounts into role-oriented wrappers.

```python
arranger = app.arranger(arranger_account)
account_manager = app.account_manager(manager_account)
primary_dealer = app.primary_dealer(dealer_account)
trustee = app.trustee(trustee_account)
authority = app.authority(authority_account)
observer = app.observer(observer_account)
op_daemon = app.op_daemon(op_daemon_account)
holder = app.account(holder_account)
```

## Arranger

`ArrangerRole` covers the contract lifecycle and arranger-controlled actions:

- `configure(...)`
- `configure_from_attributes(...)`
- `configure_contract(...)`
- `upload_schedule(...)`
- `execute_ied()`
- `set_transfer_window(...)`
- `fund_due_cashflows(...)`
- `append_observed_cash_event(...)`
- `append_observed_cash_events(...)`
- `apply_non_cash_event(...)`
- `rotate_arranger(...)`
- `set_op_daemon(...)`
- `assign_role(...)`
- `revoke_role(...)`

## Other Roles

- `AccountManagerRole.open_account(...)`
- `PrimaryDealerRole.primary_distribution(...)`
- `TrusteeRole.set_default(...)`
- `AuthorityRole.suspend_account(...)`
- `AuthorityRole.set_contract_suspension(...)`
- `ObserverRole.apply_non_cash_event(...)`
- `OpDaemonRole.claim(...)`

## Holding Accounts

`HoldingAccount` is the investor-facing wrapper:

- `get_raw_position()`
- `get_actualized_position(...)`
- `get_valuation(...)`
- `quote_trade(...)`
- `build_otc_dvp(...)`
- `transfer(...)`
- `claim(...)`
- `update_payment_address(...)`
