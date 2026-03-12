import dataclasses
import importlib
from collections.abc import Callable
from typing import Any, TypeVar

from algokit_utils import (
    AlgorandClient,
    AssetOptInParams,
    AssetTransferParams,
    CommonAppCallParams,
    SigningAccount,
)

from tests import utils
from tests.conftest import INITIAL_ALGO_FUNDS

# Type variable for client types
ClientType = TypeVar("ClientType")
RoleAccountType = TypeVar("RoleAccountType", bound=SigningAccount)


def create_and_fund_client(
    algorand: AlgorandClient,
    factory_class: Any,
    arranger: SigningAccount,
    create_method_args: Any,
) -> Any:
    """
    Creates a typed app client using a factory and funds it.

    Args:
        algorand: AlgorandClient instance
        factory_class: Factory class for the client
        arranger: Account that will create the app
        create_method_args: Arguments to pass to the create method

    Returns:
        Created and funded client
    """
    factory = algorand.client.get_typed_app_factory(
        factory_class,
        default_sender=arranger.address,
        default_signer=arranger.signer,
    )
    client, _ = factory.send.create.asset_create(create_method_args)
    algorand.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return client


def create_bare_client_and_fund(
    algorand: AlgorandClient,
    factory_class: Any,
    arranger: SigningAccount,
) -> Any:
    """
    Creates a bare typed app client using a factory and funds it.

    Args:
        algorand: AlgorandClient instance
        factory_class: Factory class for the client
        arranger: Account that will create the app

    Returns:
        Created and funded client
    """
    factory = algorand.client.get_typed_app_factory(
        factory_class,
        default_sender=arranger.address,
        default_signer=arranger.signer,
    )
    client, _ = factory.send.create.bare()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )
    return client


def create_role_account(
    algorand: AlgorandClient,
    role_account_class: type[RoleAccountType],
    client: Any,
    role_config: bytes | None = None,
    rbac_assign_role_args_class: Any = None,
) -> RoleAccountType:
    """
    Creates and configures a role account (account_manager, authority, trustee, etc.).

    Args:
        algorand: AlgorandClient instance
        role_account_class: The role account class (DAsaAccountManager, DAsaAuthority, etc.)
        client: The client to assign the role on
        role_config: Optional role configuration bytes (defaults to basic config if None)
        rbac_assign_role_args_class: The RbacAssignRoleArgs class for the specific client

    Returns:
        Configured role account
    """
    account = algorand.account.random()
    role_account = role_account_class(private_key=account.private_key)

    algorand.account.ensure_funded_from_environment(
        account_to_fund=role_account.address,
        min_spending_balance=INITIAL_ALGO_FUNDS,
    )

    if role_config is None:
        role_config = utils.set_role_config()

    field_names = {
        field.name for field in dataclasses.fields(rbac_assign_role_args_class)
    }
    if "config" in field_names:
        assign_role_args = rbac_assign_role_args_class(
            role_id=role_account.role_id(),
            role_address=role_account.address,
            config=role_config,
        )
    elif "validity" in field_names:
        role_module = importlib.import_module(rbac_assign_role_args_class.__module__)
        role_validity_class = role_module.RoleValidity
        assign_role_args = rbac_assign_role_args_class(
            role_id=role_account.role_id(),
            role_address=role_account.address,
            validity=role_validity_class(
                role_validity_start=0,
                role_validity_end=2**64 - 1,
            ),
        )
    else:
        raise TypeError(
            f"Unsupported RBAC assign args shape: {rbac_assign_role_args_class.__name__}"
        )

    client.send.rbac_assign_role(assign_role_args)
    return role_account


def activate_client_with_config_and_funding(
    algorand: AlgorandClient,
    client: Any,
    bank: SigningAccount,
    d_asa_config: utils.DAsaConfig,
    total_asa_funds: int,
    asset_config_args_class: Any,
) -> Any:
    """
    Activates a client by configuring it and transferring denomination assets.

    Args:
        algorand: AlgorandClient instance
        client: The client to activate
        bank: Account that will transfer assets
        d_asa_config: D-ASA configuration
        total_asa_funds: Total amount of assets to transfer
        asset_config_args_class: The AssetConfigArgs class for the specific client

    Returns:
        The activated client
    """
    client.send.asset_config(asset_config_args_class(**d_asa_config.dictify()))

    algorand.send.asset_transfer(
        AssetTransferParams(
            asset_id=d_asa_config.denomination_asset_id,
            amount=total_asa_funds,
            receiver=client.app_address,
            sender=bank.address,
            signer=bank.signer,
        )
    )

    return client


def build_account_factory(
    algorand: AlgorandClient,
    currency: utils.Currency,
    account_manager: utils.DAsaAccountManager,
    account_open_args_class: Any,
) -> Callable[[Any], utils.DAsaAccount]:
    """
    Builds a factory function for creating D-ASA accounts.

    Args:
        algorand: AlgorandClient instance
        currency: Currency configuration
        account_manager: Account manager for opening accounts
        account_open_args_class: The AccountOpenArgs class for the specific client

    Returns:
        Factory function that creates D-ASA accounts
    """

    def _factory(client: Any) -> utils.DAsaAccount:
        account = algorand.account.random()

        algorand.account.ensure_funded_from_environment(
            account_to_fund=account.address,
            min_spending_balance=INITIAL_ALGO_FUNDS,
        )

        algorand.send.asset_opt_in(
            AssetOptInParams(
                asset_id=currency.id,
                sender=account.address,
                signer=account.signer,
            )
        )

        client.send.account_open(
            account_open_args_class(
                holding_address=account.address,
                payment_address=account.address,
            ),
            params=CommonAppCallParams(sender=account_manager.address),
        )
        return utils.DAsaAccount(
            d_asa_client=client,
            holding_address=account.address,
            private_key=account.private_key,
        )

    return _factory


def build_account_with_units_factory(
    account_factory: Callable[[Any], utils.DAsaAccount],
    primary_dealer: utils.DAsaPrimaryDealer,
    client: Any,
    primary_distribution_args_class: Any,
    initial_units: int,
) -> Callable[..., utils.DAsaAccount]:
    """
    Builds a factory function for creating D-ASA accounts with units.

    Args:
        account_factory: Factory for creating basic accounts
        primary_dealer: Primary dealer for distributing units
        client: The client to use for distribution
        primary_distribution_args_class: The PrimaryDistributionArgs class
        initial_units: Default number of units to distribute

    Returns:
        Factory function that creates accounts with units
    """

    def _factory(*, units: int = initial_units) -> utils.DAsaAccount:
        account = account_factory(client)
        client.send.primary_distribution(
            primary_distribution_args_class(
                holding_address=account.holding_address,
                units=units,
            ),
            params=CommonAppCallParams(sender=primary_dealer.address),
        )
        return account

    return _factory


def set_client_to_primary_phase(
    client: Any,
    set_secondary_time_events_args_class: Any,
    secondary_market_time_events: list[int],
) -> Any:
    """
    Sets a client to primary distribution phase.

    Args:
        client: The client to update
        set_secondary_time_events_args_class: The SetSecondaryTimeEventsArgs class
        secondary_market_time_events: List of secondary market time events

    Returns:
        The updated client
    """
    client.send.set_secondary_time_events(
        set_secondary_time_events_args_class(
            secondary_market_time_events=secondary_market_time_events
        )
    )
    state = client.state.global_state
    utils.time_warp(state.primary_distribution_opening_date)
    return client


def suspend_client(
    client: Any,
    authority: utils.DAsaAuthority,
    rbac_gov_asset_suspension_args_class: Any,
) -> Any:
    """
    Suspends a client.

    Args:
        client: The client to suspend
        authority: Authority account
        rbac_gov_asset_suspension_args_class: The RbacGovAssetSuspensionArgs class

    Returns:
        The suspended client
    """
    client.send.rbac_gov_asset_suspension(
        rbac_gov_asset_suspension_args_class(suspended=True),
        params=CommonAppCallParams(sender=authority.address),
    )
    return client


def set_client_to_default(
    client: Any,
    trustee: utils.DAsaTrustee,
    set_default_status_args_class: Any,
) -> Any:
    """
    Sets a client to defaulted status.

    Args:
        client: The client to default
        trustee: Trustee account
        set_default_status_args_class: The SetDefaultStatusArgs class

    Returns:
        The defaulted client
    """
    client.send.set_default_status(
        set_default_status_args_class(defaulted=True),
        params=CommonAppCallParams(sender=trustee.address),
    )
    return client
