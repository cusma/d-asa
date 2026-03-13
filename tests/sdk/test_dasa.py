from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import tomllib
from algosdk.constants import ZERO_ADDRESS

from smart_contracts import constants as cst
from smart_contracts import enums
from src import (
    DAsa,
    DAsaRole,
    PricingContext,
    RoleValidityWindow,
    TradeQuoteInput,
    make_pam_zero_coupon_bond,
    normalize_contract_attributes,
)
from src.models import AccountPosition


@dataclass(frozen=True, slots=True)
class DummyTransaction:
    kind: str
    params: object


class FakeMap:
    def __init__(self, values: dict[object, object] | None = None) -> None:
        self._values = values or {}

    def get_value(self, key: object) -> object | None:
        return self._values.get(key)


class FakeComposer:
    def __init__(self) -> None:
        self.steps: list[tuple[str, object, object | None]] = []

    def add_transaction(
        self, txn: object, signer: object | None = None
    ) -> FakeComposer:
        self.steps.append(("add_transaction", txn, signer))
        return self

    def transfer(self, args: object) -> FakeComposer:
        self.steps.append(("transfer", args, None))
        return self

    def send(self, send_params: object | None = None) -> dict[str, object]:
        return {"send_params": send_params, "steps": self.steps}

    def simulate(self, **kwargs: object) -> dict[str, object]:
        return {"kwargs": kwargs, "steps": self.steps}


class FakeCreateTransaction:
    def payment(self, params: object) -> DummyTransaction:
        return DummyTransaction(kind="payment", params=params)

    def asset_transfer(self, params: object) -> DummyTransaction:
        return DummyTransaction(kind="asset_transfer", params=params)


class FakeAlgod:
    def __init__(self, timestamp: int) -> None:
        self._timestamp = timestamp

    def status(self) -> dict[str, int]:
        return {"last-round": 1}

    def block_info(self, round_number: int) -> dict[str, object]:
        assert round_number == 1
        return {"block": {"ts": self._timestamp}}


class FakeAlgorand:
    def __init__(self, timestamp: int) -> None:
        self.client = SimpleNamespace(algod=FakeAlgod(timestamp))
        self.create_transaction = FakeCreateTransaction()
        self.send = SimpleNamespace(payment=lambda params: params)


class FakeSend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, object | None, object | None]] = []
        self.contract_schedule_returns: list[int] = []

    def contract_config(
        self,
        args: object,
        params: object | None = None,
        send_params: object | None = None,
    ) -> SimpleNamespace:
        self.calls.append(("contract_config", args, params, send_params))
        return SimpleNamespace(abi_return=111)

    def contract_schedule(
        self,
        args: object,
        params: object | None = None,
        send_params: object | None = None,
    ) -> SimpleNamespace:
        self.calls.append(("contract_schedule", args, params, send_params))
        value = 200 + len(
            [call for call in self.calls if call[0] == "contract_schedule"]
        )
        self.contract_schedule_returns.append(value)
        return SimpleNamespace(abi_return=value)


class FakeClient:
    def __init__(
        self,
        *,
        timestamp: int,
        global_state: SimpleNamespace,
        account_positions: dict[str, object] | None = None,
        schedule_pages: dict[int, object] | None = None,
        role_maps: dict[str, dict[str, object]] | None = None,
        send: FakeSend | None = None,
        app_id: int = 7,
        app_address: str = "APP_ADDRESS",
        default_sender: str | None = None,
        default_signer: object | None = None,
    ) -> None:
        role_maps = role_maps or {}
        self.algorand = FakeAlgorand(timestamp)
        self.app_id = app_id
        self.app_address = app_address
        self._default_sender = default_sender
        self._default_signer = default_signer
        self._send = send or FakeSend()
        self.state = SimpleNamespace(
            global_state=global_state,
            box=SimpleNamespace(
                account=FakeMap(account_positions),
                schedule_page=FakeMap(schedule_pages),
                account_manager=FakeMap(role_maps.get("account_manager")),
                primary_dealer=FakeMap(role_maps.get("primary_dealer")),
                trustee=FakeMap(role_maps.get("trustee")),
                authority=FakeMap(role_maps.get("authority")),
                observer=FakeMap(role_maps.get("observer")),
            ),
        )
        self.send = self._send

    def clone(
        self,
        *,
        default_sender: str | None = None,
        default_signer: object | None = None,
        **_: object,
    ) -> FakeClient:
        return FakeClient(
            timestamp=self.algorand.client.algod._timestamp,
            global_state=self.state.global_state,
            account_positions=self.state.box.account._values,
            schedule_pages=self.state.box.schedule_page._values,
            role_maps={
                "account_manager": self.state.box.account_manager._values,
                "primary_dealer": self.state.box.primary_dealer._values,
                "trustee": self.state.box.trustee._values,
                "authority": self.state.box.authority._values,
                "observer": self.state.box.observer._values,
            },
            send=self._send,
            app_id=self.app_id,
            app_address=self.app_address,
            default_sender=default_sender,
            default_signer=default_signer,
        )

    def new_group(self) -> FakeComposer:
        return FakeComposer()


def _global_state(**overrides: object) -> SimpleNamespace:
    defaults = {
        "arranger": "ARRANGER",
        "op_daemon": ZERO_ADDRESS,
        "contract_suspended": 0,
        "defaulted": 0,
        "status": enums.STATUS_ACTIVE,
        "contract_type": enums.CT_PAM,
        "denomination_asset_id": 1,
        "settlement_asset_id": 1,
        "initial_exchange_date": 1_700_000_000,
        "maturity_date": 1_800_000_000,
        "transfer_opening_date": 0,
        "transfer_closure_date": 0,
        "day_count_convention": enums.DCC_A360,
        "total_units": 100,
        "reserved_units_total": 0,
        "initial_exchange_amount": 10_000,
        "outstanding_principal": 10_000,
        "next_principal_redemption": 0,
        "dynamic_principal_redemption": 0,
        "interest_calculation_base": 10_000,
        "accrued_interest": 0,
        "nominal_interest_rate": 0,
        "rate_reset_spread": 0,
        "rate_reset_multiplier": cst.FIXED_POINT_SCALE,
        "rate_reset_floor": 0,
        "rate_reset_cap": 0,
        "rate_reset_next": 0,
        "has_rate_reset_floor": 0,
        "has_rate_reset_cap": 0,
        "reserved_principal": 0,
        "reserved_interest": 0,
        "cumulative_interest_index": 0,
        "cumulative_principal_index": 0,
        "event_cursor": 1,
        "schedule_entry_count": 2,
        "fixed_point_scale": cst.FIXED_POINT_SCALE,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _schedule_entry(
    event_id: int,
    event_type: int,
    scheduled_time: int,
    accrual_factor: int = 0,
) -> tuple[int, int, int, int, int, int, int, int, int]:
    return (event_id, event_type, scheduled_time, accrual_factor, 0, 0, 0, 0, 0)


def test_root_exports_include_high_level_surface() -> None:
    import src

    assert src.DAsa is DAsa
    assert src.make_pam_zero_coupon_bond is make_pam_zero_coupon_bond
    assert src.normalize_contract_attributes is normalize_contract_attributes
    assert not hasattr(src, "dasa_client")


def test_actualized_position_activates_reserved_units_and_settles_indices() -> None:
    client = FakeClient(
        timestamp=1_700_000_100,
        global_state=_global_state(
            cumulative_interest_index=105,
            cumulative_principal_index=207,
            event_cursor=4,
            fixed_point_scale=100,
        ),
        account_positions={
            "INVESTOR": AccountPosition(
                units=0,
                reserved_units=10,
                payment_address="INVESTOR",
                suspended=False,
                settled_cursor=0,
                interest_checkpoint=5,
                principal_checkpoint=7,
                claimable_interest=2,
                claimable_principal=3,
            )
        },
        schedule_pages={0: [_schedule_entry(0, enums.EVT_IED, 1_700_000_000)]},
    )

    position = (
        DAsa.from_client(client)
        .account(SimpleNamespace(address="INVESTOR", signer=object()))
        .get_actualized_position()
    )

    assert position.units == 10
    assert position.reserved_units == 0
    assert position.claimable_interest == 12
    assert position.claimable_principal == 23
    assert position.settled_cursor == 4
    assert position.interest_checkpoint == 105
    assert position.principal_checkpoint == 207


def test_quote_trade_adds_mid_period_accrual_and_dirty_price() -> None:
    start = 1_700_000_000
    valuation_time = start + 90 * cst.DAY_2_SEC
    client = FakeClient(
        timestamp=valuation_time,
        global_state=_global_state(
            accrued_interest=200,
            nominal_interest_rate=100_000_000,
            event_cursor=1,
            schedule_entry_count=2,
        ),
        account_positions={
            "INVESTOR": AccountPosition(
                units=20,
                reserved_units=0,
                payment_address="INVESTOR",
                suspended=False,
                settled_cursor=1,
                interest_checkpoint=0,
                principal_checkpoint=0,
                claimable_interest=15,
                claimable_principal=25,
            )
        },
        schedule_pages={
            0: [
                _schedule_entry(0, enums.EVT_IED, start),
                _schedule_entry(1, enums.EVT_IP, start + 180 * cst.DAY_2_SEC),
            ]
        },
    )
    app = DAsa.from_client(
        client, pricing_context=PricingContext(notional_unit_value=100)
    )
    quote = app.account(
        SimpleNamespace(address="INVESTOR", signer=object())
    ).quote_trade(
        20,
        clean_quote=TradeQuoteInput(clean_price_per_100=Decimal("99.50")),
    )

    assert quote.principal_share_total == 2_000
    assert quote.accrued_interest_not_due_total == 90
    assert quote.par_reference_dirty_total == 2_090
    assert quote.seller_retained_claimable_interest == 15
    assert quote.seller_retained_claimable_principal == 25
    assert quote.market_clean_total == Decimal("1990.00")
    assert quote.market_dirty_total == Decimal("2080.00")


def test_quote_trade_rejects_due_event() -> None:
    due_time = 1_700_000_000
    client = FakeClient(
        timestamp=due_time,
        global_state=_global_state(event_cursor=1, schedule_entry_count=2),
        account_positions={
            "INVESTOR": AccountPosition(
                units=10,
                reserved_units=0,
                payment_address="INVESTOR",
                suspended=False,
                settled_cursor=1,
                interest_checkpoint=0,
                principal_checkpoint=0,
                claimable_interest=0,
                claimable_principal=0,
            )
        },
        schedule_pages={
            0: [
                _schedule_entry(0, enums.EVT_IED, due_time - cst.DAY_2_SEC),
                _schedule_entry(1, enums.EVT_IP, due_time),
            ]
        },
    )
    holding = DAsa.from_client(client).account(
        SimpleNamespace(address="INVESTOR", signer=object())
    )

    try:
        holding.quote_trade(1)
    except ValueError as exc:
        assert "due ACTUS event is pending" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected quote_trade to reject a pending due event")


def test_build_otc_dvp_supports_algo_and_asa_payment_legs() -> None:
    timestamp = 1_700_000_100
    client = FakeClient(
        timestamp=timestamp,
        global_state=_global_state(
            accrued_interest=200,
            nominal_interest_rate=100_000_000,
            event_cursor=1,
            schedule_entry_count=2,
        ),
        account_positions={
            "SELLER": AccountPosition(
                units=20,
                reserved_units=0,
                payment_address="SELLER",
                suspended=False,
                settled_cursor=1,
                interest_checkpoint=0,
                principal_checkpoint=0,
                claimable_interest=0,
                claimable_principal=0,
            )
        },
        schedule_pages={
            0: [
                _schedule_entry(0, enums.EVT_IED, timestamp - cst.DAY_2_SEC),
                _schedule_entry(1, enums.EVT_IP, timestamp + 90 * cst.DAY_2_SEC),
            ]
        },
    )
    app = DAsa.from_client(client)
    seller = SimpleNamespace(address="SELLER", signer=object())
    buyer = SimpleNamespace(address="BUYER", signer=object())

    algo_draft = app.account(seller).build_otc_dvp(
        buyer=buyer,
        units=5,
        payment_amount=1_000,
    )
    asa_draft = app.account(seller).build_otc_dvp(
        buyer=buyer,
        units=5,
        payment_amount=2_000,
        payment_asset_id=77,
    )

    assert algo_draft.payment_transaction.kind == "payment"
    assert asa_draft.payment_transaction.kind == "asset_transfer"
    assert algo_draft.composer.steps[0][0] == "add_transaction"
    assert algo_draft.composer.steps[1][0] == "transfer"
    transfer_args = algo_draft.composer.steps[1][1]
    assert transfer_args.sender_holding_address == "SELLER"
    assert transfer_args.receiver_holding_address == "BUYER"
    assert transfer_args.units == 5


def test_arranger_configure_contract_uses_mappers_and_updates_pricing_context() -> None:
    normalized = normalize_contract_attributes(
        make_pam_zero_coupon_bond(
            contract_id=1,
            status_date=1_700_000_000,
            initial_exchange_date=1_700_000_000 + 30 * cst.DAY_2_SEC,
            maturity_date=1_700_000_000 + 365 * cst.DAY_2_SEC,
            notional_principal=10_000,
            premium_discount_at_ied=0,
        ),
        denomination_asset_id=1,
        denomination_asset_decimals=2,
        notional_unit_value=100,
        secondary_market_opening_date=1_700_000_000 + 30 * cst.DAY_2_SEC,
        secondary_market_closure_date=1_700_000_000 + 366 * cst.DAY_2_SEC,
    )
    fake_send = FakeSend()
    client = FakeClient(
        timestamp=1_700_000_000,
        global_state=_global_state(
            status=enums.STATUS_INACTIVE, event_cursor=0, schedule_entry_count=0
        ),
        send=fake_send,
    )
    app = DAsa.from_client(client)
    arranger = SimpleNamespace(address="ARRANGER", signer=object())

    result = app.arranger(arranger).configure_contract(
        normalized=normalized,
        prospectus_url="prospectus",
    )

    assert result == normalized
    assert app.pricing_context == PricingContext(
        notional_unit_value=normalized.terms.notional_unit_value
    )
    assert [call[0] for call in fake_send.calls] == [
        "contract_config",
        "contract_schedule",
    ]


def test_pyproject_runtime_dependencies_only_keep_algokit_utils() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    parsed = tomllib.loads(pyproject.read_text())
    poetry = parsed["tool"]["poetry"]
    runtime_dependencies = poetry["dependencies"]
    dev_dependencies = poetry["group"]["dev"]["dependencies"]

    assert "algokit-utils" in runtime_dependencies
    assert "python-dotenv" not in runtime_dependencies
    assert "algorand-python" not in runtime_dependencies
    assert "python-dotenv" in dev_dependencies
    assert poetry["packages"] == [
        {"include": "src"},
        {"include": "smart_contracts"},
        {"include": "modules"},
    ]


def test_contract_view_role_helpers_resolve_active_roles() -> None:
    timestamp = 1_700_000_000
    client = FakeClient(
        timestamp=timestamp,
        global_state=_global_state(op_daemon="OP_DAEMON"),
        role_maps={
            "account_manager": {
                "MANAGER": SimpleNamespace(
                    role_validity_start=0,
                    role_validity_end=2**64 - 1,
                )
            }
        },
    )
    roles = DAsa.from_client(client).contract.get_address_roles("MANAGER")

    assert roles.account_manager is True
    assert roles.arranger is False
    assert roles.op_daemon is False
    assert DAsa.from_client(client).contract.get_role_validity(
        DAsaRole.ACCOUNT_MANAGER,
        "MANAGER",
    ) == RoleValidityWindow(0, 2**64 - 1)


def test_contract_view_get_address_roles_at_time_zero() -> None:
    """Test that get_address_roles correctly uses timestamp 0 when at_time=0 is passed."""
    # Current timestamp is much later than 0
    current_timestamp = 1_700_000_000

    client = FakeClient(
        timestamp=current_timestamp,
        global_state=_global_state(op_daemon="OP_DAEMON"),
        role_maps={
            "account_manager": {
                "MANAGER": SimpleNamespace(
                    # Role is only valid from timestamp 1000 onwards
                    role_validity_start=1000,
                    role_validity_end=2**64 - 1,
                )
            }
        },
    )

    contract_view = DAsa.from_client(client).contract

    # When checking roles at current time, the role should be active (1000 < current_timestamp)
    roles_now = contract_view.get_address_roles("MANAGER")
    assert roles_now.account_manager is True

    # When checking roles at timestamp 0, the role should NOT be active (0 < 1000)
    # This tests the edge case where at_time=0 should use 0, not fall back to current timestamp
    roles_at_zero = contract_view.get_address_roles("MANAGER", at_time=0)
    assert roles_at_zero.account_manager is False

    # When checking roles at timestamp 1000, the role should be active (exactly at start)
    roles_at_start = contract_view.get_address_roles("MANAGER", at_time=1000)
    assert roles_at_start.account_manager is True
