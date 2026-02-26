from typing import Final

import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    AccountGetInfoArgs,
    AccountOpenArgs,
    MockAccountingModuleClient,
)
from tests.utils import DAsaAccount, DAsaAccountManager

ACCOUNT_TEST_UNITS: Final[int] = 7


def test_pass_account_open(
    algorand: AlgorandClient,
    accounting_client: MockAccountingModuleClient,
    account_manager: DAsaAccountManager,
) -> None:
    holding = algorand.account.random()
    payment = algorand.account.random()

    accounting_client.send.account_open(
        AccountOpenArgs(
            holding_address=holding.address,
            payment_address=payment.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
        ),
    )

    d_asa_account_info = accounting_client.send.account_get_info(
        AccountGetInfoArgs(
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
    no_role_account: SigningAccount,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        accounting_client.send.account_open(
            AccountOpenArgs(
                holding_address=no_role_account.address,
                payment_address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=no_role_account.address,
            ),
        )


def test_fail_unauthorized_status() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended(
    algorand: AlgorandClient,
    no_role_account: SigningAccount,
    account_manager: DAsaAccountManager,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.SUSPENDED):
        accounting_client.send.account_open(
            AccountOpenArgs(
                holding_address=no_role_account.address,
                payment_address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=account_manager.address,
            ),
        )


def test_fail_invalid_holding_address(
    account_manager: DAsaAccountManager,
    account_a: DAsaAccount,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        accounting_client.send.account_open(
            AccountOpenArgs(
                holding_address=account_a.holding_address,
                payment_address=account_a.payment_address,
            ),
            params=CommonAppCallParams(
                sender=account_manager.address,
            ),
        )
