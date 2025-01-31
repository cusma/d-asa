import pytest
from algokit_utils import SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    BaseDAsaClient,
    CommonAppCallParams,
)
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    SetAssetSuspensionArgs,
)
from tests.utils import DAsaAuthority


def test_pass_set_asset_suspension(
    authority: DAsaAuthority, base_d_asa_client_active: BaseDAsaClient
) -> None:
    asset_suspended = (
        base_d_asa_client_active.send.get_asset_info().abi_return.suspended
    )
    assert not asset_suspended

    base_d_asa_client_active.send.set_asset_suspension(
        SetAssetSuspensionArgs(suspended=True),
        params=CommonAppCallParams(
            sender=authority.address,
        ),
    )

    asset_suspended = (
        base_d_asa_client_active.send.get_asset_info().abi_return.suspended
    )
    assert asset_suspended


def test_fail_unauthorized(
    oscar: SigningAccount, base_d_asa_client_active: BaseDAsaClient
) -> None:
    with pytest.raises(Exception, match=err.UNAUTHORIZED):
        base_d_asa_client_active.send.set_asset_suspension(
            SetAssetSuspensionArgs(suspended=True),
            params=CommonAppCallParams(
                sender=oscar.address,
            ),
        )
