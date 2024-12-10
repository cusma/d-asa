from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.encoding import encode_address

from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from smart_contracts.base_d_asa import config as sc_cfg


def test_pass_asset_create(
    asset_metadata: bytes,
    arranger: AddressAndSigner,
    base_d_asa_client_void: BaseDAsaClient,
) -> None:
    base_d_asa_client_void.create_asset_create(
        arranger=arranger.address, metadata=asset_metadata
    )

    state = base_d_asa_client_void.get_global_state()

    # Roles
    assert encode_address(state.arranger.as_bytes) == arranger.address

    # Asset Configuration
    assert not state.denomination_asset_id
    assert not state.unit_value
    assert not state.day_count_convention

    # Metadata
    assert state.metadata.as_bytes == asset_metadata

    # Supply
    assert not state.total_units
    assert not state.circulating_units

    # Coupons
    assert not state.total_coupons

    # Time Schedule
    assert not state.primary_distribution_opening_date
    assert not state.primary_distribution_closure_date
    assert not state.issuance_date
    assert not state.secondary_market_opening_date
    assert not state.secondary_market_closure_date
    assert not state.maturity_date

    # Status
    assert state.status == sc_cfg.STATUS_EMPTY
    assert not state.suspended


def test_fail_invalid_state_schema() -> None:
    pass  # TODO