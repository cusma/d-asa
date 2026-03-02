import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    AccountGetInfoArgs,
    AccountOpenArgs,
    MockAccountingModuleClient,
)
from tests.utils import DAsaAccountManager


def test_pass_account_get_info(
    no_role_account: SigningAccount,
    account_manager: DAsaAccountManager,
    accounting_client: MockAccountingModuleClient,
) -> None:
    accounting_client.send.account_open(
        AccountOpenArgs(
            holding_address=no_role_account.address,
            payment_address=no_role_account.address,
        ),
        params=CommonAppCallParams(sender=account_manager.address),
    )

    account_info = accounting_client.send.account_get_info(
        AccountGetInfoArgs(holding_address=no_role_account.address)
    ).abi_return
    assert account_info.payment_address == no_role_account.address
    assert account_info.units == 0
    assert account_info.unit_value == 0
    assert account_info.paid_coupons == 0
    assert not account_info.suspended


def test_fail_invalid_holding_address(
    no_role_account: SigningAccount,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        accounting_client.send.account_get_info(
            AccountGetInfoArgs(holding_address=no_role_account.address)
        )
