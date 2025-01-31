import pytest
from algokit_utils import SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetMetadata,
    AssetUpdateArgs,
    BaseDAsaClient,
    CommonAppCallParams,
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
        args=AssetUpdateArgs(metadata=updated_metadata)
    )
    metadata = base_d_asa_client_active.send.get_asset_metadata().abi_return
    assert metadata.prospectus_url == updated_metadata.prospectus_url


def test_fail_unauthorized(
    asset_metadata: AssetMetadata,
    oscar: SigningAccount,
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    # NOTE: This is now identified as a runtime error not a LogicError, because the error messages comes
    # directly from the ARC56 source.
    # see contets of the arc56 file for more details. This is also consistent with the behaviour on the utils-ts
    # https://github.com/algorandfoundation/algokit-utils-ts/blob/b1392427938594404b70148f6309363ca77b1b55/src/types/app-client.ts#L956
    with pytest.raises(Exception, match=err.UNAUTHORIZED):
        base_d_asa_client_active.send.update.asset_update(
            args=AssetUpdateArgs(metadata=asset_metadata),
            params=CommonAppCallParams(sender=oscar.address, signer=oscar.signer),
        )
