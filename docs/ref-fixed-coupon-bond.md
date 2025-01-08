# Fixed Coupon Bond

| Property                | Option                    |
|-------------------------|---------------------------|
| Denomination            | On-chain (ASA)            |
| Principal repayment     | At maturity               |
| Early repayment options | No                        |
| Interest                | Fixed                     |
| Coupons                 | Yes (Fixed)               |
| Time Schedule           | Fixed (Events)            |
| Day-Count Convention    | Actual/Actual, Continuous |
| Primary Distribution    | Direct placement          |
| Primary Market          | Placed at nominal value   |
| Transfer Agent          | Trustless                 |
| Payment Agent           | Trustless                 |
| Secondary Market        | Yes                       |
| Default                 | Manual (Trustee)          |

## Payment Agent

Payments are trustless (i.e., can be triggered by anyone), as long as payments'
conditions are met (e.g., the payment is due).

A coupon payment **cannot** be executed until all the previous due coupons (if
any) have been paid to all the investors.

## Transfer Agent

D-ASA units **cannot** be transferred until all the pending due coupon payments
for the sender and receiver (if any) have been executed.

## Default

Called manually by the trustee.
