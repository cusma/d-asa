# Time Schedule

> Debt instruments may have fixed or variable time schedule (e.g., variable coupon
> due date, etc.).

> Debt instruments may have a limited or unlimited time schedule (e.g., a fixed
> coupon bond or a perpetual bond).

## Time Measurement

The time on the Algorand Virtual Machine is defined by the block <a href="https://en.wikipedia.org/wiki/Unix_time">UNIX
timestamp</a>[^1].

> The Algorand protocol has dynamic block latency with instant finality. At the
> time of writing (Jan 2025), block finality is about 2.8 seconds[^2].

> The AVM time may present a drift with respect to external standard time references.

## Events

The D-ASA events \\([EVT]\\) are defined by:

- *time events* \\([TEV]\\) (or "anchors");
- *time periods* (or "cycles").

---

[^1]: ACTUS is based on <a href="https://en.wikipedia.org/wiki/ISO_8601">ISO 8601</a>
timestamps. The UNIX to ISO 8601 conversions are left to clients (see [Calendar](./day-count-convention.md#calendar)
section).

[^2]: ACTUS timestamps have millisecond precision, which is not compatible with
blockchains' latency.
