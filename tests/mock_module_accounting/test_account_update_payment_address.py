import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_accounting.mock_accounting_module_client import (
    AccountOpenArgs,
    AccountUpdatePaymentAddressArgs,
    MockAccountingModuleClient,
)
from tests.utils import DAsaAccountManager


def test_pass_account_update_payment_address(
    arranger: SigningAccount,
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

    accounting_client.send.account_update_payment_address(
        AccountUpdatePaymentAddressArgs(
            holding_address=no_role_account.address,
            payment_address=arranger.address,
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )

    account_info = accounting_client.send.account_get_info(
        (no_role_account.address,)
    ).abi_return
    assert account_info.payment_address == arranger.address


def test_fail_invalid_holding_address(
    no_role_account: SigningAccount,
    accounting_client: MockAccountingModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        accounting_client.send.account_update_payment_address(
            AccountUpdatePaymentAddressArgs(
                holding_address=no_role_account.address,
                payment_address=no_role_account.address,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_unauthorized(
    arranger: SigningAccount,
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
        accounting_client.send.account_update_payment_address(
            AccountUpdatePaymentAddressArgs(
                holding_address=no_role_account.address,
                payment_address=arranger.address,
            ),
            params=CommonAppCallParams(sender=arranger.address),
        )


def test_concrete_pass_account_update_payment_address(
    no_role_account: SigningAccount,
    shared_account_factory,
    shared_client_active,
) -> None:
    account = shared_account_factory(shared_client_active)
    shared_client_active.send.account_update_payment_address(
        (account.holding_address, no_role_account.address),
        params=CommonAppCallParams(sender=account.address),
    )
    account_info = shared_client_active.send.account_get_info(
        (account.holding_address,)
    ).abi_return
    assert account_info.payment_address == no_role_account.address


def test_concrete_fail_invalid_holding_address(
    no_role_account: SigningAccount,
    shared_client_active,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        shared_client_active.send.account_update_payment_address(
            (no_role_account.address, no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_concrete_fail_unauthorized(
    no_role_account: SigningAccount,
    shared_account_factory,
    shared_client_active,
) -> None:
    account = shared_account_factory(shared_client_active)
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_active.send.account_update_payment_address(
            (account.holding_address, no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
