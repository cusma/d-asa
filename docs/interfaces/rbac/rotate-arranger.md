# RBAC Rotate Arranger

```json
{
  "name": "rbac_rotate_arranger",
  "desc": "Rotate Arranger role to a new address",
  "readonly": false,
  "args": [
    {
      "type": "address",
      "name": "new_address",
      "desc": "New Arranger address"
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
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an
authorized.
