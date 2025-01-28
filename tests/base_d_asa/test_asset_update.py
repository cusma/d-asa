from copy import deepcopy

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetMetadata,
    BaseDAsaClient,
)


def test_pass_update(
    asset_metadata: AssetMetadata, base_d_asa_client_active: BaseDAsaClient
) -> None:
    metadata = base_d_asa_client_active.get_asset_metadata().return_value
    assert metadata.prospectus_url == asset_metadata.prospectus_url
    updated_metadata = deepcopy(asset_metadata)
    updated_metadata.prospectus_url = "Updated Prospectus"
    base_d_asa_client_active.update_asset_update(metadata=updated_metadata)
    metadata = base_d_asa_client_active.get_asset_metadata().return_value
    assert metadata.prospectus_url == updated_metadata.prospectus_url


def test_fail_unauthorized(
    asset_metadata: AssetMetadata,
    oscar: AddressAndSigner,
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_active.update_asset_update(
            metadata=asset_metadata,
            transaction_parameters=OnCompleteCallParameters(signer=oscar.signer),
        )
