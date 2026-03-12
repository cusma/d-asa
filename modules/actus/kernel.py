from algopy import Asset, Global, UInt64, op

from modules import RbacModule
from smart_contracts import constants as cst
from smart_contracts import enums
from smart_contracts import errors as err
from smart_contracts.abi_types import TimeStamp


class ActusKernelStateModule(RbacModule):
    """Global State and shared kernel math helpers."""

    def __init__(self) -> None:
        """Initialize the global state variables used by the ACTUS kernel."""
        super().__init__()

        # Contract
        self.status = UInt64(enums.STATUS_INACTIVE)
        self.contract_type = UInt64()

        # Denomination
        self.denomination_asset_id = Asset()
        self.settlement_asset_id = Asset()

        # Time
        self.initial_exchange_date = TimeStamp()
        self.maturity_date = TimeStamp()
        self.secondary_market_opening_date = TimeStamp()
        self.secondary_market_closure_date = TimeStamp()

        # Day Count Convention
        self.day_count_convention = UInt64()

        # Principal
        self.outstanding_principal = UInt64()

        self.total_units = UInt64()
        self.circulating_units = UInt64()
        self.reserved_units_total = UInt64()

        # Interest
        self.nominal_interest_rate = UInt64()
        self.accrued_interest = UInt64()
        self.rate_reset_spread = UInt64()
        self.rate_reset_multiplier = UInt64(cst.FIXED_POINT_SCALE)
        self.rate_reset_floor = UInt64()
        self.rate_reset_cap = UInt64()
        self.rate_reset_next = UInt64()

        self.initial_exchange_amount = UInt64()
        self.interest_calculation_base = UInt64()
        self.next_principal_redemption = UInt64()

        # Primary Distribution
        self.reserved_principal = UInt64()
        self.reserved_interest = UInt64()

        # Cumulative Index
        self.cumulative_interest_index = UInt64()
        self.cumulative_principal_index = UInt64()

        # Flags
        self.has_rate_reset_floor = False
        self.has_rate_reset_cap = False
        self.dynamic_principal_redemption = False

        # Scaling
        self.fixed_point_scale = UInt64(cst.FIXED_POINT_SCALE)

    def status_is_active(self) -> bool:
        """Return whether the contract is active after IED."""
        return self.status == UInt64(enums.STATUS_ACTIVE)

    def status_is_pending_ied(self) -> bool:
        """Return whether the contract is configured but still awaiting IED."""
        return self.status == UInt64(enums.STATUS_PENDING_IED)

    def status_is_ended(self) -> bool:
        """Return whether the contract has reached its terminal state."""
        return self.status == UInt64(enums.STATUS_ENDED)

    def assert_configured(self) -> None:
        """Require the contract to have completed configuration."""
        assert self.status != UInt64(enums.STATUS_INACTIVE), err.CONTRACT_NOT_CONFIGURED

    def assert_initial_exchange_executed(self) -> None:
        """Require the initial exchange event to have been executed."""
        assert not self.status_is_pending_ied(), err.INITIAL_EXCHANGE_PENDING

    def _reserved_total(self) -> UInt64:
        """Return the settlement funds already ring-fenced for holders."""
        return self.reserved_interest + self.reserved_principal

    def _available_settlement_funds(self) -> UInt64:
        """Return the app's free settlement balance after reserved cashflows."""
        balance = self.settlement_asset_id.balance(Global.current_application_address)
        reserved_total = self._reserved_total()
        assert balance >= reserved_total, err.NOT_ENOUGH_FUNDS
        return balance - reserved_total

    def _scaled_mul_div(
        self, multiplicand: UInt64, multiplier: UInt64, divisor: UInt64
    ) -> UInt64:
        """Multiply and divide in fixed-point space using wide AVM math."""
        if multiplicand == UInt64(0) or multiplier == UInt64(0):
            return UInt64(0)
        high, low = op.mulw(multiplicand, multiplier)
        return op.divw(high, low, divisor)

    def _amount_to_index_delta(self, amount: UInt64) -> UInt64:
        """Convert a contract-wide amount into a per-unit cumulative index delta."""
        if amount == UInt64(0):
            return UInt64(0)
        assert self.circulating_units > UInt64(0), err.NO_UNITS
        return self._scaled_mul_div(
            amount, self.fixed_point_scale, self.circulating_units
        )

    def _assert_transfer_window(self) -> None:
        """Require transfers to happen within the configured secondary market window."""
        if self.secondary_market_opening_date:
            assert (
                self.secondary_market_opening_date <= Global.latest_timestamp
            ), err.SECONDARY_MARKET_CLOSED
        if self.secondary_market_closure_date:
            assert (
                Global.latest_timestamp < self.secondary_market_closure_date
            ), err.SECONDARY_MARKET_CLOSED
