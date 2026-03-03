from collections.abc import Callable

import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.perpetual_bond.perpetual_bond_client import (
    AccountGovSuspensionArgs,
    AssetTransferArgs,
    GetAccountUnitsCurrentValueArgs,
    PayCouponArgs,
    PerpetualBondClient,
)
from tests.utils import DAsaAccount, DAsaAuthority, DAsaConfig, time_warp


def test_pass_asset_transfer(
    perpetual_bond_cfg: DAsaConfig,
    perpetual_bond_client_primary: PerpetualBondClient,
    account_factory: Callable[..., DAsaAccount],
    account_with_coupons_factory: Callable[..., DAsaAccount],
) -> None:
    account_a = account_with_coupons_factory(units=3, coupons=1)
    account_b = account_factory(perpetual_bond_client_primary)

    state = perpetual_bond_client_primary.state.global_state
    coupon_1_date = state.issuance_date + state.coupon_period

    pre_transfer_units_a = account_a.units
    pre_transfer_units_b = account_b.units
    pre_transfer_unit_value_a = account_a.unit_value
    pre_transfer_unit_value_b = account_b.unit_value

    assert pre_transfer_unit_value_a != pre_transfer_unit_value_b
    assert pre_transfer_unit_value_b == 0
    assert account_a.paid_coupons != account_b.paid_coupons

    time_warp(coupon_1_date + state.coupon_period // 10)

    transfer_units = 1
    accrued_interest = (
        perpetual_bond_client_primary.send.get_account_units_current_value(
            GetAccountUnitsCurrentValueArgs(
                holding_address=account_a.holding_address,
                units=transfer_units,
            )
        ).abi_return.accrued_interest
    )

    transferred_value = perpetual_bond_client_primary.send.asset_transfer(
        AssetTransferArgs(
            sender_holding_address=account_a.holding_address,
            receiver_holding_address=account_b.holding_address,
            units=transfer_units,
        ),
        params=CommonAppCallParams(sender=account_a.address),
    ).abi_return

    post_transfer_units_a = account_a.units
    post_transfer_units_b = account_b.units
    post_transfer_unit_value_a = account_a.unit_value
    post_transfer_unit_value_b = account_b.unit_value

    assert (
        transferred_value
        == perpetual_bond_cfg.minimum_denomination * transfer_units + accrued_interest
    )
    assert post_transfer_units_a == pre_transfer_units_a - transfer_units
    assert post_transfer_units_b == pre_transfer_units_b + transfer_units
    assert post_transfer_unit_value_a == post_transfer_unit_value_b
    assert account_a.paid_coupons == account_b.paid_coupons


def test_fail_secondary_market_not_open_yet(
    perpetual_bond_client_primary: PerpetualBondClient,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
) -> None:
    with pytest.raises(LogicError, match=err.SECONDARY_MARKET_CLOSED):
        perpetual_bond_client_primary.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_unauthorized(
    no_role_account: SigningAccount,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_defaulted_status(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_defaulted: PerpetualBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.DEFAULTED):
        perpetual_bond_client_defaulted.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_suspended(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_suspended: PerpetualBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.SUSPENDED):
        perpetual_bond_client_suspended.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_invalid_sender(
    no_role_account: SigningAccount,
    account_a: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=no_role_account.address,
                receiver_holding_address=account_a.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_fail_invalid_receiver(
    no_role_account: SigningAccount,
    account_a: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_HOLDING_ADDRESS):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=no_role_account.address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_suspended_sender(
    authority: DAsaAuthority,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    perpetual_bond_client_ongoing.send.account_gov_suspension(
        AccountGovSuspensionArgs(
            holding_address=account_a.holding_address,
            suspended=True,
        ),
        params=CommonAppCallParams(sender=authority.address),
    )

    with pytest.raises(LogicError, match=err.SUSPENDED):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_suspended_receiver(
    authority: DAsaAuthority,
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    perpetual_bond_client_ongoing.send.account_gov_suspension(
        AccountGovSuspensionArgs(
            holding_address=account_b.holding_address,
            suspended=True,
        ),
        params=CommonAppCallParams(sender=authority.address),
    )

    with pytest.raises(LogicError, match=err.SUSPENDED):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


def test_fail_over_transfer(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    with pytest.raises(LogicError, match=err.OVER_TRANSFER):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_a.holding_address,
                receiver_holding_address=account_b.holding_address,
                units=account_a.units + 1,
            ),
            params=CommonAppCallParams(sender=account_a.address),
        )


@pytest.mark.skip("The PENDING_COUPON_PAYMENT is shadowed by NON_FUNGIBLE_UNITS")
def test_fail_pending_coupon_payment(
    account_a: DAsaAccount,
    account_b: DAsaAccount,
    perpetual_bond_client_ongoing: PerpetualBondClient,
) -> None:
    state = perpetual_bond_client_ongoing.state.global_state
    time_warp(state.issuance_date + state.coupon_period)
    perpetual_bond_client_ongoing.send.pay_coupon(
        PayCouponArgs(
            holding_address=account_a.holding_address,
            payment_info=b"",
        )
    )

    with pytest.raises(LogicError, match=err.PENDING_COUPON_PAYMENT):
        perpetual_bond_client_ongoing.send.asset_transfer(
            AssetTransferArgs(
                sender_holding_address=account_b.holding_address,
                receiver_holding_address=account_a.holding_address,
                units=1,
            ),
            params=CommonAppCallParams(sender=account_b.address),
        )
