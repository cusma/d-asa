# Reference Implementation {#reference-implementation}

The reference implementation provides the following features:

- RBAC:
  - Arranger: creates and configures the D-ASA
  - Account Manager: opens and closes accounts (proxy a KYC process)
  - Primary Dealer: performs the primary distribution on the primary market
  - Trustee: can call a default
  - Authority: can suspend accounts or the whole asset

- Denomination:
  - ASA

- Payment Agent:
  - On-chain (ASA)

- Day-count conventions:
  - Actual/Actual
  - Continuous

- Payoffs:
  - Fixed Coupon Bond: placed at nominal value, fixed coupon rates, fixed payments
  time schedule, principal at maturity
  - Zero Coupon Bond: placed at discount, fixed interest rate, principal at maturity

- Transfer Agent:
  - On-chain

- Secondary market

- Notarize metadata (e.g. prospectus)

For the coupon payments, the reference implementation enforces the following behaviors:

- A coupon payment can not be executed until all the previous due coupons (if any)
have been paid to all the investors.

For the asset transfer of secondary markets, the reference implementation enforces
the following behaviors:

- D-ASA units can not be transferred until all the pending due coupon payments for
the sender and receiver (if any) have been executed.
