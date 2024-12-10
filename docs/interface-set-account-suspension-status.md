# Set Account Suspension Status

```json
{{#include ./include/interface.set-account-suspension-status.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.
