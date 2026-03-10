# Settlement {#settlement}

> Debt instruments cash flows may be settled in a currency different from the denomination.

The D-ASA **MUST** define either an on-chain or off-chain *settlement asset* \\([CURS]\\)[^1]
to regulate the cash flows.

The *settlement asset identifier* (`uint64`) **MUST** be set using the `asset_config`
method.

All values (`uint64`) are integer minor units of the relevant on-chain or off-chain
*settlement asset*.

If the D-ASA **defines** a *settlement asset* different from the *denomination asset*,
then the respective denomination/settlement conversion rate is applied at settlement
time.

> The denomination/settlement conversion rate can be provided by different oracles,
> depending on if the denomination/settlement assets are on-chain or off-chain.

If the D-ASA **does not define** a different *settlement asset*, then the cash flows
**MUST** be settled in the denomination asset and the *settlement asset identifier*
**MUST** be equal to the *denomination asset identifier*.

## On-chain settlement {#on-chain-settlement}

The *settlement asset* **MUST** be an Algorand Standard Asset (ASA), an Application
asset (App), or the ALGO.

The *settlement asset identifier* **MUST** be the ASA ID, the App ID, or `0` for
ALGO.

If asset is ALGO (`0`): amount is in microALGOs (\\( 10{^-6} \\) ALGO).

If asset is ASA or App: amount is in base units as per that asset’s `decimals`.

{{#include ../../../_include/styles.md:example}}
> The value (`uint64`) `10000` of settlement in ASA settlement 2 decimals is interpreted
> as `100.00` units of the ASA.

> On-chain settlement is possible even if the denomination asset is a traditional
> off-chain currency.

## Off-chain settlement {#off-chain-settlement}

The *settlement asset identifier* **MUST** be the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a> currency numeric code.

The *settlement asset* **MUST** use the decimal digits specified by the <a href="https://en.wikipedia.org/wiki/ISO_4217">ISO
4217</a>.

If asset is ISO 4217 numeric code: amount is in minor units (\\( 10^{-d} \\) with
\\( d \\) as per ISO 4217 *digits*).

{{#include ../../../_include/styles.md:example}}
> The value (`uint64`) `10000` of a settlement in EUR (ISO 4217, 2 decimals) is
> interpreted as `100.00` Euro.

> In the case of an off-chain settlement, the D-ASA state machine:
>
> - Regulates payments’ approval conditions (e.g. a coupon is due);
> - Notarizes the amounts and timestamps of payments settled off-chain.

---

[^1]: ACTUS only allows ISO 4217 currency identifiers, therefore an on-chain settlement
is not supported by ACTUS.
