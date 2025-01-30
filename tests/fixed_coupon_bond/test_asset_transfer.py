from typing import Callable

import pytest
from algokit_utils import (
    AlgorandClient,
    LogicError,
    OnCompleteCallParameters,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
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
        fixed_coupon_bond_client_primary.get_account_units_current_value(
            holding_address=account_a.holding_address,
            units=transfer_1_units,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ]
            ),
        ).return_value.accrued_interest
    )
    transferred_value_1 = fixed_coupon_bond_client_primary.asset_transfer(
        sender_holding_address=account_a.holding_address,
        receiver_holding_address=account_b.holding_address,
        units=transfer_1_units,
        transaction_parameters=OnCompleteCallParameters(
            signer=account_a.signer,
            boxes=[
                (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                (fixed_coupon_bond_client_primary.app_id, account_b.box_id),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    ).return_value

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
        fixed_coupon_bond_client_primary.get_account_units_current_value(
            holding_address=account_a.holding_address,
            units=transfer_2_units,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ]
            ),
        ).return_value.accrued_interest
    )
    transferred_value_2 = fixed_coupon_bond_client_primary.asset_transfer(
        sender_holding_address=account_a.holding_address,
        receiver_holding_address=account_b.holding_address,
        units=transfer_2_units,
        transaction_parameters=OnCompleteCallParameters(
            signer=account_a.signer,
            boxes=[
                (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                (fixed_coupon_bond_client_primary.app_id, account_b.box_id),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    ).return_value

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
        fixed_coupon_bond_client_primary.get_account_units_current_value(
            holding_address=account_a.holding_address,
            units=transfer_3_units,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ]
            ),
        ).return_value.accrued_interest
    )
    transferred_value_3 = fixed_coupon_bond_client_primary.asset_transfer(
        sender_holding_address=account_a.holding_address,
        receiver_holding_address=account_b.holding_address,
        units=transfer_3_units,
        transaction_parameters=OnCompleteCallParameters(
            signer=account_a.signer,
            boxes=[
                (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                (fixed_coupon_bond_client_primary.app_id, account_b.box_id),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    ).return_value

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
        fixed_coupon_bond_client_primary.asset_transfer(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=1,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_a.signer,
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                    (fixed_coupon_bond_client_primary.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )


# TODO: test_fail_secondary_market_closed


def test_fail_unauthorized(
    oscar: SigningAccount,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        fixed_coupon_bond_client_ongoing.asset_transfer(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=1,
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                    (fixed_coupon_bond_client_ongoing.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )


def test_fail_suspended(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    fixed_coupon_bond_client_suspended: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.SUSPENDED):
        fixed_coupon_bond_client_suspended.asset_transfer(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=1,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_a.signer,
                boxes=[
                    (fixed_coupon_bond_client_suspended.app_id, account_a.box_id),
                    (fixed_coupon_bond_client_suspended.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_suspended.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_suspended.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )


def test_fail_invalid_sender(
    oscar: SigningAccount,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_ongoing.asset_transfer(
            sender_holding_address=oscar.address,
            receiver_holding_address=account_a.holding_address,
            units=1,
            transaction_parameters=OnCompleteCallParameters(
                signer=oscar.signer,
                boxes=[
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        DAsaAccount.box_id_from_address(oscar.address),
                    ),
                    (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )


def test_fail_invalid_receiver(
    oscar: SigningAccount,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_ongoing.asset_transfer(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=oscar.address,
            units=1,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_a.signer,
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        DAsaAccount.box_id_from_address(oscar.address),
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
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
        fixed_coupon_bond_client_ongoing.asset_transfer(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=account_a.units + 1,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_a.signer,
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                    (fixed_coupon_bond_client_ongoing.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )


def test_fail_pending_coupon_payment() -> None:
    pass  # TODO


def test_fail_not_fungible(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: DAsaConfig,
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
    account_with_units_factory: Callable[..., DAsaAccount],
) -> None:
    account_a = account_with_units_factory()
    account_b = account_with_units_factory()

    coupon_1_date = fixed_coupon_bond_cfg.time_events[sc_cfg.ISSUANCE_DATE_IDX + 1]
    time_warp(coupon_1_date)

    fixed_coupon_bond_client_primary.pay_coupon(
        holding_address=account_a.holding_address,
        payment_info=b"",
        transaction_parameters=OnCompleteCallParameters(
            foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
            accounts=[account_a.payment_address],
            boxes=[
                (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_COUPON_RATES),
                (fixed_coupon_bond_client_primary.app_id, sc_cst.BOX_ID_TIME_EVENTS),
            ],
        ),
    )

    with pytest.raises(LogicError, match=err.NON_FUNGIBLE_UNITS):
        fixed_coupon_bond_client_primary.asset_transfer(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=1,
            transaction_parameters=OnCompleteCallParameters(
                signer=account_a.signer,
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account_a.box_id),
                    (fixed_coupon_bond_client_primary.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_primary.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )
