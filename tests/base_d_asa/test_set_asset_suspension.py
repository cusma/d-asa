import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from tests.utils import DAsaAuthority


def test_pass_set_asset_suspension(
    authority: DAsaAuthority, base_d_asa_client_active: BaseDAsaClient
) -> None:
    asset_suspended = base_d_asa_client_active.get_asset_info().return_value.suspended
    assert not asset_suspended

    base_d_asa_client_active.set_asset_suspension(
        suspended=True,
        transaction_parameters=OnCompleteCallParameters(
            signer=authority.signer,
            boxes=[(base_d_asa_client_active.app_id, authority.box_id)],
        ),
    )

    asset_suspended = base_d_asa_client_active.get_asset_info().return_value.suspended
    assert asset_suspended


def test_fail_unauthorized(
    oscar: AddressAndSigner, base_d_asa_client_active: BaseDAsaClient
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_active.set_asset_suspension(
            suspended=True,
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                boxes=[
                    (
                        base_d_asa_client_active.app_id,
                        DAsaAuthority.box_id_from_address(oscar.address),
                    )
                ],
            ),
        )
