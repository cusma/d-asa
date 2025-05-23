from typing import Final

import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
    BaseDAsaClient,
    GetAccountInfoArgs,
    OpenAccountArgs,
)
from tests.utils import DAsaAccount, DAsaAccountManager

ACCOUNT_TEST_UNITS: Final[int] = 7


def test_pass_open_account(
    algorand: AlgorandClient,
    base_d_asa_client_empty: BaseDAsaClient,
    account_manager: DAsaAccountManager,
) -> None:
    holding = algorand.account.random()
    payment = algorand.account.random()

    base_d_asa_client_empty.send.open_account(
        OpenAccountArgs(
            holding_address=holding.address,
            payment_address=payment.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
        ),
    )

    d_asa_account_info = base_d_asa_client_empty.send.get_account_info(
        GetAccountInfoArgs(
            holding_address=holding.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
        ),
    ).abi_return

    assert d_asa_account_info.payment_address == payment.address
    assert d_asa_account_info.units == 0
    assert d_asa_account_info.unit_value == 0
    assert d_asa_account_info.paid_coupons == 0
    assert not d_asa_account_info.suspended


def test_fail_unauthorized_caller(
    algorand: AlgorandClient,
    oscar: SigningAccount,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    holding = algorand.account.random()
    payment = algorand.account.random()

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_empty.send.open_account(
            OpenAccountArgs(
                holding_address=holding.address,
                payment_address=payment.address,
            ),
            params=CommonAppCallParams(
                sender=oscar.address,
            ),
        )


def test_fail_unauthorized_status() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended(
    algorand: AlgorandClient,
    account_manager: DAsaAccountManager,
    base_d_asa_client_suspended: BaseDAsaClient,
) -> None:
    holding = algorand.account.random()
    payment = algorand.account.random()

    with pytest.raises(LogicError, match=err.SUSPENDED):
        base_d_asa_client_suspended.send.open_account(
            OpenAccountArgs(
                holding_address=holding.address,
                payment_address=payment.address,
            ),
            params=CommonAppCallParams(
                sender=account_manager.address,
            ),
        )


def test_fail_invalid_holding_address(
    base_d_asa_client_empty: BaseDAsaClient,
    account_manager: DAsaAccountManager,
    account_a: DAsaAccount,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        base_d_asa_client_empty.send.open_account(
            OpenAccountArgs(
                holding_address=account_a.holding_address,
                payment_address=account_a.payment_address,
            ),
            params=CommonAppCallParams(
                sender=account_manager.address,
            ),
        )
