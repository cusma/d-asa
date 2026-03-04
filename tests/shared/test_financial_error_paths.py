from typing import Any

import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from tests import utils
from tests.utils import time_warp

from .cases import ContractCase


def test_fail_get_account_units_current_value_no_primary_distribution(
    no_role_account: SigningAccount,
    shared_client_active: Any,
) -> None:
    with pytest.raises(LogicError, match=err.NO_PRIMARY_DISTRIBUTION):
        shared_client_active.send.get_account_units_current_value(
            (no_role_account.address, 1)
        )


def test_fail_get_account_units_current_value_invalid_holding_address(
    no_role_account: SigningAccount,
    shared_client_primary: Any,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        shared_client_primary.send.get_account_units_current_value(
            (no_role_account.address, 1)
        )


def test_fail_get_account_units_current_value_invalid_units(
    shared_account_a: utils.DAsaAccount,
    shared_client_primary: Any,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_UNITS):
        shared_client_primary.send.get_account_units_current_value(
            (shared_account_a.holding_address, shared_account_a.units + 1)
        )


def test_fail_get_account_units_current_value_pending_coupon_payment(
    contract_case: ContractCase,
    shared_account_a: utils.DAsaAccount,
    shared_account_b: utils.DAsaAccount,
    shared_client_ongoing: Any,
) -> None:
    if not contract_case.capabilities.has_coupon:
        pytest.skip("contract has no coupons")

    next_coupon_due_date = (
        shared_client_ongoing.send.get_coupons_status().abi_return.next_coupon_due_date
    )
    time_warp(next_coupon_due_date)
    shared_client_ongoing.send.pay_coupon((shared_account_a.holding_address, b""))

    with pytest.raises(LogicError, match=err.PENDING_COUPON_PAYMENT):
        shared_client_ongoing.send.get_account_units_current_value(
            (shared_account_b.holding_address, 1)
        )


def test_fail_pay_principal_unauthorized_status(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_client_empty: Any,
) -> None:
    if not contract_case.capabilities.has_principal:
        pytest.skip("contract has no principal payments")

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_empty.send.pay_principal((no_role_account.address, b""))


def test_fail_pay_principal_defaulted(
    contract_case: ContractCase,
    shared_account_a: utils.DAsaAccount,
    shared_trustee: utils.DAsaTrustee,
    shared_client_ongoing: Any,
) -> None:
    if not contract_case.capabilities.has_principal:
        pytest.skip("contract has no principal payments")

    shared_client_ongoing.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_ongoing.send.pay_principal(
            (shared_account_a.holding_address, b"")
        )


def test_fail_pay_principal_suspended(
    contract_case: ContractCase,
    shared_account_a: utils.DAsaAccount,
    shared_authority: utils.DAsaAuthority,
    shared_client_ongoing: Any,
) -> None:
    if not contract_case.capabilities.has_principal:
        pytest.skip("contract has no principal payments")

    shared_client_ongoing.send.rbac_gov_asset_suspension(
        (True,),
        params=CommonAppCallParams(sender=shared_authority.address),
    )
    with pytest.raises(LogicError, match=err.SUSPENDED):
        shared_client_ongoing.send.pay_principal(
            (shared_account_a.holding_address, b"")
        )


def test_fail_pay_coupon_unauthorized_status(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_client_empty: Any,
) -> None:
    if not contract_case.capabilities.has_coupon:
        pytest.skip("contract has no coupon payments")

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_empty.send.pay_coupon((no_role_account.address, b""))


def test_fail_pay_coupon_defaulted(
    contract_case: ContractCase,
    shared_account_a: utils.DAsaAccount,
    shared_trustee: utils.DAsaTrustee,
    shared_client_ongoing: Any,
) -> None:
    if not contract_case.capabilities.has_coupon:
        pytest.skip("contract has no coupon payments")

    shared_client_ongoing.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_ongoing.send.pay_coupon((shared_account_a.holding_address, b""))


def test_fail_pay_coupon_suspended(
    contract_case: ContractCase,
    shared_account_a: utils.DAsaAccount,
    shared_authority: utils.DAsaAuthority,
    shared_client_ongoing: Any,
) -> None:
    if not contract_case.capabilities.has_coupon:
        pytest.skip("contract has no coupon payments")

    shared_client_ongoing.send.rbac_gov_asset_suspension(
        (True,),
        params=CommonAppCallParams(sender=shared_authority.address),
    )
    with pytest.raises(LogicError, match=err.SUSPENDED):
        shared_client_ongoing.send.pay_coupon((shared_account_a.holding_address, b""))


def test_fail_update_interest_rate_defaulted(
    contract_case: ContractCase,
    shared_interest_oracle: utils.DAsaInterestOracle,
    shared_trustee: utils.DAsaTrustee,
    shared_client_ongoing: Any,
) -> None:
    if contract_case.name != "perpetual_bond":
        pytest.skip("only perpetual supports interest rate updates")

    shared_client_ongoing.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    with pytest.raises(LogicError, match=err.DEFAULTED):
        shared_client_ongoing.send.update_interest_rate(
            (shared_client_ongoing.state.global_state.interest_rate + 1,),
            params=CommonAppCallParams(sender=shared_interest_oracle.address),
        )


def test_fail_update_interest_rate_suspended(
    contract_case: ContractCase,
    shared_interest_oracle: utils.DAsaInterestOracle,
    shared_authority: utils.DAsaAuthority,
    shared_client_ongoing: Any,
) -> None:
    if contract_case.name != "perpetual_bond":
        pytest.skip("only perpetual supports interest rate updates")

    shared_client_ongoing.send.rbac_gov_asset_suspension(
        (True,),
        params=CommonAppCallParams(sender=shared_authority.address),
    )
    with pytest.raises(LogicError, match=err.SUSPENDED):
        shared_client_ongoing.send.update_interest_rate(
            (shared_client_ongoing.state.global_state.interest_rate + 1,),
            params=CommonAppCallParams(sender=shared_interest_oracle.address),
        )
