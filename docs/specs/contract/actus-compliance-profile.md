# ACTUS Compliance Profile

> Debt instruments such as bullet bonds, amortizing loans, mortgages, etc. differ
> based on their cash flow exchange patterns (e.g., principal and interest payment
> time schedules, fixed or variable interest rates, etc.).

> The ACTUS taxonomy reduces the majority of all financial contracts to a defined
> set of 32 generalized cash flow exchange patterns, called contract types.

The D-ASA **MUST** be to classified with an ACTUS *contract type* \\( [CT] \\)
(`uint8`) (see the [ACTUS taxonomy](https://github.com/actusfrf/actus-dictionary/blob/master/actus-dictionary-taxonomy.json)).

The *contract type* **MUST** have the following properties:

- `family`: Basic
- `class`: Fixed Income
- `sub-class`: Maturities

## Contract Identifier

The D-ASA *contract identifier* \\( [CID] \\) is the Algorand Application ID (`uint64`).

The D-ASA contract layer **MUST** follow a constrained ACTUS fixed-income profile
that can be normalized and executed on the AVM.

## Supported contract families

The current kernel supports the following ACTUS contract family identifiers:

| ID  | Contract Type | Description                                                                                                                            | Rate                  | Use case                                                       |
|:---:|:-------------:|:---------------------------------------------------------------------------------------------------------------------------------------|:----------------------|:---------------------------------------------------------------|
| `0` |     `PAM`     | Principal payment fully at \\( [IED] \\) and repaid at \\( [MD] \\).                                                                   | Fix or variable rates | All kind of bonds, term deposits, bullet loans, mograges, etc. |
| `1` |     `ANN`     | Principal payment fully at \\( [IED] \\) and repaid periodically in constants amounts till \\( [MD] \\).                               | Fix or variable rates | Classical level payment morgages, leasing contracts, etc.      |
| `2` |     `NAM`     | As `ANN`, when resetting reate total amount (principal + interest) stay constant. \\( [MD] \\) shifts.                                 | Variable only         | Adjustable rate morgages                                       |
| `3` |     `LAM`     | Principal payment fully at \\( [IED] \\) and repaid periodically in constants amounts till \\( [MD] \\), interest reduced accordingly. | Fix or variable       | Amortizing loans                                               |
| `4` |     `LAX`     | Flexible version of `LAM`.                                                                                                             | Fix or variable       | Teaser rate loans                                              |
| `5` |     `CLM`     | Loans rolled over as long as they are not called. Once called, it has to be paid back after noticed period.                            | Fix or variable       | Loans with call options                                        |

> Non-normative subtypes such as `PAM:ZCB` and `PAM:FCB` are resolved before normalization.
> The AVM kernel stores only the normalized family identifier.

## Supported event types

The normalized execution schedule **MUST** contain only event types permitted for
the configured contract family.

| Family | Allowed events                                            |
|:-------|:----------------------------------------------------------|
| `PAM`  | `IED`, `IP`, `MD`, `RR`, `RRF`                            |
| `ANN`  | `IED`, `IP`, `PR`, `MD`, `RR`, `RRF`, `IPCB`, `PRF`       |
| `NAM`  | `IED`, `IP`, `PR`, `MD`, `RR`, `RRF`, `IPCB`              |
| `LAM`  | `IED`, `IP`, `PR`, `MD`, `RR`, `RRF`, `IPCB`              |
| `LAX`  | `IED`, `IP`, `PR`, `PI`, `MD`, `RR`, `RRF`, `IPCB`, `PRF` |
| `CLM`  | `IED`, `IP`, `PR`, `MD`, `RR`, `RRF`                      |

- **Cash events** are limited to `IP`, `PR`, and `MD`.

- **Non-cash events** are limited to `IED`, `PI`, `RR`, `RRF`, `IPCB`, and `PRF`.

## Normalization constraints

The D-ASA profile further requires:

- `business_day_convention = NOS`;
- `calendar = NC`;
- One of the supported day-count conventions listed in [Day-Count Convention](./day-count-convention.md);
- AVM-compatible `uint64` values for amounts, times, and fixed-point factors.

Normalization **MUST** reject any contract that cannot satisfy those constraints.

## Observed events

Observed schedule extension is intentionally narrow:

- Only `CLM` contracts may append observed events at runtime;

- `append_observed_cash_event` only accepts observed `PR` cash events;

- `apply_non_cash_event` applies due `RR` and `RRF` events under Observer control;

- Arranger-controlled observed appends **MUST** preserve event ordering and contiguous
event IDs.
