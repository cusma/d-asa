# Revoke Role

```json
{{#include ./include/interface.revoke-role.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller or if the operation is not authorized.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `INVALID_ROLE` error code if the *role identifier*
is invalid.

The call **MUST** fail with the `INVALID_ROLE_ADDRESS` error code if the Account
Role Address is invalid.
