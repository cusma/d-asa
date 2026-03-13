# Denomination {#denomination}

> Debt instruments are denominated in a currency, in which principal and interests
> are calculated.

The D-ASA **MUST** be denominated either in an on-chain or off-chain *denomination
asset* \\([CUR]\\)[^1].

All values (`uint64`) are integer minor units of the relevant on-chain or off-chain
*denomination asset*.

> The reference implementation supports only on-chain ASA denominations (e.g., "stablecoins").

## On-chain denomination {#on-chain-denomination}

The *denomination asset* **MUST** be an Algorand Standard Asset (ASA), an Application
asset (App), or the ALGO.

The *denomination asset identifier* **MUST** be the ASA ID, the App ID, or `0` for
ALGO.

If asset is ALGO (`0`): amount is in microALGOs (\\( 10^{-6} \\) ALGO).

If asset is ASA or App: amount is in base units as per that asset’s `decimals`.

> [!TIP]
> The value (`uint64`) `10000` of an ASA denomination with 2 `decimals` is interpreted
> as `100.00` units of the ASA.

## Off-chain denomination {#off-chain-denomination}

The *denomination asset identifier* **MUST** be the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a> currency numeric code.

The *denomination asset* **MUST** use the decimal digits specified by the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a>.

If asset is ISO 4217 numeric code: amount is in minor units (\\( 10^{-d} \\) with
\\( d \\) as per ISO 4217 *digits*).

> [!TIP]
> The value (`uint64`) `10000` an EUR (ISO 4217, 2 decimals) denomination is interpreted
> as `100.00` Euro.

---

[^1]: ACTUS only allows ISO 4217 currency identifiers, therefore an on-chain denomination
is not supported by ACTUS.
