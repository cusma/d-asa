# Algorand Virtual Machine (AVM)

The Algorand Virtual Machine (AVM) is a *trust-less* bytecode-based Turing-complete
stack interpreter that executes programs on the Algorand protocol.

The D-ASA is an Algorand Application that runs on the AVM.

## Performance

| Metric            | Value        |
|:------------------|:-------------|
| Block Size        | 5 MB         |
| Block Time        | ~2.8 sec     |
| TPS               | ~10k txn/sec |
| Finality          | instant      |
| Numeric Precision | 512 bit      |

> For further details on the AVM architecture, refer to the AVM [specification](https://specs.algorand.co/avm/non-normative/avm-nn).

## Time

The time on the Algorand Virtual Machine is defined by the block UNIX timestamp.

> The Algorand protocol has dynamic block latency with instant finality. At the
> time of writing (March 2026), block finality is about 2.8 seconds.

> The AVM time may present a drift with respect to external standard time references.

## Transaction Ordering

> [!IMPORTANT]
> Transaction ordering in a block is not enforced by the Algorand protocol. In a
> *healthy network*, block proposers are selected randomly by the Algorand consensus
> based on a Verifiable Random Function (VRF). Therefore, the order of transactions
> (e.g., asset transfers or cashflow payments) in a block is random and unbiased,
> with no systematic advantage or precedence of a payee with respect to others.
