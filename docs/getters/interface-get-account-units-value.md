# Get Account Units Value

```json
{{#include ../.include/interface.get-account-units-value.json}}
```

The call **MUST** fail with the `NO_PRIMARY_DISTRIBUTION` error code if the method
is called before the *primary distribution opening date*.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.

The call **MUST** fail with the `INVALID_UNTIS` error code if the *unit* value is
greater than Account D-ASA units.
