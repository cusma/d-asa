from smart_contracts import constants as cst
from smart_contracts.d_asa.deploy_config import (
    DEMO_FCB_NOMINAL_RATE,
    DEMO_NOTIONAL_PRINCIPAL,
    DEMO_NOTIONAL_UNIT_VALUE,
    DEMO_ZCB_DISCOUNT_BPS,
    DemoDeploymentContext,
    DenominationAsset,
    build_fixed_coupon_bond_demo,
    build_zero_coupon_bond_demo,
)

CURRENT_TS = 1_700_000_000
DENOMINATION_ASSET_ID = 12345
DENOMINATION_ASSET_DECIMALS = 2
ISSUANCE_DELAY_SECONDS = 30 * cst.DAY_2_SEC
FIXED_COUPON_PERIOD_SECONDS = 90 * cst.DAY_2_SEC
FIXED_COUPON_MATURITY_SECONDS = 1800 * cst.DAY_2_SEC
ZERO_COUPON_MATURITY_SECONDS = 360 * cst.DAY_2_SEC


def _context() -> DemoDeploymentContext:
    return DemoDeploymentContext(
        current_ts=CURRENT_TS,
        denomination_asset=DenominationAsset(
            asset_id=DENOMINATION_ASSET_ID,
            decimals=DENOMINATION_ASSET_DECIMALS,
        ),
    )


def test_fixed_coupon_bond_demo_builds_expected_schedule() -> None:
    spec = build_fixed_coupon_bond_demo(_context())
    normalized = spec.normalized

    issuance_date = CURRENT_TS + ISSUANCE_DELAY_SECONDS
    maturity_date = issuance_date + FIXED_COUPON_MATURITY_SECONDS
    expected_event_types = ["IED"] + ["IP"] * 20 + ["MD"]

    assert spec.label == "FCB"
    assert normalized.terms.denomination_asset_id == DENOMINATION_ASSET_ID
    assert normalized.terms.initial_exchange_date == issuance_date
    assert normalized.terms.maturity_date == maturity_date
    assert normalized.terms.notional_principal == 1_000_000
    assert normalized.terms.initial_exchange_amount == 1_000_000
    assert (
        normalized.terms.total_units
        == DEMO_NOTIONAL_PRINCIPAL // DEMO_NOTIONAL_UNIT_VALUE
    )
    assert normalized.terms.rate_reset_next == int(
        DEMO_FCB_NOMINAL_RATE * cst.FIXED_POINT_SCALE
    )
    assert [entry.event_type for entry in normalized.schedule] == expected_event_types
    assert normalized.schedule[0].scheduled_time == issuance_date
    assert (
        normalized.schedule[1].scheduled_time
        == issuance_date + FIXED_COUPON_PERIOD_SECONDS
    )
    assert normalized.schedule[-1].scheduled_time == maturity_date


def test_zero_coupon_bond_demo_builds_expected_schedule() -> None:
    spec = build_zero_coupon_bond_demo(_context())
    normalized = spec.normalized

    issuance_date = CURRENT_TS + ISSUANCE_DELAY_SECONDS
    maturity_date = issuance_date + ZERO_COUPON_MATURITY_SECONDS
    discount_amount = DEMO_NOTIONAL_PRINCIPAL * DEMO_ZCB_DISCOUNT_BPS // cst.BPS
    issue_price = (
        DEMO_NOTIONAL_PRINCIPAL - discount_amount
    ) * 10**DENOMINATION_ASSET_DECIMALS

    assert spec.label == "ZCB"
    assert normalized.terms.denomination_asset_id == DENOMINATION_ASSET_ID
    assert normalized.terms.initial_exchange_date == issuance_date
    assert normalized.terms.maturity_date == maturity_date
    assert normalized.terms.notional_principal == 1_000_000
    assert normalized.terms.initial_exchange_amount == issue_price
    assert (
        normalized.terms.total_units
        == DEMO_NOTIONAL_PRINCIPAL // DEMO_NOTIONAL_UNIT_VALUE
    )
    assert normalized.terms.rate_reset_next == 0
    assert [entry.event_type for entry in normalized.schedule] == ["IED", "MD"]
    assert normalized.schedule[0].scheduled_time == issuance_date
    assert normalized.schedule[1].scheduled_time == maturity_date
