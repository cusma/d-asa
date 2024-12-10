# Secondary Market {#secondary-market}

> Debt instruments can be traded on secondary markets.

If the debt instrument can be traded on secondary markets, the D-ASA **MUST** be
transferable and implement the **OPTIONAL** `set_secondary_time_events`.

The D-ASA **MUST** define *secondary market time events* as `uint64[]` array, where:

- The length of the array **MUST** be `N>=2`;

- The first element **MUST** be the *secondary market opening date* (`uint64`):
the time at which the secondary market opens;

- The last element **MUST** be the *secondary market closure date* (`uint64`):
the time at which the secondary market closes.

The *secondary market time events* **MUST** be sorted in strictly ascending order.

The *secondary market opening date* **MUST NOT** be earlier than the *issuance date*.

The *secondary market closure date* **MUST NOT** be later than the *maturity date*.

The *secondary market time events* **SHOULD** be defined as UNIX time, in seconds.

If *secondary market time events* are defined in UNIX time with non-continuous *day-count
conventions* (ID<`255`), then *time periods* between subsequent events **SHOULD**
be multiples of a day (in seconds).

The *secondary market time events* **MUST** be set using the `set_secondary_time_events`
method.

The *secondary market time events* **MAY** be updated with the `set_secondary_time_events`
method.

The updated *secondary market time events* **MUST NOT** modify past events.

The `asset_transfer` method **MUST** fail if the secondary market is closed.
