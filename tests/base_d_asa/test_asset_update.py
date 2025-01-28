from copy import deepcopy

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    AssetMetadata,
    BaseDAsaClient,
)
from tests.utils import DAsaMetadata


def test_pass_update(
    asset_metadata: DAsaMetadata, base_d_asa_client_active: BaseDAsaClient
) -> None:
    metadata = base_d_asa_client_active.get_asset_metadata().return_value
    assert metadata.prospectus_url == asset_metadata.prospectus_url
    updated_metadata = deepcopy(asset_metadata)
    updated_metadata.prospectus_url = "Updated Prospectus"
    base_d_asa_client_active.update_asset_update(
        metadata=AssetMetadata(**asset_metadata.dictify())
    )
    metadata = base_d_asa_client_active.get_asset_metadata().return_value
    assert metadata.prospectus_url == updated_metadata.prospectus_url


def test_fail_unauthorized(
    asset_metadata: DAsaMetadata,
    oscar: AddressAndSigner,
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_active.update_asset_update(
            metadata=AssetMetadata(**asset_metadata.dictify()),
            transaction_parameters=OnCompleteCallParameters(signer=oscar.signer),
        )
