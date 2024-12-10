# Pay Principal

```json
{{#include ./include/interface.pay-principal.json}}
```

> A reference implementation **SHOULD NOT** require an authorized caller.

The call **MUST** remove D-ASA units from the Account Holding Address and from
circulation.

If the call requires authorization, it **MUST** fail with the `UNAUTHORIZED` error
code if not called by an authorized caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.

The call **MUST** fail with the `NO_UNTIS` error code if the Account has no D-ASA
units.

The call **SHOULD** fail with the `NOT_MATURE` error code if the principal is not
mature.

The call **MUST** fail with the `PENDING_COUPON_PAYMENT` error code if there is
any due coupon still to be paid.
