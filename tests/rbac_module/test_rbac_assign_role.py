import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacAssignRoleArgs,
)


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


def test_fail_defaulted() -> None:
    pass  # TODO


def test_fail_invalid_role() -> None:
    pass  # TODO


def test_fail_invalid_role_address() -> None:
    pass  # TODO
