from collections.abc import Callable
from typing import Any

import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    PayPrincipalArgs,
)
from tests.utils import DAsaAccount, time_warp

from .cases import ContractCase


def test_pass_set_secondary_time_events(
    contract_case: ContractCase,
    shared_client_active: Any,
) -> None:
    state = shared_client_active.state.global_state
    secondary_market_time_events = contract_case.secondary_market_time_events(state)
    expected_schedule = shared_client_active.send.set_secondary_time_events(
        contract_case.set_secondary_time_events_args_cls(
            secondary_market_time_events=secondary_market_time_events,
        )
    ).abi_return

    state = shared_client_active.state.global_state
    assert state.secondary_market_opening_date == secondary_market_time_events[0]
    assert (
        expected_schedule.secondary_market_opening_date
        == secondary_market_time_events[0]
    )

    if contract_case.capabilities.has_maturity:
        assert state.secondary_market_closure_date == secondary_market_time_events[1]
        assert (
            expected_schedule.secondary_market_closure_date
            == secondary_market_time_events[1]
        )
    else:
        assert state.secondary_market_closure_date == 0
        assert expected_schedule.secondary_market_closure_date == 0


def test_fail_unauthorized_caller(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_client_active: Any,
) -> None:
    state = shared_client_active.state.global_state
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_active.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=contract_case.secondary_market_time_events(
                    state
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_unauthorized_status_ended(
    contract_case: ContractCase,
    shared_client_primary: Any,
    shared_account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    if contract_case.name != "zero_coupon_bond":
        pytest.skip("ended status scenario is stable only on zero coupon flow")

    account = shared_account_with_units_factory(units=1)
    state = shared_client_primary.state.global_state
    time_warp(state.maturity_date)
    shared_client_primary.send.pay_principal(
        PayPrincipalArgs(holding_address=account.holding_address, payment_info=b"")
    )

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_primary.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=contract_case.secondary_market_time_events(
                    state
                )
            )
        )


def test_fail_defaulted_status(
    contract_case: ContractCase,
    shared_client_active: Any,
    shared_trustee: Any,
) -> None:
    state = shared_client_active.state.global_state
    shared_client_active.send.set_default_status(
        contract_case.set_default_status_args_cls(defaulted=True),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )

    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_active.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=contract_case.secondary_market_time_events(
                    state
                )
            )
        )


def test_fail_invalid_time_events_length(
    contract_case: ContractCase,
    shared_client_active: Any,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        shared_client_active.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=[]
            )
        )


def test_fail_invalid_sorting(
    contract_case: ContractCase,
    shared_client_active: Any,
) -> None:
    state = shared_client_active.state.global_state
    invalid_schedule = [state.issuance_date + 2 * sc_cst.DAY_2_SEC, state.issuance_date]
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        shared_client_active.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=invalid_schedule,
            )
        )


def test_fail_invalid_secondary_opening_date(
    contract_case: ContractCase,
    shared_client_active: Any,
) -> None:
    state = shared_client_active.state.global_state
    with pytest.raises(LogicError, match=err.INVALID_SECONDARY_OPENING_DATE):
        shared_client_active.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=(
                    [
                        state.issuance_date - sc_cst.DAY_2_SEC,
                        state.maturity_date,
                    ]
                    if contract_case.capabilities.has_maturity
                    else [state.issuance_date - sc_cst.DAY_2_SEC]
                ),
            )
        )


def test_fail_invalid_secondary_closure_date(
    contract_case: ContractCase,
    shared_client_active: Any,
) -> None:
    if not contract_case.capabilities.has_maturity:
        pytest.skip("perpetual contract has no maturity closure")

    state = shared_client_active.state.global_state
    with pytest.raises(LogicError, match=err.INVALID_SECONDARY_CLOSURE_DATE):
        shared_client_active.send.set_secondary_time_events(
            contract_case.set_secondary_time_events_args_cls(
                secondary_market_time_events=[
                    state.issuance_date,
                    state.maturity_date + sc_cst.DAY_2_SEC,
                ]
            )
        )
