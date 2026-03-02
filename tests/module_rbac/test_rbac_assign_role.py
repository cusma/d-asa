import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacAssignRoleArgs,
    SetDefaultStatusArgs,
)
from tests import utils
from tests.utils import DAsaTrustee


def test_pass_rbac_assign_role(
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


def test_fail_unauthorized(
    no_role_account: SigningAccount, rbac_client: MockRbacModuleClient
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=no_role_account.address,
                config=b"",
            ),
            params=CommonAppCallParams(
                sender=no_role_account.address,
            ),
        )


def test_fail_defaulted(
    trustee: DAsaTrustee,
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    rbac_client.send.set_default_status(
        SetDefaultStatusArgs(defaulted=True),
        params=CommonAppCallParams(sender=trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=no_role_account.address,
                config=b"",
            )
        )


def test_fail_invalid_role(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=0,
                role_address=no_role_account.address,
                config=b"",
            )
        )


def test_fail_invalid_role_address(
    authority: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=authority.address,
                config=b"",
            )
        )


def test_concrete_pass_rbac_assign_role(
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
    roles = shared_client_empty.send.rbac_get_address_roles(
        (no_role_account.address,)
    ).abi_return
    assert roles[0]


def test_concrete_fail_unauthorized(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_empty.send.rbac_assign_role(
            (
                sc_cst.ROLE_ACCOUNT_MANAGER,
                no_role_account.address,
                utils.set_role_config(),
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
        shared_client_empty.send.rbac_assign_role(
            (
                sc_cst.ROLE_ACCOUNT_MANAGER,
                no_role_account.address,
                utils.set_role_config(),
            )
        )


def test_concrete_fail_invalid_role(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        shared_client_empty.send.rbac_assign_role(
            (
                0,
                no_role_account.address,
                utils.set_role_config(),
            )
        )


def test_concrete_fail_invalid_role_address(
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
    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        shared_client_empty.send.rbac_assign_role(
            (
                sc_cst.ROLE_ACCOUNT_MANAGER,
                no_role_account.address,
                utils.set_role_config(),
            )
        )
