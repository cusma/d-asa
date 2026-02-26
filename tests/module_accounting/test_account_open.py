from typing import Final

import pytest
from algokit_utils import (
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    AccountGetInfoArgs,
    AccountOpenArgs,
    MockAccountingModuleClient,
    RbacGovAssetSuspensionArgs,
)
from tests.utils import DAsaAccountManager, DAsaAuthority

ACCOUNT_TEST_UNITS: Final[int] = 7


def test_pass_account_open(
    no_role_account: SigningAccount,
    accounting_client: MockAccountingModuleClient,
    account_manager: DAsaAccountManager,
) -> None:
    accounting_client.send.account_open(
        AccountOpenArgs(
            holding_address=no_role_account.address,
            payment_address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
        ),
    )

    d_asa_account_info = accounting_client.send.account_get_info(
        AccountGetInfoArgs(
            holding_address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
        ),
    ).abi_return

    assert d_asa_account_info.payment_address == no_role_account.address
    assert d_asa_account_info.units == 0
    assert d_asa_account_info.unit_value == 0
    assert d_asa_account_info.paid_coupons == 0
    assert not d_asa_account_info.suspended


def test_fail_unauthorized_caller(
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
    arranger: SigningAccount,
    no_role_account: SigningAccount,
    authority: DAsaAuthority,
    account_manager: DAsaAccountManager,
    accounting_client: MockAccountingModuleClient,
) -> None:
    accounting_client.send.rbac_gov_asset_suspension(
        RbacGovAssetSuspensionArgs(suspended=True),
        params=CommonAppCallParams(
            sender=authority.address,
        ),
    )
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
    no_role_account: SigningAccount,
    account_manager: DAsaAccountManager,
    accounting_client: MockAccountingModuleClient,
) -> None:
    accounting_client.send.account_open(
        AccountOpenArgs(
            holding_address=no_role_account.address,
            payment_address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address,
        ),
    )

    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        accounting_client.send.account_open(
            AccountOpenArgs(
                holding_address=no_role_account.address,
                payment_address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=account_manager.address,
            ),
        )
