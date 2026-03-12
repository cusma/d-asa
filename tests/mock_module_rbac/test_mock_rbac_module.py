import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import enums
from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
    MockRbacModuleSend,
    RbacAssignRoleArgs,
    RbacContractSuspensionArgs,
    RbacGetAddressRolesArgs,
    RbacGetRoleValidityArgs,
    RbacRevokeRoleArgs,
    RbacRotateArrangerArgs,
    RbacSetOpDaemonArgs,
    RoleValidity,
)
from tests import utils
from tests.utils import (
    DAsaAccountManager,
    DAsaAuthority,
    DAsaInterestOracle,
    DAsaPrimaryDealer,
    DAsaTrustee,
)


def assert_role_mask(
    roles: tuple[bool, bool, bool, bool, bool] | list[bool],
    *,
    account_manager: bool = False,
    primary_dealer: bool = False,
    trustee: bool = False,
    authority: bool = False,
    observer: bool = False,
) -> None:
    assert tuple(roles) == (
        account_manager,
        primary_dealer,
        trustee,
        authority,
        observer,
    )


def test_mock_rbac_send_surface_matches_current_abi() -> None:
    assert {name for name in dir(MockRbacModuleSend) if not name.startswith("_")} == {
        "clear_state",
        "rbac_assign_role",
        "rbac_get_address_roles",
        "rbac_get_arranger",
        "rbac_get_role_validity",
        "rbac_contract_suspension",
        "rbac_revoke_role",
        "rbac_rotate_arranger",
        "rbac_set_op_daemon",
        "update",
    }


def test_contract_update_is_arranger_only(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    result = rbac_client.send.update.contract_update()
    assert result.confirmation

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.update.contract_update(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_rbac_get_arranger_reflects_global_state(
    arranger: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    assert rbac_client.send.rbac_get_arranger().abi_return == arranger.address
    assert rbac_client.state.global_state.arranger == arranger.address


def test_rbac_set_op_daemon_is_arranger_only(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    result = rbac_client.send.rbac_set_op_daemon(
        RbacSetOpDaemonArgs(address=no_role_account.address)
    )
    assert result.abi_return > 0
    assert rbac_client.state.global_state.op_daemon == no_role_account.address

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_set_op_daemon(
            RbacSetOpDaemonArgs(address=rbac_client.app_address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_rbac_rotate_arranger_transfers_control(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    rbac_client.send.rbac_rotate_arranger(
        RbacRotateArrangerArgs(new_arranger=no_role_account.address)
    )
    assert rbac_client.send.rbac_get_arranger().abi_return == no_role_account.address

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_set_op_daemon(
            RbacSetOpDaemonArgs(address=rbac_client.app_address)
        )

    rbac_client.send.rbac_set_op_daemon(
        RbacSetOpDaemonArgs(address=rbac_client.app_address),
        params=CommonAppCallParams(sender=no_role_account.address),
    )
    assert rbac_client.state.global_state.op_daemon == rbac_client.app_address


def test_rbac_assign_role_updates_role_validity_and_masks(
    algorand: AlgorandClient,
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    current_timestamp = utils.get_latest_timestamp(algorand.client.algod)
    validity = RoleValidity(
        role_validity_start=current_timestamp - 1,
        role_validity_end=current_timestamp + 1_000,
    )

    result = rbac_client.send.rbac_assign_role(
        RbacAssignRoleArgs(
            role_id=enums.ROLE_AUTHORITY,
            role_address=no_role_account.address,
            validity=validity,
        )
    )
    assert result.abi_return > 0

    roles = rbac_client.send.rbac_get_address_roles(
        RbacGetAddressRolesArgs(address=no_role_account.address)
    ).abi_return
    assert_role_mask(roles, authority=True)

    stored_validity = rbac_client.send.rbac_get_role_validity(
        RbacGetRoleValidityArgs(
            role_id=enums.ROLE_AUTHORITY,
            role_address=no_role_account.address,
        )
    ).abi_return
    assert stored_validity == validity
    assert (
        rbac_client.state.box.authority.get_value(no_role_account.address) == validity
    )


def test_rbac_assign_role_rejects_invalid_calls(
    authority: DAsaAuthority,
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=enums.ROLE_AUTHORITY,
                role_address=no_role_account.address,
                validity=RoleValidity(0, 2**64 - 1),
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )

    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=0,
                role_address=no_role_account.address,
                validity=RoleValidity(0, 2**64 - 1),
            )
        )

    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_assign_role(
            RbacAssignRoleArgs(
                role_id=enums.ROLE_AUTHORITY,
                role_address=authority.address,
                validity=RoleValidity(0, 2**64 - 1),
            )
        )


def test_rbac_revoke_role_removes_assignment(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    rbac_client.send.rbac_assign_role(
        RbacAssignRoleArgs(
            role_id=enums.ROLE_AUTHORITY,
            role_address=no_role_account.address,
            validity=RoleValidity(0, 2**64 - 1),
        )
    )

    result = rbac_client.send.rbac_revoke_role(
        RbacRevokeRoleArgs(
            role_id=enums.ROLE_AUTHORITY,
            role_address=no_role_account.address,
        )
    )
    assert result.abi_return > 0

    roles = rbac_client.send.rbac_get_address_roles(
        RbacGetAddressRolesArgs(address=no_role_account.address)
    ).abi_return
    assert_role_mask(roles)
    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_get_role_validity(
            RbacGetRoleValidityArgs(
                role_id=enums.ROLE_AUTHORITY,
                role_address=no_role_account.address,
            )
        )


def test_rbac_revoke_role_rejects_invalid_calls(
    authority: DAsaAuthority,
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=enums.ROLE_AUTHORITY,
                role_address=authority.address,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )

    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=0,
                role_address=authority.address,
            )
        )

    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_revoke_role(
            RbacRevokeRoleArgs(
                role_id=enums.ROLE_AUTHORITY,
                role_address=no_role_account.address,
            )
        )


def test_rbac_gov_asset_suspension_is_authority_only(
    authority: DAsaAuthority,
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    assert not rbac_client.state.global_state.asset_suspended

    result = rbac_client.send.rbac_contract_suspension(
        RbacContractSuspensionArgs(suspended=True),
        params=CommonAppCallParams(sender=authority.address),
    )
    assert result.abi_return > 0
    assert rbac_client.state.global_state.asset_suspended

    rbac_client.send.rbac_contract_suspension(
        RbacContractSuspensionArgs(suspended=False),
        params=CommonAppCallParams(sender=authority.address),
    )
    assert not rbac_client.state.global_state.asset_suspended

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.rbac_contract_suspension(
            RbacContractSuspensionArgs(suspended=True),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_rbac_get_address_roles_covers_every_role_fixture(
    rbac_client: MockRbacModuleClient,
    account_manager: DAsaAccountManager,
    primary_dealer: DAsaPrimaryDealer,
    trustee: DAsaTrustee,
    authority: DAsaAuthority,
    interest_oracle: DAsaInterestOracle,
    no_role_account: SigningAccount,
) -> None:
    assert_role_mask(
        rbac_client.send.rbac_get_address_roles(
            RbacGetAddressRolesArgs(address=account_manager.address)
        ).abi_return,
        account_manager=True,
    )
    assert_role_mask(
        rbac_client.send.rbac_get_address_roles(
            RbacGetAddressRolesArgs(address=primary_dealer.address)
        ).abi_return,
        primary_dealer=True,
    )
    assert_role_mask(
        rbac_client.send.rbac_get_address_roles(
            RbacGetAddressRolesArgs(address=trustee.address)
        ).abi_return,
        trustee=True,
    )
    assert_role_mask(
        rbac_client.send.rbac_get_address_roles(
            RbacGetAddressRolesArgs(address=authority.address)
        ).abi_return,
        authority=True,
    )
    assert_role_mask(
        rbac_client.send.rbac_get_address_roles(
            RbacGetAddressRolesArgs(address=interest_oracle.address)
        ).abi_return,
        observer=True,
    )
    assert_role_mask(
        rbac_client.send.rbac_get_address_roles(
            RbacGetAddressRolesArgs(address=no_role_account.address)
        ).abi_return
    )


def test_rbac_get_role_validity_reports_arranger_and_rejects_invalid_inputs(
    arranger: SigningAccount,
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    arranger_validity = rbac_client.send.rbac_get_role_validity(
        RbacGetRoleValidityArgs(
            role_id=enums.ROLE_ARRANGER,
            role_address=arranger.address,
        )
    ).abi_return
    assert arranger_validity == RoleValidity(0, 0)

    with pytest.raises(LogicError, match=err.INVALID_ROLE):
        rbac_client.send.rbac_get_role_validity(
            RbacGetRoleValidityArgs(
                role_id=0,
                role_address=no_role_account.address,
            )
        )

    with pytest.raises(LogicError, match=err.INVALID_ROLE_ADDRESS):
        rbac_client.send.rbac_get_role_validity(
            RbacGetRoleValidityArgs(
                role_id=enums.ROLE_AUTHORITY,
                role_address=no_role_account.address,
            )
        )
