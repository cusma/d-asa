# Close Account

```json
{{#include ./include/interface.close-account.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller or if the operation is not authorized.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
does not exist.
