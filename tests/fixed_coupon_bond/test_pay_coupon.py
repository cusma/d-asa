from typing import Callable

import pytest
from algokit_utils import (
    AlgorandClient,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from smart_contracts import errors as err
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    FixedCouponBondClient,
)
from smart_contracts.fixed_coupon_bond import config as sc_cfg
from tests.utils import Currency, DAsaAccount, DAsaConfig, time_warp


def test_pass_pay_coupon(
    algorand: AlgorandClient,
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    account_a_units = account_a.units
    account_b_units = account_b.units

    time_events = fixed_coupon_bond_client_ongoing.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        print(f"Coupon {coupon} of {fixed_coupon_bond_cfg.total_coupons}")
        due_coupons = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            )
        ).return_value.due_coupons
        assert due_coupons == coupon - 1

        # Pre payment sate
        pre_payment_account_a_paid_coupons = account_a.paid_coupons
        pre_payment_account_b_paid_coupons = account_a.paid_coupons
        pre_payment_state = fixed_coupon_bond_client_ongoing.get_global_state()
        assert pre_payment_account_a_paid_coupons == due_coupons
        assert pre_payment_account_b_paid_coupons == due_coupons
        assert (
            pre_payment_state.paid_coupon_units
            == account_a_units * pre_payment_account_a_paid_coupons
            + account_b_units * pre_payment_account_b_paid_coupons
        )

        account_a_coupon_amount = fixed_coupon_bond_client_ongoing.get_payment_amount(
            holding_address=account_a.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ]
            ),
        ).return_value.interest

        account_b_coupon_amount = fixed_coupon_bond_client_ongoing.get_payment_amount(
            holding_address=account_b.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, account_b.box_id),
                    (
                        fixed_coupon_bond_client_ongoing.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ]
            ),
        ).return_value.interest

        # Coupon reaches due date
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date)
        due_coupons = fixed_coupon_bond_client_ongoing.get_coupons_status(
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)
                ],
            )
        ).return_value.due_coupons
        assert due_coupons == coupon

        # Coupon payment
        payment_a = fixed_coupon_bond_client_ongoing.pay_coupon(
            holding_address=account_a.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account_a.payment_address],
                boxes=[
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
        ).return_value
        assert payment_a.amount == account_a_coupon_amount
        print("Account A:")
        print(
            f"Paid amount: {payment_a.amount * currency.asa_to_unit:.2f} EUR, Due date: {coupon_due_date}, "
            f"Payment timestamp: {payment_a.timestamp}"
        )

        payment_b = fixed_coupon_bond_client_ongoing.pay_coupon(
            holding_address=account_b.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account_b.payment_address],
                boxes=[
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
        ).return_value
        assert payment_b.amount == account_b_coupon_amount
        print("Account B:")
        print(
            f"Paid amount: {payment_b.amount * currency.asa_to_unit:.2f} EUR, Due date: {coupon_due_date}, "
            f"Payment timestamp: {payment_b.timestamp}\n"
        )

        # Post payment state
        post_payment_account_a_paid_coupons = account_a.paid_coupons
        post_payment_account_b_paid_coupons = account_b.paid_coupons
        post_payment_state = fixed_coupon_bond_client_ongoing.get_global_state()
        assert (
            post_payment_account_a_paid_coupons
            == pre_payment_account_a_paid_coupons + 1
        )
        assert (
            post_payment_account_b_paid_coupons
            == pre_payment_account_b_paid_coupons + 1
        )
        assert (
            post_payment_state.paid_coupon_units
            == account_a_units * post_payment_account_a_paid_coupons
            + account_b_units * post_payment_account_b_paid_coupons
        )
        # TODO: assert balance updates


def test_pass_pay_multiple_coupons(
    currency: Currency,
    fixed_coupon_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_at_maturity: FixedCouponBondClient,
) -> None:
    account_units = account_a.units

    time_events = fixed_coupon_bond_client_at_maturity.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_at_maturity.app_id, sc_cst.BOX_ID_TIME_EVENTS)
            ]
        )
    ).return_value

    due_coupons = fixed_coupon_bond_client_at_maturity.get_coupons_status(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[
                (fixed_coupon_bond_client_at_maturity.app_id, sc_cst.BOX_ID_TIME_EVENTS)
            ]
        )
    ).return_value.due_coupons
    assert due_coupons == fixed_coupon_bond_cfg.total_coupons

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        print(f"Coupon {coupon} of {fixed_coupon_bond_cfg.total_coupons}")
        coupon_amount = fixed_coupon_bond_client_at_maturity.get_payment_amount(
            holding_address=account_a.holding_address,
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account_a.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_at_maturity.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                ],
            ),
        ).return_value.interest

        # Pre payment sate
        pre_payment_account_paid_coupons = account_a.paid_coupons
        pre_payment_state = fixed_coupon_bond_client_at_maturity.get_global_state()
        assert (
            pre_payment_state.paid_coupon_units
            == account_units * pre_payment_account_paid_coupons
        )

        # Coupon payment
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        payment = fixed_coupon_bond_client_at_maturity.pay_coupon(
            holding_address=account_a.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[currency.id],
                accounts=[account_a.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_at_maturity.app_id, account_a.box_id),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        ).return_value
        assert payment.amount == coupon_amount
        print(
            f"Paid amount: {payment.amount * currency.asa_to_unit:.2f} EUR, Due date: {coupon_due_date}, "
            f"Payment timestamp: {payment.timestamp}"
        )

        # Post payment state
        post_payment_account_paid_coupons = account_a.paid_coupons
        post_payment_state = fixed_coupon_bond_client_at_maturity.get_global_state()
        assert post_payment_account_paid_coupons == pre_payment_account_paid_coupons + 1
        assert (
            post_payment_state.paid_coupon_units
            == account_units * post_payment_account_paid_coupons
        )
        # TODO: assert balance updates


def test_pass_skip_suspended_account() -> None:
    pass  # TODO


def test_pass_skip_not_opted_in_account() -> None:
    pass  # TODO


def test_fail_unauthorized_status() -> None:
    pass  # TODO


def test_fail_defaulted_status() -> None:
    pass  # TODO


def test_fail_suspended() -> None:
    pass  # TODO


def test_fail_invalid_holding_address(
    oscar: SigningAccount, fixed_coupon_bond_client_at_maturity: FixedCouponBondClient
) -> None:
    with pytest.raises(Exception, match=err.INVALID_HOLDING_ADDRESS):
        fixed_coupon_bond_client_at_maturity.pay_coupon(
            holding_address=oscar.address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        DAsaAccount.box_id_from_address(oscar.address),
                    ),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ]
            ),
        )


def test_fail_no_units(
    account_factory: Callable[..., DAsaAccount],
    fixed_coupon_bond_client_primary: FixedCouponBondClient,
) -> None:
    account = account_factory(fixed_coupon_bond_client_primary)

    with pytest.raises(Exception, match=err.NO_UNITS):
        fixed_coupon_bond_client_primary.pay_coupon(
            holding_address=account.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                boxes=[
                    (fixed_coupon_bond_client_primary.app_id, account.box_id),
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
        )


def test_fail_no_due_coupon(
    algorand: AlgorandClient,
    fixed_coupon_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    fixed_coupon_bond_client_ongoing: FixedCouponBondClient,
) -> None:
    time_events = fixed_coupon_bond_client_ongoing.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(fixed_coupon_bond_client_ongoing.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value

    for coupon in range(1, fixed_coupon_bond_cfg.total_coupons + 1):
        with pytest.raises(Exception, match=err.NO_DUE_COUPON):
            fixed_coupon_bond_client_ongoing.pay_coupon(
                holding_address=account_a.holding_address,
                payment_info=b"",
                transaction_parameters=OnCompleteCallParameters(
                    foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                    accounts=[account_a.payment_address],
                    boxes=[
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
        coupon_due_date = time_events[sc_cfg.FIRST_COUPON_DATE_IDX - 1 + coupon]
        time_warp(coupon_due_date)
        fixed_coupon_bond_client_ongoing.pay_coupon(
            holding_address=account_a.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                accounts=[account_a.payment_address],
                boxes=[
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


def test_fail_pending_coupon_payment(
    fixed_coupon_bond_cfg: DAsaConfig,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    fixed_coupon_bond_client_at_maturity: FixedCouponBondClient,
) -> None:
    for coupon in range(fixed_coupon_bond_cfg.total_coupons - 1):
        if coupon % 2:
            first_payee = account_a
            second_payee = account_b
        else:
            first_payee = account_b
            second_payee = account_a

        fixed_coupon_bond_client_at_maturity.pay_coupon(
            holding_address=first_payee.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                accounts=[first_payee.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_at_maturity.app_id, first_payee.box_id),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )

        with pytest.raises(Exception, match=err.PENDING_COUPON_PAYMENT):
            fixed_coupon_bond_client_at_maturity.pay_coupon(
                holding_address=first_payee.holding_address,
                payment_info=b"",
                transaction_parameters=OnCompleteCallParameters(
                    foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                    accounts=[first_payee.payment_address],
                    boxes=[
                        (
                            fixed_coupon_bond_client_at_maturity.app_id,
                            first_payee.box_id,
                        ),
                        (
                            fixed_coupon_bond_client_at_maturity.app_id,
                            sc_cst.BOX_ID_COUPON_RATES,
                        ),
                        (
                            fixed_coupon_bond_client_at_maturity.app_id,
                            sc_cst.BOX_ID_TIME_EVENTS,
                        ),
                    ],
                ),
            )

        fixed_coupon_bond_client_at_maturity.pay_coupon(
            holding_address=second_payee.holding_address,
            payment_info=b"",
            transaction_parameters=OnCompleteCallParameters(
                foreign_assets=[fixed_coupon_bond_cfg.denomination_asset_id],
                accounts=[second_payee.payment_address],
                boxes=[
                    (fixed_coupon_bond_client_at_maturity.app_id, second_payee.box_id),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_COUPON_RATES,
                    ),
                    (
                        fixed_coupon_bond_client_at_maturity.app_id,
                        sc_cst.BOX_ID_TIME_EVENTS,
                    ),
                ],
            ),
        )
