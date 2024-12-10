# Principal (Par) {#principal-(par)}

> Debt instruments principal is the amount of capital borrowed and used as a base
> for calculating interest.

The D-ASA **MAY** define the *principal* (`uint64`)*,* expressed in the *denomination
asset*.

If the D-ASA has a *principal*, it **MUST** define a *minimum denomination* (`uint64`),
expressed in the *denomination asset*.

The *minimum denomination* **MUST** be a divisor of the *principal*.

The *principal* and the *minimum denomination* **MUST** be set using the `asset_config`
method.

If the D-ASA has no defined *principal*, the *principal* and the *minimum denomination*
**MUST** be set to `0`.
