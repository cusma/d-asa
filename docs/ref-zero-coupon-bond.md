# Zero Coupon Bond

| Property                | Option                    |
|-------------------------|---------------------------|
| Denomination            | On-chain (ASA)            |
| Principal repayment     | At maturity               |
| Early repayment options | No                        |
| Interest                | Fixed                     |
| Coupons                 | No                        |
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

## Default

Called manually by the trustee.
