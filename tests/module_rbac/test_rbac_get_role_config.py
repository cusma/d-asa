import pytest
from algokit_utils import LogicError

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
    RbacGetRoleConfigArgs,
)
from tests import utils
from tests.utils import DAsaAuthority


def test_pass_rbac_get_role_config(
    authority: DAsaAuthority,
    rbac_client: MockRbacModuleClient,
) -> None:
    config = rbac_client.send.rbac_get_role_config(
        RbacGetRoleConfigArgs(
            role_id=sc_cst.ROLE_AUTHORITY,
            role_address=authority.address,
        )
    ).abi_return

    expected = utils.set_role_config()
    expected_cfg = type(config).from_bytes(expected)
    assert config.role_validity_start == expected_cfg.role_validity_start
    assert config.role_validity_end == expected_cfg.role_validity_end


def test_pass_rbac_get_arranger_role_config(
    arranger,
    rbac_client: MockRbacModuleClient,
) -> None:
    config = rbac_client.send.rbac_get_role_config(
        RbacGetRoleConfigArgs(
            role_id=sc_cst.ROLE_ARRANGER,
            role_address=arranger.address,
        )
    ).abi_return
    assert config.role_validity_start == 0
    assert config.role_validity_end == 0


def test_fail_invalid_role(rbac_client: MockRbacModuleClient) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        rbac_client.send.rbac_get_role_config(
            RbacGetRoleConfigArgs(role_id=0, role_address=rbac_client.app_address)
        )


def test_fail_invalid_role_address(
    no_role_account,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_get_role_config(
            RbacGetRoleConfigArgs(
                role_id=sc_cst.ROLE_AUTHORITY,
                role_address=no_role_account.address,
            )
        )
