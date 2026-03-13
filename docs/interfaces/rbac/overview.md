# RBAC Interface

The RBAC interface manages privileged roles, suspension state, and application control.

Only the Arranger may call RBAC methods, unless otherwise specified.

## `contract_update`

```json
{
  "name": "contract_update",
  "readonly": false,
  "args": [],
  "returns": { "type": "void" },
  "errors": ["UNAUTHORIZED"]
}
```

## `rbac_rotate_arranger`

```json
{
  "name": "rbac_rotate_arranger",
  "readonly": false,
  "args": [
    { "name": "new_arranger", "type": "address" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the rotation" },
  "errors": ["UNAUTHORIZED"]
}
```

## `rbac_set_op_daemon`

```json
{
  "name": "rbac_set_op_daemon",
  "readonly": false,
  "args": [
    { "name": "address", "type": "address" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the assignment" },
  "errors": ["UNAUTHORIZED"]
}
```

This is a non-normative helper for payment automation.

## `rbac_assign_role`

```json
{
  "name": "rbac_assign_role",
  "readonly": false,
  "args": [
    { "name": "role_id", "type": "uint8" },
    { "name": "role_address", "type": "address" },
    { "name": "validity", "type": "RoleValidity" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the assignment" },
  "errors": ["UNAUTHORIZED", "DEFAULTED", "INVALID_ROLE", "INVALID_ROLE_ADDRESS"]
}
```

## `rbac_revoke_role`

```json
{
  "name": "rbac_revoke_role",
  "readonly": false,
  "args": [
    { "name": "role_id", "type": "uint8" },
    { "name": "role_address", "type": "address" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the revocation" },
  "errors": ["UNAUTHORIZED", "DEFAULTED", "INVALID_ROLE", "INVALID_ROLE_ADDRESS"]
}
```

## `rbac_contract_suspension`

```json
{
  "name": "rbac_contract_suspension",
  "readonly": false,
  "args": [
    { "name": "suspended", "type": "bool" }
  ],
  "returns": { "type": "uint64", "desc": "UNIX timestamp of the suspension update" },
  "errors": ["UNAUTHORIZED"]
}
```

Only an active Authority may call this method.

## `rbac_get_arranger`

```json
{
  "name": "rbac_get_arranger",
  "readonly": true,
  "args": [],
  "returns": { "type": "address", "desc": "Current arranger address" },
  "errors": []
}
```

## `rbac_get_address_roles`

```json
{
  "name": "rbac_get_address_roles",
  "readonly": true,
  "args": [
    { "name": "address", "type": "address" }
  ],
  "returns": {
    "type": "(bool,bool,bool,bool,bool)",
    "desc": "Account manager, primary dealer, trustee, authority, observer"
  },
  "errors": []
}
```

## `rbac_get_role_validity`

```json
{
  "name": "rbac_get_role_validity",
  "readonly": true,
  "args": [
    { "name": "role_id", "type": "uint8" },
    { "name": "role_address", "type": "address" }
  ],
  "returns": { "type": "RoleValidity", "desc": "Stored validity interval" },
  "errors": ["INVALID_ROLE", "INVALID_ROLE_ADDRESS"]
}
```
