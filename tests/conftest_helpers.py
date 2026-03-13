from typing import Any

from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from src.d_asa.artifacts.dasa_client import (
    RbacAssignRoleArgs,
    RoleValidity,
)
from tests.conftest import INITIAL_ALGO_FUNDS


def create_role_account[RoleAccountType: SigningAccount](
    algorand: AlgorandClient,
    role_account_class: type[RoleAccountType],
    client: Any,
) -> RoleAccountType:
    """
    Creates and configures a role account (account_manager, authority, trustee, etc.).

    Args:
        algorand: AlgorandClient instance
        role_account_class: The role account class (DAsaAccountManager, DAsaAuthority, etc.)
        client: The client to assign the role on

    Returns:
        Configured role account
    """
    account = algorand.account.random()
    role_account = role_account_class(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=role_account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )

    client.send.rbac_assign_role(
        RbacAssignRoleArgs(
            role_id=role_account.role_id(),
            role_address=role_account.address,
            validity=RoleValidity(
                role_validity_start=0,
                role_validity_end=2**64 - 1,
            ),
        )
    )
    return role_account
