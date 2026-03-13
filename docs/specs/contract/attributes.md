# Main Contract Attributes

The following are the main ACTUS Contract Attributes.

This section is intended to clarify ACTUS-specific terminology and map it to the
corresponding terms used in the D-ASA implementation. ACTUS remains the normative
specification throughout.

> [!IMPORTANT]
> In the event of any inconsistency, the ACTUS specification shall prevail.

> For further details, refer to the ACTUS specification.

## Principal

> Debt instruments principal is the amount of capital borrowed and used as a base
> for calculating interest.

The D-ASA **MUST** define the *principal* \\( [NT] \\), expressed in the *denomination
asset*.

The D-ASA **MUST** define a *minimum denomination*, expressed in the *denomination
asset*.

The *minimum denomination* **MUST** be a divisor of the *principal*.

### Discount

> Debt instruments principal may be placed at premium or discount on issuance.

The D-ASA **MAY** define a *premium* or *discount* \\( [PDIED] \\) to apply to the
principal on the issuance.

> [!TIP]
> Let’s have a D-ASA denominated in EUR, with a principal of 1M EUR paid at maturity
> and a minimum denomination of 1,000 EUR. The D-ASA has a principal discount of
> 200 bps (2%) at the issuance. Each D-ASA unit is sold on the primary market at
> 980 EUR and will be redeemed for 1,000 EUR of principal at maturity.

## Interests

> Debt instruments interest is calculated on a fixed or variable rate on the outstanding
> principal.

> The interest rate is the nominal yield paid by the debt instrument on the principal,
> usually defined *per-annum* (APY).

### Interest Rate

> Debt instruments may have variable interest rates, based on external data oracles.

The D-ASA **MAY** define a nominal *interest rate* \\( [IPNR] \\).

If the interest rate is variable, the D-ASA **MUST** define *interest update dates*
known \\( [RRF] \\) or unknown \\( [RR] \\).

#### Cap and Floor

> Debt instruments may define limitations to the interest rate variability, either
> over the whole contract lifespan or over specific periods.

#### Life Caps

The D-ASA **MAY** define a *life cap* \\( [RRLC] \\) to apply to the variable *interest
rate*.

The D-ASA **MAY** define a *life floor* \\( [RRLF] \\) to apply to the variable
*interest rate*.

#### Period Caps

The D-ASA **MAY** define a *period cap* \\( [RRPC] \\) to the variable *interest
rate*.

The D-ASA **MAY** define a *period floor* \\( [RRPF] \\) to apply to the variable
*interest rate*.

#### Fixing Period

> Debt instruments usually schedule interest rate updates before the new rate applies
> (defined by the rate reset schedule).

The D-ASA **MUST** define a *fixing period* \\( [RRFIX] \\) that specifies a period
of time before the *interest payment* \\( [IP] \\) in which the interest can be
updated.

## Issuance

> Debt instruments start accruing interest on the issuance date.

The D-ASA **MUST** have an *initial exchange date* \\( [IED] \\) (issuance).

## Maturity

> Debt instruments may have a maturity date, on which the principal is repaid and
> the contract obligations expire.

> Debt instruments may have a fixed or variable maturity date.

The D-ASA **MAY** have a *maturity date* \\( [MD] \\).

The *maturity date* **MAY** be updated in case of pre-payment options.

## Prepayment Options

> Debt instruments could have early repayment options to repay the principal to
> investors (partially or totally) before maturity or to reduce the maturity date.

> Debt instrument with defined maturity date may terminate earlier if the full principal
> redemption happens earlier than maturity.

If the debt instrument has early repayment options, the D-ASA **MUST** implement
the **OPTIONAL** `set_early_repayment_option` method.

### Prepayment Effects

> Debt instruments could have early repayment options to repay the principal to
> investors (partially or totally) before maturity or to reduce the maturity date.

> Debt instrument with a defined maturity date may terminate earlier if the full
> principal redemption happens earlier than maturity.

An early repayment option could have different *prepayment effects* \\( [PPEF] \\):

- It **MAY** repay the *principal* partially or totally before the *maturity date*;

- It **MAY** reduce the *maturity date*.

The *prepayment effect* **MUST** be identified with one of the following enumerated
IDs:

| ID    |                 Name                 | ACTUS Acronym | Description                                                                                     |
|:------|:------------------------------------:|---------------|:------------------------------------------------------------------------------------------------|
| `0`   |            No Prepayment             | \\([N]\\)     | Prepayment is not allowed under the agreement                                                   |
| `1`   | Prepayment Reduces Redemption Amount | \\([A]\\)     | Prepayment is allowed and reduces the redemption amount for the remaining period up to maturity |
| `2`   |     Prepayment Reduces Maturity      | \\([M]\\)     | Prepayment is allowed and reduces the maturity                                                  |

### Penalties

> Debt instruments may have a penalty as a consequence of an early repayment option.

The D-ASA **MAY** define a *penalty type* \\( [PYTP] \\) for the early repayment
options.

The *penalty type* **MUST** be identified with one of the following enumerated IDs:

| ID    |            Name            | ACTUS Acronym | Description                                                                                            |
|:------|:--------------------------:|---------------|:-------------------------------------------------------------------------------------------------------|
| `0`   |         No Penalty         | \\([N]\\)     | No penalty applies                                                                                     |
| `1`   |       Fixed Penalty        | \\([A]\\)     | A fixed amount applies as penalty                                                                      |
| `2`   |      Relative Penalty      | \\([R]\\)     | A penalty relative to the notional outstanding applies                                                 |
| `3`   | Interest Rate Differential | \\([I]\\)     | A penalty based on the current interest rate differential relative to the notional outstanding applies |

## Performance

> Debt instruments performances are exposed to credit risks.

The D-ASA *performance* \\( [PRF] \\) **MUST** be identified with one of the following
enumerated IDs:

| ID  |    Name    | ACTUS Acronym | Description                                                                          |
|:----|:----------:|---------------|:-------------------------------------------------------------------------------------|
| `0` | Performant | \\( [PF] \\)  | Contract is performing according to terms and conditions                             |
| `1` |  Delayed   | \\( [DL] \\)  | Contractual payment obligations are delayed according to the *grace period*          |
| `2` | Delinquent | \\( [DQ] \\)  | Contractual payment obligations are delinquent according to the *delinquency period* |
| `3` |  Default   | \\( [DF] \\)  | Contract defaulted on payment obligations according to *delinquency period*          |
| `4` |  Matured   | \\( [MA] \\)  | Contract matured                                                                     |
| `5` | Terminated | \\( [TE] \\)  | Contract has been terminated                                                         |

> [!NOTE]
> The current reference implementation supports manual default-performance tracking
> through a boolean `defaulted` flag. It does not yet model the full `PRF` lifecycle
> enum or automatic grace-period and delinquency transitions on chain.

### Grace Period

> Debt instruments may define a grace period as a time window after the payment
> due date during which payment may be retried without a penalty.

The D-ASA **MAY** define a *grace period* \\( [GRP] \\).

### Delinquency Period

> Debt instruments may define a delinquency period as a time window after the grace
> period. If payment happens after the delinquency period, then the counterparty
> is in technical default.

The D-ASA **MAY** define a *delinquency period* \\( [DQP] \\).

### Default

> Default is the ultimate failure to pay the lenders according to the payment obligations.
> When this happens, the creditors have the right to declare default to the debtors.

> Default processes require the intervention of regulatory bodies and courts, therefore
> the D-ASA default status bridges the default process off-chain.

The D-ASA **SHOULD** enter *default* status if it cannot perform payments on due
dates.

The D-ASA **MAY** disable all non-administrative methods on *default* status.

> The D-ASA default can be called either automatically (based on program conditions)
> or manually (based on the decision of a trustee).

The *Trustee* **MAY** set the default status with the `contract_set_default_status`
method.

> [!TIP]
> The D-ASA has no *grace period* and no *delinquency period*. A D-ASA coupon payment
> is triggered on due date, but there is not enough liquidity to pay all the investors.
> The D-ASA contract automatically enters in *default* immediately.

> [!TIP]
> The D-ASA has a *grace period* and a *delinquency period*. A D-ASA coupon payment
> is triggered on due date, but there is not enough liquidity to pay all the investors.
> The D-ASA program starts counting the *grace period* and *delinquency period*.
> If the *delinquency period* expires, then the contract enters in *default*.

> [!TIP]
> A D-ASA coupon payment is triggered on due date, but there is not enough liquidity
> to pay all the investors. The D-ASA contract relies on a Trustee to call the *default*.
