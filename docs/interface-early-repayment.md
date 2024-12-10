# Early Repayment

```json
{{#include ./include/interface.early-repayment.json}}
```

The call **MUST** remove D-ASA early rapid units from the Account Holding Address
and from circulation.

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `SUSPENDED` error code if the asset operations or
any account involved in the transfers are suspended.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `NO_UNTIS` error code if the Account has no D-ASA
units.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
a due coupon still to be paid for the Account.

The call **MUST** fail with the `ZERO_UNITS` error code if the distributing units
are null.

The call **MUST** fail with the `OVER_REPAYMENT` error code if there are no sufficient
remaining D-ASA units to repay.

The call **MUST** fail with the `ALREADY_MATURE` error code if the principal is
mature.
