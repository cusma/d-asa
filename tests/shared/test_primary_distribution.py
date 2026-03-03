from collections.abc import Callable
from typing import Any

import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from tests.utils import DAsaAccount, get_latest_timestamp, time_warp

from .cases import ContractCase

_ACCOUNT_TEST_UNITS = 7


def test_pass_primary_distribution(
    contract_case: ContractCase,
    shared_primary_dealer: Any,
    shared_client_primary: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    state = shared_client_primary.state.global_state
    assert state.circulating_units == 0

    remaining_units = shared_client_primary.send.primary_distribution(
        contract_case.primary_distribution_args_cls(
            holding_address=account.holding_address,
            units=_ACCOUNT_TEST_UNITS,
        ),
        params=CommonAppCallParams(sender=shared_primary_dealer.address),
    ).abi_return

    state = shared_client_primary.state.global_state
    assert state.circulating_units == _ACCOUNT_TEST_UNITS
    assert remaining_units == state.total_units - state.circulating_units
    assert account.payment_address == account.holding_address
    assert account.units == _ACCOUNT_TEST_UNITS
    assert account.paid_coupons == 0


def test_fail_primary_distribution_closed(
    algorand: AlgorandClient,
    contract_case: ContractCase,
    shared_primary_dealer: Any,
    shared_client_primary: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    state = shared_client_primary.state.global_state
    time_warp(state.primary_distribution_closure_date)
    assert (
        get_latest_timestamp(algorand.client.algod)
        >= state.primary_distribution_closure_date
    )

    with pytest.raises(LogicError, match=err.PRIMARY_DISTRIBUTION_CLOSED):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=account.holding_address,
                units=_ACCOUNT_TEST_UNITS,
            ),
            params=CommonAppCallParams(sender=shared_primary_dealer.address),
        )


def test_fail_unauthorized(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_client_primary: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=account.holding_address,
                units=_ACCOUNT_TEST_UNITS,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_invalid_holding_address(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_primary_dealer: Any,
    shared_client_primary: Any,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=no_role_account.address,
                units=_ACCOUNT_TEST_UNITS,
            ),
            params=CommonAppCallParams(sender=shared_primary_dealer.address),
        )


def test_fail_defaulted_status(
    contract_case: ContractCase,
    shared_client_primary: Any,
    shared_trustee: Any,
    shared_primary_dealer: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    shared_client_primary.send.set_default_status(
        contract_case.set_default_status_args_cls(defaulted=True),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )

    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=account.holding_address,
                units=_ACCOUNT_TEST_UNITS,
            ),
            params=CommonAppCallParams(sender=shared_primary_dealer.address),
        )


def test_fail_suspended(
    contract_case: ContractCase,
    shared_authority: Any,
    shared_primary_dealer: Any,
    shared_client_primary: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    shared_client_primary.send.rbac_gov_asset_suspension(
        contract_case.rbac_gov_asset_suspension_args_cls(suspended=True),
        params=CommonAppCallParams(sender=shared_authority.address),
    )

    with pytest.raises(LogicError, match=err.SUSPENDED):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=account.holding_address,
                units=_ACCOUNT_TEST_UNITS,
            ),
            params=CommonAppCallParams(sender=shared_primary_dealer.address),
        )


def test_fail_zero_units(
    contract_case: ContractCase,
    shared_primary_dealer: Any,
    shared_client_primary: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    with pytest.raises(LogicError, match=err.ZERO_UNITS):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=account.holding_address,
                units=0,
            ),
            params=CommonAppCallParams(sender=shared_primary_dealer.address),
        )


def test_fail_over_distribution(
    contract_case: ContractCase,
    shared_primary_dealer: Any,
    shared_client_primary: Any,
    shared_account_factory: Callable[[Any], DAsaAccount],
) -> None:
    account = shared_account_factory(shared_client_primary)
    state = shared_client_primary.state.global_state

    with pytest.raises(LogicError, match=err.OVER_DISTRIBUTION):
        shared_client_primary.send.primary_distribution(
            contract_case.primary_distribution_args_cls(
                holding_address=account.holding_address,
                units=state.total_units + 1,
            ),
            params=CommonAppCallParams(sender=shared_primary_dealer.address),
        )
