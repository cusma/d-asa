from algopy import (
    Account,
    Asset,
    Box,
    Bytes,
    Global,
    OpUpFeeSource,
    String,
    Txn,
    UInt64,
    arc4,
    ensure_budget,
    itxn,
    op,
    urange,
)

from modules.accounting import AccountingModule
from smart_contracts import abi_types as typ
from smart_contracts import config as cfg
from smart_contracts import constants as cst
from smart_contracts import enums
from smart_contracts import errors as err
from smart_contracts.events import Event


class CoreFinancialCommonMixin(AccountingModule):
    """Common financial core shared by Maturities and Non-Maturities variants."""

    def __init__(self) -> None:
        super().__init__()

        # Asset Configuration
        self.denomination_asset_id = Asset()
        self.settlement_asset_id = Asset()
        self.unit_value = UInt64()
        self.day_count_convention = UInt64()

        # Metadata
        self.metadata = Bytes()

        # Principal / Rates
        self.principal_discount = UInt64()
        self.interest_rate = UInt64()
        self.total_coupons = UInt64()

        # Time Schedule
        self.time_events = Box(typ.TimeEvents, key=cst.BOX_ID_TIME_EVENTS)
        self.primary_distribution_opening_date = UInt64()
        self.primary_distribution_closure_date = UInt64()
        self.issuance_date = UInt64()
        self.secondary_market_opening_date = UInt64()
        self.secondary_market_closure_date = UInt64()
        self.maturity_date = UInt64()

    def assert_denomination_asset(self, denomination_asset_id: Asset) -> None:
        # The reference implementation has on-chain denomination with ASA
        _creator, exists = op.AssetParamsGet.asset_creator(denomination_asset_id)
        assert exists, err.INVALID_DENOMINATION

    def set_denomination_asset(self, denomination_asset_id: Asset) -> None:
        self.denomination_asset_id = denomination_asset_id

    def assert_settlement_asset(self, settlement_asset_id: Asset) -> None:
        # The reference implementation settlement asset is the denomination asset
        assert (
            settlement_asset_id == self.denomination_asset_id
        ), err.INVALID_SETTLEMENT_ASSET

    def set_settlement_asset(self, settlement_asset_id: Asset) -> None:
        self.settlement_asset_id = settlement_asset_id
        # The reference implementation has on-chain settlement with ASA
        itxn.AssetTransfer(
            xfer_asset=self.settlement_asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=Global.min_txn_fee,
        ).submit()

    def assert_day_count_convention(self, day_count_convention: UInt64) -> None:
        # The reference implementation supports only the Actual/Actual and Continuous day-count conventions
        assert day_count_convention in (
            UInt64(cst.DCC_A_A),
            UInt64(cst.DCC_CONT),
        ), err.INVALID_DAY_COUNT_CONVENTION

    def set_day_count_convention(self, day_count_convention: UInt64) -> None:
        self.day_count_convention = day_count_convention

    def assert_interest_rate(self, interest_rate: UInt64) -> None:
        # This subroutine must be used after the principal discount has been set
        if not self.principal_discount:
            assert interest_rate > UInt64(0), err.INVALID_INTEREST_RATE

    def set_interest_rate(self, interest_rate: UInt64) -> None:
        self.interest_rate = interest_rate

    def assert_coupon_rates(self, coupon_rates: typ.CouponRates) -> None:
        assert not coupon_rates.length, err.INVALID_COUPON_RATES

    def set_coupon_rates(self, coupon_rates: typ.CouponRates) -> None:
        self.total_coupons = coupon_rates.length

    def assert_time_schedule_limits(self, time_events: typ.TimeEvents) -> None:
        assert (
            time_events.length == self.total_coupons + cfg.TIME_SCHEDULE_LIMITS
        ), err.INVALID_TIME_EVENTS_LENGTH

    def assert_time_events_sorted(self, time_events: typ.TimeEvents) -> None:
        assert (
            time_events[cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX]
            > Global.latest_timestamp
        ), err.INVALID_TIME
        for idx in urange(time_events.length - 1):
            ensure_budget(
                required_budget=UInt64(cfg.OP_UP_TIME_EVENT_SORTING),
                fee_source=OpUpFeeSource.AppAccount,
            )
            time_i = time_events[idx]
            time_f = time_events[idx + 1]
            assert time_f > time_i, err.INVALID_SORTING
            if self.day_count_convention != UInt64(cst.DCC_CONT):
                # The reference implementation requires time periods expressed in days for regular day-count conventions
                assert (time_f - time_i) % UInt64(
                    cst.DAY_2_SEC
                ) == 0, err.INVALID_TIME_PERIOD

    def set_time_events(self, time_events: typ.TimeEvents) -> None:
        self.time_events.value = time_events.copy()
        self.primary_distribution_opening_date = time_events[
            cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX
        ]
        self.primary_distribution_closure_date = time_events[
            cfg.PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX
        ]
        self.issuance_date = time_events[cfg.ISSUANCE_DATE_IDX]
        self.maturity_date = time_events[cfg.MATURITY_DATE_IDX]

    def assert_time_periods(self, time_periods: typ.TimePeriods) -> None:
        assert not time_periods.length, err.INVALID_TIME_PERIODS

    def set_time_periods(self, time_periods: typ.TimePeriods) -> None:
        pass

    def assert_is_primary_distribution_open(self) -> None:
        assert (
            self.status_is_active()
            and self.primary_distribution_opening_date
            <= Global.latest_timestamp
            < self.primary_distribution_closure_date
        ), err.PRIMARY_DISTRIBUTION_CLOSED

    def assert_is_secondary_market_open(self) -> None:
        assert (
            self.status_is_active()
            and self.secondary_market_opening_date <= Global.latest_timestamp
            and (
                not self.secondary_market_closure_date
                or Global.latest_timestamp < self.secondary_market_closure_date
            )
        ), err.SECONDARY_MARKET_CLOSED

    def days_in(self, time_period: UInt64) -> UInt64:
        return time_period // UInt64(cst.DAY_2_SEC)

    def assert_asset_transfer_authorization(
        self,
        sender_holding_address: Account,
        receiver_holding_address: Account,
    ) -> None:
        # The reference implementation grants transfer right to D-ASA owners. Other implementations may relay on other
        # roles, external Apps through C2C calls (e.g., an order book), or off-chain transfer agents.
        assert Txn.sender == sender_holding_address, err.UNAUTHORIZED
        self.assert_is_not_asset_defaulted()
        self.assert_is_not_asset_suspended()
        self.assert_valid_holding_address(sender_holding_address)
        self.assert_valid_holding_address(receiver_holding_address)
        self.assert_is_not_account_suspended(sender_holding_address)
        self.assert_is_not_account_suspended(receiver_holding_address)

    def assert_asset_transfer_preconditions(
        self,
        sender_holding_address: Account,
        receiver_holding_address: Account,
        units: UInt64,
    ) -> None:
        self.assert_is_secondary_market_open()
        self.assert_asset_transfer_authorization(
            sender_holding_address,
            receiver_holding_address,
        )
        assert sender_holding_address != receiver_holding_address, err.SELF_TRANSFER
        assert units > 0, err.NULL_TRANSFER
        assert units <= self.account[sender_holding_address].units, err.OVER_TRANSFER
        self.assert_fungible_transfer(
            sender_holding_address,
            receiver_holding_address,
        )

    def update_supply_after_principal_payment(self, holding_address: Account) -> None:
        self.circulating_units -= self.account[holding_address].units
        self.account[holding_address].units = UInt64()
        self.end_if_no_circulating_units()

    # Hook defaults for feature-specialized mixins.
    def count_due_coupons(self) -> UInt64:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def all_due_coupons_paid(self, _due_coupons: UInt64) -> bool:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def assert_pay_principal_authorization(self, _holding_address: Account) -> None:
        op.err(err.INVALID_MIXIN_COMPOSITION)

    def _emit_ied(self, *, payoff: UInt64) -> None:
        """Emit Initial Exchange (IED) event."""
        arc4.emit(
            Event(
                contract_id=Global.current_application_id.id,
                type=arc4.UInt8(enums.EVT_TYPE_IED),
                type_name=String("IED"),
                time=Global.latest_timestamp,
                payoff=payoff,
                currency_id=self.denomination_asset_id.id,
                currency_unit=self.denomination_asset_id.unit_name,
                nominal_value=self.total_units * self.unit_value,
                nominal_rate_bps=arc4.UInt16(0),
                nominal_accrued=UInt64(0),
            )
        )

    def _configure_asset_terms(
        self,
        *,
        denomination_asset_id: Asset,
        settlement_asset_id: Asset,
        principal: UInt64,
        principal_discount: UInt64,
        minimum_denomination: UInt64,
        day_count_convention: arc4.UInt8,
        interest_rate: arc4.UInt16,
        coupon_rates: typ.CouponRates,
        time_events: typ.TimeEvents,
        time_periods: typ.TimePeriods,
    ) -> None:
        self.assert_caller_is_arranger()
        assert self.status == enums.STATUS_INACTIVE, err.ALREADY_CONFIGURED

        # Set Denomination Asset
        self.assert_denomination_asset(denomination_asset_id)
        self.set_denomination_asset(denomination_asset_id)

        # Set Settlement Asset
        self.assert_settlement_asset(settlement_asset_id)
        self.set_settlement_asset(settlement_asset_id)

        # Set Principal and Minimum Denomination
        assert principal % minimum_denomination == 0, err.INVALID_MINIMUM_DENOMINATION
        self.unit_value = minimum_denomination
        self.total_units = principal // minimum_denomination
        self.principal_discount = principal_discount

        # Set Day-Count Convention
        self.assert_day_count_convention(day_count_convention.as_uint64())
        self.set_day_count_convention(day_count_convention.as_uint64())

        # Set Interest Rate
        self.assert_interest_rate(interest_rate.as_uint64())
        self.set_interest_rate(interest_rate.as_uint64())

        # Set Coupons
        self.assert_coupon_rates(coupon_rates)
        self.set_coupon_rates(coupon_rates)

        # Set Time Events
        self.assert_time_schedule_limits(time_events)
        self.assert_time_events_sorted(time_events)
        self.set_time_events(time_events)

        # Set Time Periods
        self.assert_time_periods(time_periods)
        self.set_time_periods(time_periods)

        self.status = UInt64(enums.STATUS_ACTIVE)

    @arc4.abimethod(create="require")
    def asset_create(self, *, arranger: Account, metadata: typ.AssetMetadata) -> None:
        """
        Create a new D-ASA

        Args:
            arranger: D-ASA Arranger Address
            metadata: D-ASA metadata
        """
        self.arranger.value = arranger
        self.metadata = metadata.bytes

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def asset_update(self, *, metadata: typ.AssetMetadata) -> None:
        """
        Update D-ASA application.
        """
        # The reference implementation grants the update permissions to the Arranger.
        # Other implementations may disable D-ASA application updatability or change its authorizations.
        # ⚠️ WARNING: Application updates must be executed VERY carefully, as they might introduce breaking changes.
        self.assert_caller_is_arranger()
        self.metadata = metadata.bytes

    @arc4.abimethod
    def set_secondary_time_events(
        self, *, secondary_market_time_events: typ.TimeEvents
    ) -> typ.SecondaryMarketSchedule:
        """
        Set secondary market time schedule

        Args:
            secondary_market_time_events: Secondary market time events (strictly ascending order)

        Returns:
            Secondary Market Opening Date, Secondary Market Closure Date

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_TIME_EVENTS_LENGTH: Time events length is invalid
            INVALID_SORTING: Time events are not sorted correctly
            INVALID_SECONDARY_OPENING_DATE: Invalid secondary market opening date
            INVALID_SECONDARY_CLOSURE_DATE: Invalid secondary market closure date
        """
        self.assert_caller_is_arranger()
        assert not self.status_is_ended(), err.UNAUTHORIZED
        self.assert_is_not_asset_defaulted()

        assert secondary_market_time_events.length >= 1, err.INVALID_TIME_EVENTS_LENGTH
        if secondary_market_time_events.length > 1:
            self.assert_time_events_sorted(secondary_market_time_events)

        assert (
            self.issuance_date
            <= secondary_market_time_events[cfg.SECONDARY_MARKET_OPENING_DATE_IDX]
        ), err.INVALID_SECONDARY_OPENING_DATE
        self.secondary_market_opening_date = secondary_market_time_events[
            cfg.SECONDARY_MARKET_OPENING_DATE_IDX
        ]
        if self.maturity_date:
            assert (
                self.maturity_date
                >= secondary_market_time_events[cfg.SECONDARY_MARKET_CLOSURE_DATE_IDX]
            ), err.INVALID_SECONDARY_CLOSURE_DATE
            self.secondary_market_closure_date = secondary_market_time_events[
                cfg.SECONDARY_MARKET_CLOSURE_DATE_IDX
            ]
        return typ.SecondaryMarketSchedule(
            secondary_market_opening_date=self.secondary_market_opening_date,
            secondary_market_closure_date=self.secondary_market_closure_date,
        )

    @arc4.abimethod
    def set_default_status(self, *, defaulted: bool) -> UInt64:
        """
        Set D-ASA default status

        Args:
            defaulted: Default status

        Raises:
            UNAUTHORIZED: Not authorized
        """

        self.assert_caller_is_trustee()
        self.asset_defaulted = defaulted
        return Global.latest_timestamp

    @arc4.abimethod
    def primary_distribution(
        self, *, holding_address: Account, units: UInt64
    ) -> UInt64:
        """
        Distribute D-ASA units to accounts according the primary market

        Args:
            holding_address: Account Holding Address
            units: Amount of D-ASA units to distribute

        Returns:
            Remaining D-ASA units to be distributed

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended operations
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            ZERO_UNITS: Cannot distribute zero units
            OVER_DISTRIBUTION: Insufficient remaining D-ASA units
            PRIMARY_DISTRIBUTION_CLOSED: Primary distribution is closed
        """
        self.assert_is_primary_distribution_open()
        # The reference implementation grants primary distribution permissions to the Primary Dealer role. Other
        # implementations may relay on other roles or external Apps through C2C calls (e.g., an auction).
        self.assert_caller_is_primary_dealer()
        self.assert_valid_holding_address(holding_address)
        self.assert_is_not_asset_defaulted()
        self.assert_is_not_asset_suspended()
        assert units > 0, err.ZERO_UNITS
        assert self.circulating_units + units <= self.total_units, err.OVER_DISTRIBUTION

        self.circulating_units += units
        self.account[holding_address].units += units
        self.account[holding_address].unit_value = self.unit_value

        self._emit_ied(payoff=self.unit_value * units)

        return self.total_units - self.circulating_units

    @arc4.abimethod(readonly=True)
    def get_asset_info(self) -> typ.AssetInfo:
        """
        Get D-ASA info

        Returns:
            Denomination asset ID, Settlement asset ID, Outstanding principal, Unit nominal value, Day-count convention,
            Interest rate, Total supply, Circulating supply, Primary distribution opening date, Primary distribution
            closure date, Issuance date, Maturity date, Suspended, Performance
        """
        performance = UInt64(cst.PRF_PERFORMANT)
        if Global.latest_timestamp > self.maturity_date > 0:
            performance = UInt64(cst.PRF_MATURED)
        # The reference implementation has no grace or delinquency periods
        if self.asset_defaulted:
            performance = UInt64(cst.PRF_DEFAULTED)

        return typ.AssetInfo(
            denomination_asset_id=self.denomination_asset_id.id,
            settlement_asset_id=self.settlement_asset_id.id,
            outstanding_principal=self.outstanding_principal(),
            unit_value=self.unit_value,
            day_count_convention=arc4.UInt8(self.day_count_convention),
            principal_discount=arc4.UInt16(self.principal_discount),
            interest_rate=arc4.UInt16(self.interest_rate),
            total_supply=self.total_units,
            circulating_supply=self.circulating_units,
            primary_distribution_opening_date=self.primary_distribution_opening_date,
            primary_distribution_closure_date=self.primary_distribution_closure_date,
            issuance_date=self.issuance_date,
            maturity_date=self.maturity_date,
            suspended=self.asset_suspended,
            performance=arc4.UInt8(performance),
        )

    @arc4.abimethod(readonly=True)
    def get_time_events(self) -> typ.TimeEvents:
        """
        Get D-ASA time events

        Returns:
            Time events
        """
        time_events = typ.TimeEvents()
        if self.status_is_active():
            time_events = self.time_events.value.copy()
        return time_events

    @arc4.abimethod(readonly=True)
    def get_secondary_market_schedule(self) -> typ.TimeEvents:
        """
        Get secondary market schedule

        Returns:
            Secondary market schedule
        """
        return typ.TimeEvents(
            (self.secondary_market_opening_date, self.secondary_market_closure_date)
        )

    @arc4.abimethod(readonly=True)
    def get_asset_metadata(self) -> typ.AssetMetadata:
        """
        Get D-ASA metadata

        Returns:
            Contract type, Calendar, Business day convention, End of month convention, Early repayment effect, Early
            repayment penalty type, Prospectus hash, Prospectus URL
        """
        return typ.AssetMetadata.from_bytes(self.metadata)
