# RBAC Get Role Config

```json
{
  "name": "rbac_get_role_config",
  "desc": "Get role configuration",
  "readonly": true,
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
    }
  ],
  "returns": {
    "type": "byte[]",
    "desc": "Role configuration"
  },
  "errors": [
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
