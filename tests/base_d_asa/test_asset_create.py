from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.abi import ArrayStaticType, ByteType, StringType, TupleType, UintType
from algosdk.encoding import encode_address

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetMetadata,
    BaseDAsaClient,
)
from smart_contracts.base_d_asa import config as sc_cfg

from .conftest import PROSPECTUS_URL


def test_pass_asset_create(
    asset_metadata: AssetMetadata,
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
    assert not state.settlement_asset_id
    assert not state.unit_value
    assert not state.day_count_convention

    # Metadata
    assert state.metadata.as_bytes == TupleType(
        [
            UintType(8),  # Contract Type
            UintType(8),  # Calendar
            UintType(8),  # Business Day Convention
            UintType(8),  # End of Month Convention
            UintType(8),  # Prepayment Effect
            UintType(8),  # Penalty Type
            ArrayStaticType(ByteType(), 32),  # Prospectus Hash
            StringType(),  # Prospectus URL
        ]
    ).encode(
        [
            sc_cst.CT_PAM,
            sc_cst.CLDR_NC,
            sc_cst.BDC_NOS,
            sc_cst.EOMC_SD,
            sc_cst.PPEF_N,
            sc_cst.PYTP_N,
            bytes(32),
            PROSPECTUS_URL,
        ]
    )

    # Principal and Supply
    assert not state.total_units
    assert not state.circulating_units
    assert not state.principal_discount

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
