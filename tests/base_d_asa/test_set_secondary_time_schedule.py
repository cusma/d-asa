import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    BaseDAsaClient,
    SetSecondaryTimeEventsArgs,
)


def test_pass_set_secondary_time_events(
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    state = base_d_asa_client_active.state.global_state
    expected_schedule = base_d_asa_client_active.send.set_secondary_time_events(
        SetSecondaryTimeEventsArgs(
            secondary_market_time_events=[state.issuance_date, state.maturity_date]
        ),
    ).abi_return

    state = base_d_asa_client_active.state.global_state
    assert (
        state.secondary_market_opening_date
        == state.issuance_date
        == expected_schedule.secondary_market_opening_date
    )
    assert (
        state.secondary_market_closure_date
        == state.maturity_date
        == expected_schedule.secondary_market_closure_date
    )


def test_fail_unauthorized_caller(
    oscar: SigningAccount, base_d_asa_client_active: BaseDAsaClient
) -> None:
    state = base_d_asa_client_active.state.global_state
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_active.send.set_secondary_time_events(
            SetSecondaryTimeEventsArgs(
                secondary_market_time_events=[state.issuance_date, state.maturity_date]
            ),
            params=CommonAppCallParams(
                sender=oscar.address,
            ),
        )


def test_fail_unauthorized_status() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_invalid_time_events_length(
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_TIME_EVENTS_LENGTH):
        base_d_asa_client_active.send.set_secondary_time_events(
            SetSecondaryTimeEventsArgs(secondary_market_time_events=[]),
        )


def test_fail_invalid_sorting(base_d_asa_client_active: BaseDAsaClient) -> None:
    state = base_d_asa_client_active.state.global_state
    with pytest.raises(LogicError, match=err.INVALID_SORTING):
        base_d_asa_client_active.send.set_secondary_time_events(
            SetSecondaryTimeEventsArgs(
                secondary_market_time_events=[state.maturity_date, state.issuance_date]
            ),
        )


# TODO: Test INVALID_TIME_PERIOD for Actual/Actual convention


def test_invalid_secondary_opening_date(
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    state = base_d_asa_client_active.state.global_state
    with pytest.raises(LogicError, match=err.INVALID_SECONDARY_OPENING_DATE):
        base_d_asa_client_active.send.set_secondary_time_events(
            SetSecondaryTimeEventsArgs(
                secondary_market_time_events=[
                    state.issuance_date - 1 * sc_cst.DAY_2_SEC,
                    state.maturity_date,
                ]
            ),
        )


def test_invalid_secondary_closure_date(
    base_d_asa_client_active: BaseDAsaClient,
) -> None:
    state = base_d_asa_client_active.state.global_state
    with pytest.raises(LogicError, match=err.INVALID_SECONDARY_CLOSURE_DATE):
        base_d_asa_client_active.send.set_secondary_time_events(
            SetSecondaryTimeEventsArgs(
                secondary_market_time_events=[
                    state.issuance_date,
                    state.maturity_date + 1 * sc_cst.DAY_2_SEC,
                ]
            ),
        )
