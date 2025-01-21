# Contract Type

> Debt instruments such as bullet bonds, amortizing loans, mortgages, etc. differ
> based on their cash flow exchange patterns (e.g., principal and interest payment
> time schedules, fixed or variable interest rates, etc.).

> The ACTUS taxonomy reduces the majority of all financial contracts to a defined
> set of 32 generalized cash flow exchange patterns, called contract types.

The D-ASA **MAY** define an informative *contract type* \\([CT]\\).

It is **RECOMMENDED** to classify the D-ASA *contract type* according to the <a href="https://github.com/actusfrf/actus-dictionary/blob/master/actus-dictionary-taxonomy.json">ACTUS
taxonomy</a>.

The ACTUS *contract type* **MUST** have the following properties:

- `family`: Basic
- `class`: Fixed Income

The *contract type* **MAY** be set using the **OPTIONAL** `set_asset_metadata` method
(see [Metadata](./metadata.md) section).

It is **RECOMMENDED** to use the unique D-ASA ID as *contract identifier* \\([CID]\\).
