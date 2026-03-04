# RBAC Governance Asset Suspension

```json
{
  "name": "rbac_gov_asset_suspension",
  "desc": "Set asset suspension status",
  "readonly": false,
  "args": [
    {
      "type": "bool",
      "name": "suspended",
      "desc": "Suspension status"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the set asset suspension status"
  },
  "errors": [
    {
      "code": "UNAUTHORIZED",
      "message": "Not authorized"
    }
  ]
}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.
