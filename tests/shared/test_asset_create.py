from typing import Any

from algokit_utils import SigningAccount

from smart_contracts import enums

from .cases import ContractCase


def test_pass_asset_create(
    arranger: SigningAccount,
    contract_case: ContractCase,
    shared_asset_metadata: Any,
    shared_client_empty: Any,
) -> None:
    state = shared_client_empty.state.global_state

    assert state.arranger == arranger.address
    assert not state.denomination_asset_id
    assert not state.settlement_asset_id
    assert not state.unit_value
    assert not state.day_count_convention

    metadata = shared_client_empty.send.get_asset_metadata().abi_return
    assert metadata.contract_type == shared_asset_metadata.contract_type
    assert metadata.calendar == shared_asset_metadata.calendar
    assert (
        metadata.business_day_convention
        == shared_asset_metadata.business_day_convention
    )
    assert (
        metadata.end_of_month_convention
        == shared_asset_metadata.end_of_month_convention
    )
    assert metadata.prepayment_effect == shared_asset_metadata.prepayment_effect
    assert metadata.penalty_type == shared_asset_metadata.penalty_type
    assert bytes(metadata.prospectus_hash) == shared_asset_metadata.prospectus_hash
    assert metadata.prospectus_url == shared_asset_metadata.prospectus_url

    assert not state.total_units
    assert not state.circulating_units
    assert not state.principal_discount
    assert not state.total_coupons

    if contract_case.capabilities.has_coupon and hasattr(state, "paid_coupon_units"):
        assert not state.paid_coupon_units
    if contract_case.capabilities.has_time_periods and hasattr(state, "coupon_period"):
        assert not state.coupon_period

    assert not state.primary_distribution_opening_date
    assert not state.primary_distribution_closure_date
    assert not state.issuance_date
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date
    assert not state.maturity_date

    assert state.status == enums.STATUS_INACTIVE
    assert not state.asset_suspended
