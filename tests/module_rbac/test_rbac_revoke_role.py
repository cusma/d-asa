import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacAssignRoleArgs,
    RbacRevokeRoleArgs,
    SetDefaultStatusArgs,
)
from tests.utils import DAsaAuthority, DAsaTrustee


def test_pass_rbac_revoke_role(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    rbac_client.send.rbac_assign_role(
        RbacAssignRoleArgs(
            role_id=sc_cst.ROLE_AUTHORITY,
            role_address=no_role_account.address,
            config=b"",
        )
    )

    rbac_client.send.rbac_revoke_role(
        RbacRevokeRoleArgs(
            role_id=sc_cst.ROLE_AUTHORITY,
            role_address=no_role_account.address,
        )
    )

    roles = rbac_client.send.rbac_get_address_roles(no_role_account.address).abi_return
    assert not roles[3]


def test_fail_unauthorized(
    no_role_account: SigningAccount,
    authority: DAsaAuthority,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=authority.address,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_defaulted(
    trustee: DAsaTrustee,
    authority: DAsaAuthority,
    rbac_client: MockRbacModuleClient,
) -> None:
    rbac_client.send.set_default_status(
        SetDefaultStatusArgs(defaulted=True),
        params=CommonAppCallParams(sender=trustee.address),
    )

    with pytest.raises(LogicError, match=err.DEFAULTED):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=authority.address,
            )
        )


def test_fail_invalid_role(
    authority: DAsaAuthority,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=0,
                role_address=authority.address,
            )
        )


def test_fail_invalid_role_address(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=no_role_account.address,
            )
        )
