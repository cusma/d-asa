import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    AccountCloseArgs,
    AccountOpenArgs,
    MockAccountingModuleClient,
    SetDefaultStatusArgs,
)
from tests.utils import DAsaAccountManager, DAsaTrustee


def test_pass_close_account(
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

    close_result = accounting_client.send.account_close(
        AccountCloseArgs(holding_address=no_role_account.address),
        params=CommonAppCallParams(sender=account_manager.address),
    ).abi_return
    assert close_result[0] == 0

    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        accounting_client.send.account_close(
            AccountCloseArgs(holding_address=no_role_account.address),
            params=CommonAppCallParams(sender=account_manager.address),
        )


def test_fail_unauthorized_caller(
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

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        accounting_client.send.account_close(
            AccountCloseArgs(holding_address=no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_unauthorized_status(
    no_role_account: SigningAccount,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        accounting_client.send.account_close(
            AccountCloseArgs(holding_address=no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_defaulted_status(
    no_role_account: SigningAccount,
    trustee: DAsaTrustee,
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
    accounting_client.send.set_default_status(
        SetDefaultStatusArgs(defaulted=True),
        params=CommonAppCallParams(sender=trustee.address),
    )

    with pytest.raises(LogicError, match=err.DEFAULTED):
        accounting_client.send.account_close(
            AccountCloseArgs(holding_address=no_role_account.address),
            params=CommonAppCallParams(sender=account_manager.address),
        )


def test_fail_invalid_holding_address(
    no_role_account: SigningAccount,
    account_manager: DAsaAccountManager,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        accounting_client.send.account_close(
            AccountCloseArgs(holding_address=no_role_account.address),
            params=CommonAppCallParams(sender=account_manager.address),
        )


def test_concrete_pass_close_account(
    shared_account_manager,
    shared_account_factory,
    shared_client_active,
) -> None:
    account = shared_account_factory(shared_client_active)
    close_result = shared_client_active.send.account_close(
        (account.holding_address,),
        params=CommonAppCallParams(sender=shared_account_manager.address),
    ).abi_return
    assert close_result[0] == 0

    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        shared_client_active.send.account_close(
            (account.holding_address,),
            params=CommonAppCallParams(sender=shared_account_manager.address),
        )


def test_concrete_fail_unauthorized_caller(
    no_role_account: SigningAccount,
    shared_account_factory,
    shared_client_active,
) -> None:
    account = shared_account_factory(shared_client_active)
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_active.send.account_close(
            (account.holding_address,),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_concrete_fail_defaulted_status(
    shared_trustee,
    shared_account_manager,
    shared_account_factory,
    shared_client_active,
) -> None:
    account = shared_account_factory(shared_client_active)
    shared_client_active.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_active.send.account_close(
            (account.holding_address,),
            params=CommonAppCallParams(sender=shared_account_manager.address),
        )


def test_concrete_fail_invalid_holding_address(
    no_role_account: SigningAccount,
    shared_account_manager,
    shared_client_active,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        shared_client_active.send.account_close(
            (no_role_account.address,),
            params=CommonAppCallParams(sender=shared_account_manager.address),
        )
