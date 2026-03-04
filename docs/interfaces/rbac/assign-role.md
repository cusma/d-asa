# RBAC Assign Role

```json
{
  "name": "rbac_assign_role",
  "desc": "Assign a role to an address",
  "readonly": false,
  "args": [
    {
      "type": "uint8",
      "name": "role_id",
      "desc": "Role Identifier"
    },
    {
      "type": "address",
      "name": "role_address",
      "desc": "Account Role Address"
    },
    {
      "type": "byte[]",
      "name": "config",
      "desc": "Role configuration (Optional)"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the role assignment"
  },
  "errors": [
    {
      "code": "UNAUTHORIZED",
      "message": "Not authorized"
    },
    {
      "code": "DEFAULTED",
      "message": "Defaulted"
    },
    {
      "code": "INVALID_ROLE",
      "message": "Invalid role identifier"
    },
    {
      "code": "INVALID_ROLE_ADDRESS",
      "message": "Invalid account role address"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an
authorized.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MUST** fail with the `INVALID_ROLE` error code if the *role identifier*
is invalid.

The call **MUST** fail with the `INVALID_ROLE_ADDRESS` error code if the *role
address* has been already assigned to the *role*.
