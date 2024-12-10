from typing import Final

import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from tests.utils import DAsaAccount, DAsaAccountManager

ACCOUNT_TEST_UNITS: Final[int] = 7


def test_pass_open_account(
    algorand_client: AlgorandClient,
    base_d_asa_client_empty: BaseDAsaClient,
    account_manager: DAsaAccountManager,
) -> None:
    holding = algorand_client.account.random()
    payment = algorand_client.account.random()

    base_d_asa_client_empty.open_account(
        holding_address=holding.address,
        payment_address=payment.address,
        transaction_parameters=OnCompleteCallParameters(
            signer=account_manager.signer,
            boxes=[
                (base_d_asa_client_empty.app_id, account_manager.box_id),
                (
                    base_d_asa_client_empty.app_id,
                    DAsaAccount.box_id_from_address(holding.address),
                ),
            ],
        ),
    )

    d_asa_account_info = base_d_asa_client_empty.get_account_info(
        holding_address=holding.address,
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (
                    base_d_asa_client_empty.app_id,
                    DAsaAccount.box_id_from_address(holding.address),
                )
            ]
        ),
    ).return_value

    assert d_asa_account_info.payment_address == payment.address
    assert d_asa_account_info.units == 0
    assert d_asa_account_info.unit_value == 0
    assert d_asa_account_info.paid_coupons == 0
    assert not d_asa_account_info.suspended


def test_fail_unauthorized_caller(
    algorand_client: AlgorandClient,
    oscar: AddressAndSigner,
    base_d_asa_client_empty: BaseDAsaClient,
) -> None:
    holding = algorand_client.account.random()
    payment = algorand_client.account.random()

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_empty.open_account(
            holding_address=holding.address,
            payment_address=payment.address,
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                boxes=[
                    (
                        base_d_asa_client_empty.app_id,
                        DAsaAccountManager.box_id_from_address(oscar.address),
                    ),
                    (
                        base_d_asa_client_empty.app_id,
                        DAsaAccount.box_id_from_address(holding.address),
                    ),
                ],
            ),
        )


def test_fail_unauthorized_status() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended(
    algorand_client: AlgorandClient,
    account_manager: DAsaAccountManager,
    base_d_asa_client_suspended: BaseDAsaClient,
) -> None:
    holding = algorand_client.account.random()
    payment = algorand_client.account.random()

    with pytest.raises(LogicError, match=err.SUSPENDED):
        base_d_asa_client_suspended.open_account(
            holding_address=holding.address,
            payment_address=payment.address,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_manager.signer,
                boxes=[
                    (base_d_asa_client_suspended.app_id, account_manager.box_id),
                    (
                        base_d_asa_client_suspended.app_id,
                        DAsaAccount.box_id_from_address(holding.address),
                    ),
                ],
            ),
        )


def test_fail_invalid_holding_address(
    base_d_asa_client_empty: BaseDAsaClient,
    account_manager: DAsaAccountManager,
    account_a: DAsaAccount,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        base_d_asa_client_empty.open_account(
            holding_address=account_a.holding_address,
            payment_address=account_a.payment_address,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_manager.signer,
                boxes=[
                    (base_d_asa_client_empty.app_id, account_manager.box_id),
                    (base_d_asa_client_empty.app_id, account_a.box_id),
                ],
            ),
        )
