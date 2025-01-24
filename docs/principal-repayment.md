# Principal Repayment {#principal-repayment}

> Debt instruments repay the principal according to the repayment schedule.

The *principal* **MUST** be repaid according to a *principal repayment schedule*.

In the case of an on-chain payment agent, the D-ASA **MUST** repay the *principal*
to the Investor’s Payment Addresses.

## Bullet Schedule

If the debt instrument has a *bullet principal repayment schedule*, the principal
**MUST** be paid entirely at the *maturity date* using the `pay_principal` method.

If the D-ASA has coupons, the *principal* **MUST NOT** be paid if there is any due
coupon still to be paid.

## Amortizing Schedule

If the debt instrument has an *amortizing principal repayment schedule*, the *principal*
**MUST** be repaid along with the **fixed** number of *coupons*, according to the
*principal amortization* (see [Amortization](./principal.md#amortization) section),
using the `pay_coupon` method.

The first coupon due date corresponds to \\([PRANX]\\).

The D-ASA *unit value* **MUST** be updated according to the *outstanding principal.*

It is **RECOMMENDED** to use an ACTUS *interest calculation base* \\([IPCB]\\).

> A reference implementation **SHOULD** calculate interest on the outstanding principal.

> A reference implementation **SHOULD** restrict the amortizing rates updatability.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a *principal* of 1M EUR and a *minimum
> denomination* of 1,000 EUR, 5 coupons, and an even amortizing schedule (20% amortizing
> rate). The D-ASA has 1,000 *total units*. The D-ASA initial *unit value* is 1,000
> EUR. The 1st coupon pays both the interest (according to the *coupon rates*) and
> 20% of the principal (according to *amortizing rates*). The D-ASA outstanding
> principal is 800k EUR. The D-ASA *unit value* is 800 EUR.

> 📎 **EXAMPLE**
>
> Let’s have a D-ASA denominated in EUR, with a *principal* of 1M EUR and a *minimum
> denomination* of 1,000 EUR. The D-ASA originally had 1,000 *total units* (worth
> 1,000 EUR each) in circulation. A partial repayment of 500k EUR (50% of the original
> principal) must be executed pro-rata to all investors. A single amortizing rate
> of 5,000 bps is used. After the partial repayment, the D-ASA still has 1000 circulating
> units (worth 500 EUR each).
