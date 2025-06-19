# Get Account Info

```json
{{#include ../.include/interface.get-account-info.json}}
```

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Sender
or Receiver Holding Address is invalid.
