# Early Repayment {#early-repayment}

If the *early repayment options* repays the principal amount before *maturity* (*prepayment
effect* `1`, see [Prepayment Effects](./early-repayment-options.md#prepayment-effects)
section), the D-ASA **MUST** implement the **OPTIONAL** `early_repayment` method.

In the case of an on-chain payment agent, the D-ASA **MUST** repay the *principal*
to the Investor Payment Addresses.

The D-ASA units associated with the early repaid principal **MUST** be removed from
Investors’ Accounts and from circulation.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a *principal* of 1M EUR and a *minimum
> denomination* of 1,000 EUR. The D-ASA originally had 1,000 *total units* in circulation.
> An early repayment of 500k EUR (equal to 500 units) is executed for some Investors.
> The D-ASA now has 500 circulating units (worth 1,000 EUR each), while 500 early
> repaid units are removed from circulation.
