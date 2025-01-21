# Fixed Coupon Bond

| Contract                | ACTUS        | Option                   |
|-------------------------|--------------|--------------------------|
| Type                    | \\([CT]\\)   | \\([PAM]\\)              |
| Denomination            | \\([CUR]\\)  | ASA                      |
| Settlement              | \\([CURS]\\) | ASA                      |
| Early repayment options |              | No                       |
| Early repayment penalty | \\([PYTP]\\) | -                        |
| Interest                | \\([IPNR]\\) | Fixed                    |
| Coupons                 |              | Yes (Fixed)              |
| Time Schedule           |              | Fixed (Events)           |
| Maturity Date           | \\([MD]\\)   | Yes (Fixed)              |
| Principal repayment     |              | At maturity              |
| Day-Count Convention    | \\([IPCD]\\) | \\([AA]\\) or Continuous |
| Calendar                | \\([CLDR]\\) | \\([NC]\\)               |
| Grace Period            | \\([GRP]\\)  | No                       |
| Delinquency Period      | \\([DQP]\\)  | No                       |
| Performance             | \\([PRF]\\)  | Manual default (Trustee) |

| Execution            | Option                  |
|----------------------|-------------------------|
| Primary Distribution | Direct placement        |
| Primary Market       | Placed at nominal value |
| Transfer Agent       | Trustless               |
| Payment Agent        | Trustless, On-chain     |
| Secondary Market     | Yes                     |

## Payment Agent

Payments are trustless (i.e., can be triggered by anyone), as long as payments'
conditions are met (e.g., the payment is due).

A coupon payment **cannot** be executed until all the previous due coupons (if
any) have been paid to all the investors.

## Transfer Agent

D-ASA units **cannot** be transferred until all the pending due coupon payments
for the sender and receiver (if any) have been executed.

## Performance

No grace period. No delinquency period. Default called manually by the trustee.
