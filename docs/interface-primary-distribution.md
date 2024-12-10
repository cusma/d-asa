# Primary Distribution

```json
{{#include ./include/interface.primary-distribution.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by the authorized
primary market entity.

The call **MUST** fail with the `INVALID_HOLDING_ADDRESS` error code if the Account
associated with the holding address does not exist.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset operations are
suspended.

The call **MUST** fail with the `ZERO_UNITS` error code if the distributing units
are null.

The call **MUST** fail with the `OVER_DISTRIBUTION` error code if there are no sufficient
remaining D-ASA units for the primary distribution.

The call **MUST** fail with the `PRIMARY_DISTRIBUTION_CLOSED` error code if the
*primary distribution* is closed.
