from collections.abc import Callable

import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
    AssetTransferArgs,
    GetAccountUnitsCurrentValueArgs,
    ZeroCouponBondClient,
)
from tests.utils import DAsaAccount, DAsaConfig, time_warp


def test_pass_asset_transfer(
    zero_coupon_bond_cfg: DAsaConfig,
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
    account_factory: Callable[..., DAsaAccount],
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account_a = account_with_units_factory(units=3)
    account_b = account_factory(zero_coupon_bond_client_primary)

    asset_info = zero_coupon_bond_client_primary.state.global_state
    maturity_period = asset_info.maturity_date - asset_info.issuance_date

    pre_transfer_units_a = account_a.units
    pre_transfer_units_b = account_b.units
    pre_transfer_unit_value_a = account_a.unit_value
    pre_transfer_unit_value_b = account_b.unit_value

    assert pre_transfer_unit_value_a != pre_transfer_unit_value_b
    assert pre_transfer_unit_value_b == 0

    time_warp(asset_info.issuance_date + maturity_period // 10)

    transfer_1_units = 1
    accrued_interest_1 = (
        zero_coupon_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_1_units,
            )
        ).abi_return.accrued_interest
    )
    transferred_value_1 = zero_coupon_bond_client_primary.send.asset_transfer(
        AssetTransferArgs(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=transfer_1_units,
        ),
        params=CommonAppCallParams(sender=account_a.address),
    ).abi_return

    post_transfer_1_units_a = account_a.units
    post_transfer_1_units_b = account_b.units
    post_transfer_1_unit_value_a = account_a.unit_value
    post_transfer_1_unit_value_b = account_b.unit_value

    assert (
        transferred_value_1
        == zero_coupon_bond_cfg.minimum_denomination * transfer_1_units
        + accrued_interest_1
    )
    assert post_transfer_1_units_a == pre_transfer_units_a - transfer_1_units
    assert post_transfer_1_units_b == pre_transfer_units_b + transfer_1_units
    assert post_transfer_1_unit_value_a == post_transfer_1_unit_value_b
    assert account_a.paid_coupons == account_b.paid_coupons

    time_warp(asset_info.issuance_date + maturity_period // 5)

    transfer_2_units = 1
    accrued_interest_2 = (
        zero_coupon_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_2_units,
            )
        ).abi_return.accrued_interest
    )
    transferred_value_2 = zero_coupon_bond_client_primary.send.asset_transfer(
        AssetTransferArgs(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=transfer_2_units,
        ),
        params=CommonAppCallParams(sender=account_a.address),
    ).abi_return

    post_transfer_2_units_a = account_a.units
    post_transfer_2_units_b = account_b.units
    post_transfer_2_unit_value_a = account_a.unit_value
    post_transfer_2_unit_value_b = account_b.unit_value

    assert (
        transferred_value_2
        == zero_coupon_bond_cfg.minimum_denomination * transfer_2_units
        + accrued_interest_2
    )
    assert post_transfer_2_units_a == post_transfer_1_units_a - transfer_2_units
    assert post_transfer_2_units_b == post_transfer_1_units_b + transfer_2_units
    assert post_transfer_2_unit_value_a == post_transfer_2_unit_value_b
    assert account_a.paid_coupons == account_b.paid_coupons

    time_warp(asset_info.issuance_date + maturity_period // 2)

    transfer_3_units = 1
    accrued_interest_3 = (
        zero_coupon_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_3_units,
            )
        ).abi_return.accrued_interest
    )
    transferred_value_3 = zero_coupon_bond_client_primary.send.asset_transfer(
        AssetTransferArgs(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=transfer_3_units,
        ),
        params=CommonAppCallParams(sender=account_a.address),
    ).abi_return

    post_transfer_3_units_a = account_a.units
    post_transfer_3_units_b = account_b.units
    post_transfer_3_unit_value_a = account_a.unit_value

    assert (
        transferred_value_3
        == zero_coupon_bond_cfg.minimum_denomination * transfer_3_units
        + accrued_interest_3
    )
    assert post_transfer_3_units_a == 0
    assert (
        post_transfer_3_units_b
        == transfer_1_units + transfer_2_units + transfer_3_units
    )
    assert post_transfer_3_unit_value_a == 0
    assert account_a.paid_coupons == 0


def test_fail_secondary_market_not_open_yet(
    zero_coupon_bond_client_primary: ZeroCouponBondClient,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
) -> None:
    with pytest.raises(LogicError, match=err.SECONDARY_MARKET_CLOSED):
        zero_coupon_bond_client_primary.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


# TODO: test_fail_secondary_market_closed


def test_fail_unauthorized(
    oscar: SigningAccount,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        zero_coupon_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=oscar.address),
        )


def test_fail_suspended(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    zero_coupon_bond_client_suspended: ZeroCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.SUSPENDED):
        zero_coupon_bond_client_suspended.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_invalid_sender(
    oscar: SigningAccount,
    account_a: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        zero_coupon_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=oscar.address,
                receiver_holding_address=account_a.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=oscar.address),
        )


def test_fail_invalid_receiver(
    oscar: SigningAccount,
    account_a: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        zero_coupon_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=oscar.address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended_sender() -> None:
    pass  # TODO


def test_fail_suspended_receiver() -> None:
    pass  # TODO


def test_fail_over_transfer(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    zero_coupon_bond_client_ongoing: ZeroCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.OVER_TRANSFER):
        zero_coupon_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=account_a.units + 1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )
