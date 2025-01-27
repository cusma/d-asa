# Fixed Coupon Bond

| Contract                | ACTUS        | Option                   |
|-------------------------|--------------|--------------------------|
| Type                    | \\([CT]\\)   | \\([PAM]\\)              |
| ID                      | \\([CID]\\)  | D-ASA App ID             |
| Denomination            | \\([CUR]\\)  | ASA                      |
| Settlement              | \\([CURS]\\) | ASA                      |
| Interest                | \\([IPNR]\\) | Fixed                    |
| Coupons                 | \\([IP]\\)   | Yes (Fixed)              |
| Time Schedule           | \\([EVT]\\)  | Events (Fixed)           |
| Maturity Date           | \\([MD]\\)   | Yes (Fixed)              |
| Principal Redemption    | \\([PR]\\)   | At Maturity              |
| Early Repayment Options | \\([PPEF]\\) | \\([N]\\)                |
| Early Repayment Penalty | \\([PYTP]\\) | -                        |
| Day-Count Convention    | \\([IPCD]\\) | \\([AA]\\) or Continuous |
| Calendar                | \\([CLDR]\\) | \\([NC]\\)               |
| Business Day Convention | \\([BDC]\\)  | -                        |
| End of Month Convention | \\([EOMC]\\) | -                        |
| Performance             | \\([PRF]\\)  | Manual Default (Trustee) |
| Grace Period            | \\([GRP]\\)  | No                       |
| Delinquency Period      | \\([DQP]\\)  | No                       |

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

AVM fees (ALGO) for the execution of the cash flows are paid by who triggers the
cash flow.

A coupon payment **cannot** be executed until all the previous due coupons (if
any) have been paid to all the investors.

## Transfer Agent

D-ASA units **cannot** be transferred until all the pending due coupon payments
for the sender and receiver (if any) have been executed.

## Performance

No grace period. No delinquency period. Default called manually by the trustee.
