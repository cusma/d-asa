# Denomination {#denomination}

> Debt instruments are denominated in a currency, in which principal and interests
> are calculated.

The D-ASA **MUST** be denominated either in an on-chain or off-chain *denomination
asset* \\([CUR]\\)[^1].

The *denomination asset identifier* (`uint64`) **MUST** be set using the `asset_config`
method.

## On-chain denomination {#on-chain-denomination}

The *denomination asset* **MUST** be an Algorand Standard Asset (ASA), an Application
asset (App), or the ALGO.

The *denomination asset identifier* **MUST** be the ASA ID, the App ID, or `0`for
ALGO.

## Off-chain denomination {#off-chain-denomination}

The *denomination asset identifier* **MUST** the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a> currency numeric code.

The *denomination asset* **MUST** use the decimal digits specified by the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a>.

---

[^1]: ACTUS only allows ISO 4217 currency identifiers, therefore an on-chain denomination
is not supported by ACTUS.
