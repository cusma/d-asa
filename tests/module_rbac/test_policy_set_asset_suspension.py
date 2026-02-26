import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacGovAssetSuspensionArgs,
)
from tests.utils import DAsaAuthority


def test_pass_rbac_gov_asset_suspension(
    authority: DAsaAuthority, rbac_client: MockRbacModuleClient
) -> None:
    asset_suspended = rbac_client.state.global_state.asset_suspended
    assert not asset_suspended

    rbac_client.send.rbac_gov_asset_suspension(
        RbacGovAssetSuspensionArgs(suspended=True),
        params=CommonAppCallParams(
            sender=authority.address,
        ),
    )

    asset_suspended = rbac_client.state.global_state.asset_suspended
    assert asset_suspended


def test_fail_unauthorized(
    no_role_account: SigningAccount, rbac_client: MockRbacModuleClient
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_gov_asset_suspension(
            RbacGovAssetSuspensionArgs(suspended=True),
            params=CommonAppCallParams(
                sender=no_role_account.address,
            ),
        )
