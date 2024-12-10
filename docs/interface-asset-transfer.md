# Asset Transfer

```json
{{#include ./include/interface.asset-transfer.json}}
```

The call **MUST** transfer D-ASA units from the Sender Account Holding Address (removing
D-ASA units) to the Receiver Account Holding Address (adding D-ASA units).

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `SUSPENDED` error code if the asset operations or
any account involved in the transfers are suspended.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `SECONDARY_MARKET_CLOSED` error code if the secondary
market is closed.

The call **MUST** fail with the `OVER_TRANSFER` error code if the Sender Account
Holding Address has insufficient D-ASA units to transfer.

The call **MUST** fail with the `NON_FUNGIBLE_UNITS` error code if the Sender and
Receiver units are not fungible (e.g. different paid coupons, see D-ASA units fungibility
section).

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
a due coupon still to be paid to the Sender Holding Address.
