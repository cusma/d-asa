# Denomination {#denomination}

> Debt instruments are denominated in a currency.

The D-ASA **MUST** be denominated either in an on-chain or off-chain *denomination
asset*.

The *denomination asset identifier* **MUST** be set using the `asset_config` method.

## On-chain denomination {#on-chain-denomination}

The *denomination asset* **MUST** be an Algorand Standard Asset (ASA), an Application
asset (App), or the ALGO.

The *denomination asset* **MUST** be identified by the ASA ID, the App ID, or `0`
for ALGO.

## Off-chain denomination {#off-chain-denomination}

The *denomination asset* **MUST** be identified by the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a> currency numeric code.

The *denomination asset* **MUST** use the decimal digits specified by the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a>.

> In the case of an off-chain payment agent the D-ASA state machine:
>
> - Regulates payments’ approval conditions (e.g. a coupon is due);
> - Notarizes the amounts and timestamps of payments settled off-chain.
