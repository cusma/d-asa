# Assign Role

```json
{{#include ./include/interface.assign-role.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an
authorized.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `INVALID_ROLE` error code if the *role identifier*
is invalid.

The call **MUST** fail with the `INVALID_ROLE_ADDRESS` error code if the *role
address* has been already assigned to the *role*.
