# Perpetual Bond

Placed at nominal value, variable interest rate, not callable.

## Payment Agent

Payments are trustless (i.e., can be triggered by anyone), as long as payments'
conditions are met (e.g., the payment is due).

A coupon payment **cannot** be executed until all the previous due coupons (if
any) have been paid to all the investors.

## Transfer Agent

D-ASA units **cannot** be transferred until all the pending due coupon payments
for the sender and receiver (if any) have been executed.

## Interest Rate

Updated by the interest oracle.

Interest rate **cannot** be updated until all the previous due coupons (if any)
have been paid to all the investors.

## Default

Called manually by the trustee.
