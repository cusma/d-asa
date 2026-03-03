from algokit_utils import SigningAccount

from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
)
from tests.utils import (
    DAsaAccountManager,
    DAsaAuthority,
    DAsaInterestOracle,
    DAsaPrimaryDealer,
    DAsaTrustee,
)


def test_pass_rbac_get_address_roles_for_assigned_accounts(
    rbac_client: MockRbacModuleClient,
    account_manager: DAsaAccountManager,
    primary_dealer: DAsaPrimaryDealer,
    trustee: DAsaTrustee,
    authority: DAsaAuthority,
    interest_oracle: DAsaInterestOracle,
) -> None:
    account_manager_roles = rbac_client.send.rbac_get_address_roles(
        account_manager.address
    ).abi_return
    assert account_manager_roles == (True, False, False, False, False)

    primary_dealer_roles = rbac_client.send.rbac_get_address_roles(
        primary_dealer.address
    ).abi_return
    assert primary_dealer_roles == (False, True, False, False, False)

    trustee_roles = rbac_client.send.rbac_get_address_roles(trustee.address).abi_return
    assert trustee_roles == (False, False, True, False, False)

    authority_roles = rbac_client.send.rbac_get_address_roles(
        authority.address
    ).abi_return
    assert authority_roles == (False, False, False, True, False)

    interest_oracle_roles = rbac_client.send.rbac_get_address_roles(
        interest_oracle.address
    ).abi_return
    assert interest_oracle_roles == (False, False, False, False, True)


def test_pass_rbac_get_address_roles_for_unassigned_account(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    roles = rbac_client.send.rbac_get_address_roles(no_role_account.address).abi_return
    assert roles == (False, False, False, False, False)


def test_concrete_pass_rbac_get_address_roles(
    no_role_account: SigningAccount,
    shared_account_manager,
    shared_client_empty,
) -> None:
    manager_roles = shared_client_empty.send.rbac_get_address_roles(
        (shared_account_manager.address,)
    ).abi_return
    assert manager_roles == (True, False, False, False, False)

    unassigned_roles = shared_client_empty.send.rbac_get_address_roles(
        (no_role_account.address,)
    ).abi_return
    assert unassigned_roles == (False, False, False, False, False)
