# D-ASA units {#d-asa-units}

> D-ASA units represent the ownership of the tokenized debt instrument.

## Supply {#supply}

The D-ASA **MUST** define its *total units* (`uint64`).

If the D-ASA has a *principal*, its initials *total units* **MUST** be equal to
the *principal* divided by the *minimum denomination.*

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a principal of 1M EUR and a minimum
> denomination of 1,000 EUR. The D-ASA has 1,000 initial total units.

The D-ASA *total units* **MAY** be updated with the **OPTIONAL** `update_total_units`
method.

## Value {#value}

> The D-ASA unit’s value is always intended as **nominal value** (at redemption).

The D-ASA *unit value* (`uint64`) **MUST** be expressed in the *denomination asset*.

If the D-ASA has a *principal*, its initial *unit value* **MUST** be equal to the
*minimum denomination.*

The D-ASA *unit* *value* **MAY** change over time.

> The D-ASA unit’s value may change according to different conditions, such as an
> amortizing principal repayment schedule (see Amortizing Schedule section).

The D-ASA *unit value* **MAY** change globally or locally (per account).

> The D-ASA unit’s value can be global or local (per-account). Global unit value
> should be used when the value of all the units can be updated at the same time.
> Local unit value should be used when the units' value ia updated at different
> times per each account.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with an initial unit value of 1,000 EUR.
> The D-ASA accrues interest on a daily basis, paid at redemption. The unit value
> is updated globally (for all the units).

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with an initial unit value of 1,000 EUR.
> The D-ASA has an amortizing principal repayment schedule. Repayments are executed
> per-account. The unit value is updated per-account (for the account’s units).

The D-ASA *unit value* **MAY** be globally updated with the **OPTIONAL** `update_global_unit_value`
method.

## Fungibility {#fungibility}

> D-ASA units' fungibility depends on:
>
> - Units value (nominal);
> - Executed payments.
>

The D-ASA *fungible units* **MUST** have the same *value* and *executed payments.*

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA with 4 coupons. Lenders A and B are holding 10 D-ASA units
> each. The 1st coupon is due. Coupon payments are not executed synchronously for
> all the Lenders. The coupon payment is executed for Lender A, while Lender B is
> still waiting for the payment settlement. Lender A units are temporarily non-fungible
> with Lender B units until the 1st coupon is paid for both.
