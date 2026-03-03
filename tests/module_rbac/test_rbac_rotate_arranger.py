import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacRotateArrangerArgs,
)


def test_pass_rbac_rotate_arranger(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    rbac_client.send.rbac_rotate_arranger(
        RbacRotateArrangerArgs(new_arranger=no_role_account.address)
    )
    assert rbac_client.send.rbac_get_arranger().abi_return == no_role_account.address


def test_fail_unauthorized(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_rotate_arranger(
            RbacRotateArrangerArgs(new_arranger=no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_concrete_pass_rbac_rotate_arranger(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    shared_client_empty.send.rbac_rotate_arranger((no_role_account.address,))
    assert (
        shared_client_empty.send.rbac_get_arranger().abi_return
        == no_role_account.address
    )


def test_concrete_fail_unauthorized(
    no_role_account: SigningAccount,
    shared_client_empty,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_empty.send.rbac_rotate_arranger(
            (no_role_account.address,),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
