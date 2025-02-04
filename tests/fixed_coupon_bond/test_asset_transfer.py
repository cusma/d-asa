from typing import Callable

import pytest
from algokit_utils import (
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AssetTransferArgs,
    FixedCouponBondClient,
    GetAccountUnitsCurrentValueArgs,
    PayCouponArgs,
)
from smart_contracts.base_d_asa import config as sc_cfg
from tests.utils import DAsaAccount, DAsaConfig, time_warp


def test_pass_asset_transfer(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_factory: Callable[..., DAsaAccount],
    account_with_coupons_factory: Callable[..., DAsaAccount],
) -> None:
    paid_coupons = 1
    account_a = account_with_coupons_factory(units=3, coupons=paid_coupons)
    account_b = account_factory(fixed_coupon_bond_client_primary)

    coupon_1_date = fixed_coupon_bond_cfg.time_events[
        sc_cfg.ISSUANCE_DATE_IDX + paid_coupons
    ]
    coupon_2_date = fixed_coupon_bond_cfg.time_events[
        sc_cfg.ISSUANCE_DATE_IDX + paid_coupons + 1
    ]
    coupon_period = coupon_2_date - coupon_1_date

    pre_transfer_units_a = account_a.units
    pre_transfer_units_b = account_b.units
    pre_transfer_unit_value_a = account_a.unit_value
    pre_transfer_unit_value_b = account_b.unit_value

    assert pre_transfer_unit_value_a != pre_transfer_unit_value_b
    assert pre_transfer_unit_value_b == 0
    assert account_a.paid_coupons != account_b.paid_coupons

    time_warp(coupon_1_date + coupon_period // 10)

    transfer_1_units = 1
    accrued_interest_1 = (
        fixed_coupon_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_1_units,
            )
        ).abi_return.accrued_interest
    )
    transferred_value_1 = fixed_coupon_bond_client_primary.send.asset_transfer(
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
        == fixed_coupon_bond_cfg.minimum_denomination * transfer_1_units
        + accrued_interest_1
    )
    assert post_transfer_1_units_a == pre_transfer_units_a - transfer_1_units
    assert post_transfer_1_units_b == pre_transfer_units_b + transfer_1_units
    assert post_transfer_1_unit_value_a == post_transfer_1_unit_value_b
    assert account_a.paid_coupons == account_b.paid_coupons

    time_warp(coupon_1_date + coupon_period // 5)

    transfer_2_units = 1
    accrued_interest_2 = (
        fixed_coupon_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_2_units,
            ),
        ).abi_return.accrued_interest
    )
    transferred_value_2 = fixed_coupon_bond_client_primary.send.asset_transfer(
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
        == fixed_coupon_bond_cfg.minimum_denomination * transfer_2_units
        + accrued_interest_2
    )
    assert post_transfer_2_units_a == post_transfer_1_units_a - transfer_2_units
    assert post_transfer_2_units_b == post_transfer_1_units_b + transfer_2_units
    assert post_transfer_2_unit_value_a == post_transfer_2_unit_value_b
    assert account_a.paid_coupons == account_b.paid_coupons

    time_warp(coupon_1_date + coupon_period // 2)

    transfer_3_units = 1
    accrued_interest_3 = (
        fixed_coupon_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_3_units,
            )
        ).abi_return.accrued_interest
    )
    transferred_value_3 = fixed_coupon_bond_client_primary.send.asset_transfer(
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
        == fixed_coupon_bond_cfg.minimum_denomination * transfer_3_units
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
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
) -> None:
    with pytest.raises(LogicError, match=err.SECONDARY_MARKET_CLOSED):
        fixed_coupon_bond_client_primary.send.asset_transfer(
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
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        fixed_coupon_bond_client_ongoing.send.asset_transfer(
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
    fixed_coupon_bond_client_suspended: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.SUSPENDED):
        fixed_coupon_bond_client_suspended.send.asset_transfer(
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
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_ongoing.send.asset_transfer(
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
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_ongoing.send.asset_transfer(
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
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.OVER_TRANSFER):
        fixed_coupon_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=account_a.units + 1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_pending_coupon_payment() -> None:
    pass  # TODO


def test_fail_not_fungible(
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account_a = account_with_units_factory()
    account_b = account_with_units_factory()

    coupon_1_date = fixed_coupon_bond_cfg.time_events[sc_cfg.ISSUANCE_DATE_IDX + 1]
    time_warp(coupon_1_date)

    fixed_coupon_bond_client_primary.send.pay_coupon(
        PayCouponArgs(
            holding_address=account_a.holding_address,
            payment_info=b"",
        )
    )

    with pytest.raises(LogicError, match=err.NON_FUNGIBLE_UNITS):
        fixed_coupon_bond_client_primary.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )
