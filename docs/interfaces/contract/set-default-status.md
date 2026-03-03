# Set Default Status

```json
{
  "name": "set_default_status",
  "desc": "Set D-ASA default status",
  "readonly": false,
  "args": [
    {
      "type": "bool",
      "name": "defaulted",
      "desc": "Default status"
    }
  ],
  "returns": {
    "type": "uint64",
    "desc": "Timestamp of the set status"
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
