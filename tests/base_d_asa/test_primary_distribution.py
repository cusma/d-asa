from typing import Callable, Final

import pytest
from algokit_utils import (
    AlgorandClient,
    LogicError,
    OnCompleteCallParameters,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from tests.utils import (
    DAsaAccount,
    DAsaAuthority,
    DAsaPrimaryDealer,
    get_latest_timestamp,
    time_warp,
)

ACCOUNT_TEST_UNITS: Final[int] = 7


def test_pass_primary_distribution(
    primary_dealer: DAsaPrimaryDealer,
    base_d_asa_client_primary: BaseDAsaClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(base_d_asa_client_primary)
    state = base_d_asa_client_primary.get_global_state()
    assert state.circulating_units == 0

    remaining_units = base_d_asa_client_primary.primary_distribution(
        holding_address=account.holding_address,
        units=ACCOUNT_TEST_UNITS,
        transaction_parameters=OnCompleteCallParameters(
            signer=primary_dealer.signer,
            boxes=[
                (base_d_asa_client_primary.app_id, primary_dealer.box_id),
                (base_d_asa_client_primary.app_id, account.box_id),
            ],
        ),
    ).return_value

    state = base_d_asa_client_primary.get_global_state()
    assert state.circulating_units == ACCOUNT_TEST_UNITS
    assert remaining_units == state.total_units - state.circulating_units
    # TODO: assert not state.paid_coupon_units
    assert account.payment_address == account.holding_address
    assert account.units == ACCOUNT_TEST_UNITS
    assert account.paid_coupons == 0

    remaining_units = base_d_asa_client_primary.primary_distribution(
        holding_address=account.holding_address,
        units=ACCOUNT_TEST_UNITS,
        transaction_parameters=OnCompleteCallParameters(
            signer=primary_dealer.signer,
            boxes=[
                (base_d_asa_client_primary.app_id, primary_dealer.box_id),
                (base_d_asa_client_primary.app_id, account.box_id),
            ],
        ),
    ).return_value

    state = base_d_asa_client_primary.get_global_state()
    assert state.circulating_units == 2 * ACCOUNT_TEST_UNITS
    assert remaining_units == state.total_units - state.circulating_units
    # TODO: assert not state.paid_coupon_units
    assert account.payment_address == account.holding_address
    assert account.units == 2 * ACCOUNT_TEST_UNITS
    assert account.paid_coupons == 0


def test_fail_primary_distribution_closed(
    algorand: AlgorandClient,
    base_d_asa_client_primary: BaseDAsaClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(base_d_asa_client_primary)
    state = base_d_asa_client_primary.get_global_state()
    time_warp(state.primary_distribution_closure_date)
    assert (
        get_latest_timestamp(algorand.client.algod)
        >= state.primary_distribution_closure_date
    )

    with pytest.raises(LogicError, match=err.PRIMARY_DISTRIBUTION_CLOSED):
        base_d_asa_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=ACCOUNT_TEST_UNITS,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[(base_d_asa_client_primary.app_id, account.box_id)]
            ),
        )


def test_fail_unauthorized(
    oscar: SigningAccount,
    base_d_asa_client_primary: BaseDAsaClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(base_d_asa_client_primary)
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=ACCOUNT_TEST_UNITS,
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                boxes=[
                    (
                        base_d_asa_client_primary.app_id,
                        DAsaPrimaryDealer.box_id_from_address(oscar.address),
                    ),
                    (base_d_asa_client_primary.app_id, account.box_id),
                ],
            ),
        )


def test_fail_invalid_holding_address() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended(
    authority: DAsaAuthority,
    primary_dealer: DAsaPrimaryDealer,
    base_d_asa_client_primary: BaseDAsaClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(base_d_asa_client_primary)
    base_d_asa_client_primary.set_asset_suspension(
        suspended=True,
        transaction_parameters=OnCompleteCallParameters(
            signer=authority.signer,
            boxes=[(base_d_asa_client_primary.app_id, authority.box_id)],
        ),
    )
    with pytest.raises(LogicError, match=err.SUSPENDED):
        base_d_asa_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=ACCOUNT_TEST_UNITS,
            transaction_parameters=OnCompleteCallParameters(
                signer=primary_dealer.signer,
                boxes=[
                    (base_d_asa_client_primary.app_id, primary_dealer.box_id),
                    (base_d_asa_client_primary.app_id, account.box_id),
                ],
            ),
        )


def test_fail_zero_units(
    primary_dealer: DAsaPrimaryDealer,
    base_d_asa_client_primary: BaseDAsaClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(base_d_asa_client_primary)
    with pytest.raises(LogicError, match=err.ZERO_UNITS):
        base_d_asa_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=0,
            transaction_parameters=OnCompleteCallParameters(
                signer=primary_dealer.signer,
                boxes=[
                    (base_d_asa_client_primary.app_id, primary_dealer.box_id),
                    (base_d_asa_client_primary.app_id, account.box_id),
                ],
            ),
        )


def test_fail_over_distribution(
    primary_dealer: DAsaPrimaryDealer,
    base_d_asa_client_primary: BaseDAsaClient,
    account_factory: Callable[..., DAsaAccount],
) -> None:
    account = account_factory(base_d_asa_client_primary)
    state = base_d_asa_client_primary.get_global_state()

    with pytest.raises(LogicError, match=err.OVER_DISTRIBUTION):
        base_d_asa_client_primary.primary_distribution(
            holding_address=account.holding_address,
            units=state.total_units + 1,
            transaction_parameters=OnCompleteCallParameters(
                signer=primary_dealer.signer,
                boxes=[
                    (base_d_asa_client_primary.app_id, primary_dealer.box_id),
                    (base_d_asa_client_primary.app_id, account.box_id),
                ],
            ),
        )
