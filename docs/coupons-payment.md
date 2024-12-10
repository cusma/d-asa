# Coupons Payment {#coupons-payment}

If the D-ASA has coupons, it **MUST** pay due coupons, according to the *time events*,
with the **OPTIONAL** `pay_coupon` method.

The D-ASA **MUST** pay due coupons, once, to the Landers.

The D-ASA **MUST NOT** pay coupons before *coupon due dates*.

In the case of an on-chain payment agent, the D-ASA **MUST** pay the *coupons* to
the Lander Payment Addresses.
