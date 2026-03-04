import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacAssignRoleArgs,
    RbacGetAddressRolesArgs,
    RbacRevokeRoleArgs,
)
from tests import utils
from tests.utils import DAsaAuthority


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

    roles = rbac_client.send.rbac_get_address_roles(
        RbacGetAddressRolesArgs(address=no_role_account.address),
    ).abi_return
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


def test_concrete_pass_rbac_revoke_role(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    shared_client_empty.send.rbac_assign_role(
        (
            sc_cst.ROLE_ACCOUNT_MANAGER,
            no_role_account.address,
            utils.set_role_config(),
        )
    )
    shared_client_empty.send.rbac_revoke_role(
        (
            sc_cst.ROLE_ACCOUNT_MANAGER,
            no_role_account.address,
        )
    )
    roles = shared_client_empty.send.rbac_get_address_roles(
        (no_role_account.address,)
    ).abi_return
    assert not roles[0]


def test_concrete_fail_unauthorized(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_empty.send.rbac_revoke_role(
            (
                sc_cst.ROLE_ACCOUNT_MANAGER,
                no_role_account.address,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_concrete_fail_defaulted(
    no_role_account: SigningAccount,
    shared_trustee,
    shared_client_empty,
) -> None:
    shared_client_empty.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_empty.send.rbac_revoke_role(
            (
                sc_cst.ROLE_ACCOUNT_MANAGER,
                no_role_account.address,
            )
        )


def test_concrete_fail_invalid_role(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        shared_client_empty.send.rbac_revoke_role((0, no_role_account.address))


def test_concrete_fail_invalid_role_address(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        shared_client_empty.send.rbac_revoke_role(
            (
                sc_cst.ROLE_ACCOUNT_MANAGER,
                no_role_account.address,
            )
        )
