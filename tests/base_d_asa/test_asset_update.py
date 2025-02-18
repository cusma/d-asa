import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetMetadata,
    AssetUpdateArgs,
    BaseDAsaClient,
)


def test_pass_update(
    asset_metadata: AssetMetadata, base_d_asa_client_active: BaseDAsaClient
) -> None:
    metadata = base_d_asa_client_active.send.get_asset_metadata().abi_return
    assert metadata.prospectus_url == asset_metadata.prospectus_url
    updated_metadata = AssetMetadata(
        contract_type=sc_cst.CT_PAM,
        calendar=sc_cst.CLDR_NC,
        business_day_convention=sc_cst.BDC_NOS,
        end_of_month_convention=sc_cst.EOMC_SD,
        prepayment_effect=sc_cst.PPEF_N,
        penalty_type=sc_cst.PYTP_N,
        prospectus_hash=bytes(32),
        prospectus_url="Updated Prospectus",
    )
    base_d_asa_client_active.send.update.asset_update(
        AssetUpdateArgs(metadata=updated_metadata)
    )
    metadata = base_d_asa_client_active.send.get_asset_metadata().abi_return
    assert metadata.prospectus_url == updated_metadata.prospectus_url


def test_fail_unauthorized(
    asset_metadata: AssetMetadata,
    oscar: SigningAccount,
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_active.send.update.asset_update(
            AssetUpdateArgs(metadata=asset_metadata),
            params=CommonAppCallParams(sender=oscar.address),
        )
