from typing import Any, Final

import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    AccountCloseArgs,
    AccountGetInfoArgs,
    AccountOpenArgs,
    MockAccountingModuleClient,
    RbacGovAssetSuspensionArgs,
    SetDefaultStatusArgs,
)
from tests.utils import DAsaAccountManager, DAsaAuthority, DAsaTrustee

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


def test_fail_unauthorized_status(
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
    accounting_client.send.account_close(
        AccountCloseArgs(holding_address=no_role_account.address),
        params=CommonAppCallParams(sender=account_manager.address),
    )
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        accounting_client.send.account_open(
            AccountOpenArgs(
                holding_address=no_role_account.address,
                payment_address=no_role_account.address,
            ),
            params=CommonAppCallParams(sender=account_manager.address),
        )


def test_fail_defaulted_status(
    no_role_account: SigningAccount,
    trustee: DAsaTrustee,
    account_manager: DAsaAccountManager,
    accounting_client: MockAccountingModuleClient,
) -> None:
    accounting_client.send.set_default_status(
        SetDefaultStatusArgs(defaulted=True),
        params=CommonAppCallParams(sender=trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        accounting_client.send.account_open(
            AccountOpenArgs(
                holding_address=no_role_account.address,
                payment_address=no_role_account.address,
            ),
            params=CommonAppCallParams(sender=account_manager.address),
        )


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


def test_concrete_pass_account_open(
    algorand: AlgorandClient,
    shared_account_manager,
    shared_client_active: Any,
) -> None:
    account = algorand.account.random()
    shared_client_active.send.account_open(
        (account.address, account.address),
        params=CommonAppCallParams(sender=shared_account_manager.address),
    )
    account_info = shared_client_active.send.account_get_info(
        (account.address,)
    ).abi_return
    assert account_info.payment_address == account.address
    assert account_info.units == 0
    assert account_info.unit_value == 0
    assert account_info.paid_coupons == 0
    assert not account_info.suspended


def test_concrete_fail_unauthorized(
    algorand: AlgorandClient,
    no_role_account: SigningAccount,
    shared_client_active: Any,
) -> None:
    account = algorand.account.random()
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_active.send.account_open(
            (account.address, account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_concrete_fail_defaulted_status(
    algorand: AlgorandClient,
    shared_account_manager,
    shared_trustee,
    shared_client_active: Any,
) -> None:
    account = algorand.account.random()
    shared_client_active.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_active.send.account_open(
            (account.address, account.address),
            params=CommonAppCallParams(sender=shared_account_manager.address),
        )


def test_concrete_fail_suspended(
    algorand: AlgorandClient,
    shared_authority,
    shared_account_manager,
    shared_client_active: Any,
) -> None:
    account = algorand.account.random()
    shared_client_active.send.rbac_gov_asset_suspension(
        (True,),
        params=CommonAppCallParams(sender=shared_authority.address),
    )
    with pytest.raises(LogicError, match=err.SUSPENDED):
        shared_client_active.send.account_open(
            (account.address, account.address),
            params=CommonAppCallParams(sender=shared_account_manager.address),
        )


def test_concrete_fail_invalid_holding_address(
    shared_account_manager,
    shared_account_factory,
    shared_client_active: Any,
) -> None:
    account = shared_account_factory(shared_client_active)
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        shared_client_active.send.account_open(
            (account.holding_address, account.holding_address),
            params=CommonAppCallParams(sender=shared_account_manager.address),
        )
