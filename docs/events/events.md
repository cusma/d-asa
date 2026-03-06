# Events

The D-ASA implements ACTUS events as [ARC-28 events](https://dev.algorand.co/arc-standards/arc-0028/).

The following is the ACTUS event schema:

```json
{
  "name": "Event",
  "desc": "ACTUS Event",
  "args": [
    {
      "type": "uint64",
      "name": "contract_id",
      "desc": "The Contract ID emitting the event"
    },
    {
      "type": "uint8",
      "name": "type",
      "desc": "The ACTUS Event type"
    },
    {
      "type": "string",
      "name": "type_name",
      "desc": "The ACTUS Event acronym"
    },
    {
      "type": "uint64",
      "name": "time",
      "desc": "The timestamp of the event (UNIX time)"
    },
    {
      "type": "uint64",
      "name": "payoff",
      "desc": "The payoff associated with the event (if any)"
    },
    {
      "type": "uint64",
      "name": "currency_id",
      "desc": "The currency ID (Asset ID on chain or ISO 4217 numeric code)"
    },
    {
      "type": "byte[]",
      "name": "currency_unit",
      "desc": "The unit name of the currency ID"
    },
    {
      "type": "uint64",
      "name": "nominal_value",
      "desc": "The nominal value at the time of the event"
    },
    {
      "type": "uint16",
      "name": "nominal_rate_bps"
    },
    {
      "type": "uint64",
      "name": "nominal_accrued"
    }
  ]
}
```

The D-ASA supports the following ACTUS event types:

| Type | Acronym    | Description          |
|------|------------|----------------------|
| `3`  | \\( PR \\) | Principal Redemption |
| `8`  | \\( IP \\) | Interest Payment     |
