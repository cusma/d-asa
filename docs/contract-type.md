# Contract Type

> Debt instruments such as bullet bonds, amortizing loans, mortgages, etc. differ
> based on their cash flow exchange patterns (e.g., principal and interest payment
> time schedules, fixed or variable interest rates, etc.).

> The ACTUS taxonomy reduces the majority of all financial contracts to a defined
> set of 32 generalized cash flow exchange patterns, called contract types.

It is **RECOMMENDED** to identify the D-ASA with a *contract type* \\([CT]\\) of
the <a href="https://github.com/actusfrf/actus-dictionary/blob/master/actus-dictionary-taxonomy.json">ACTUS
taxonomy</a>.

The *contract type* **MUST** have the following properties:

- `family`: Basic
- `class`: Fixed Income

The *contract type* **MUST** be identified by the ACTUS taxonomy *acronym* (`string`).

The *contract type* **MAY** be set using the **OPTIONAL** `set_asset_metadata` method
(see [Metadata](./metadata.md) section).
