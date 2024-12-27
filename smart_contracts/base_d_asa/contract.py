# pyright: reportMissingModuleSource=false
from algopy import (
    ARC4Contract,
    Asset,
    Box,
    BoxMap,
    Bytes,
    Global,
    OpUpFeeSource,
    Txn,
    UInt64,
    arc4,
    ensure_budget,
    itxn,
    op,
    subroutine,
    urange,
)

from .. import constants as cst
from .. import errors as err
from .. import types as typ
from . import config as cfg


class BaseDAsa(ARC4Contract):
    """
    Base D-ASA Class implementing common interfaces and state schema:

    - Asset creation and configuration
    - Role-based access control
    - Account management (creation, suspension, close-out)
    - Primary distribution
    - Getters (asset info, account info, time events)
    """

    def __init__(self) -> None:
        # Role Based Access Control
        self.arranger = Global.zero_address  # TODO: Use role key
        self.account_manager = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_BOX_ID_ACCOUNT_MANAGER
        )
        self.primary_dealer = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_BOX_ID_PRIMARY_DEALER
        )
        self.trustee = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_BOX_ID_TRUSTEE
        )
        self.authority = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_BOX_ID_AUTHORITY
        )

        # Asset Configuration
        self.denomination_asset_id = UInt64()
        self.unit_value = UInt64()
        self.day_count_convention = UInt64()

        # Metadata
        self.metadata = Bytes()

        # Supply
        self.total_units = UInt64()
        self.circulating_units = UInt64()

        # Interest
        self.interest_rate = UInt64()

        # Coupons
        self.coupon_rates = Box(typ.CouponRates, key=cst.BOX_ID_COUPON_RATES)
        self.total_coupons = UInt64()

        # Time Schedule
        self.time_events = Box(typ.TimeEvents, key=cst.BOX_ID_TIME_EVENTS)
        self.primary_distribution_opening_date = UInt64()
        self.primary_distribution_closure_date = UInt64()
        self.issuance_date = UInt64()
        self.secondary_market_opening_date = UInt64()
        self.secondary_market_closure_date = UInt64()
        self.maturity_date = UInt64()

        # Status
        self.status = UInt64(cfg.STATUS_EMPTY)
        self.suspended = UInt64()
        self.defaulted = UInt64()

        # Account
        self.account = BoxMap(
            arc4.Address, typ.AccountInfo, key_prefix=cst.PREFIX_BOX_ID_ACCOUNT
        )

    @subroutine
    def status_is_active(self) -> bool:
        return self.status == cfg.STATUS_ACTIVE

    @subroutine
    def status_is_ended(self) -> bool:
        return self.status == cfg.STATUS_ENDED

    @subroutine
    def assert_is_not_defaulted(self) -> None:
        assert not self.defaulted, err.DEFAULTED

    @subroutine
    def assert_is_not_suspended(self) -> None:
        assert not self.suspended, err.SUSPENDED

    @subroutine
    def assert_caller_is_arranger(self) -> None:
        assert Txn.sender == self.arranger, err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_account_manager(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.account_manager
            and self.account_manager[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.account_manager[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_trustee(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.trustee
            and self.trustee[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.trustee[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_authority(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.authority
            and self.authority[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.authority[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_primary_dealer(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.primary_dealer
            and self.primary_dealer[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.primary_dealer[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_valid_holding_address(self, holding_address: arc4.Address) -> None:
        assert holding_address in self.account, err.INVALID_HOLDING_ADDRESS

    @subroutine
    def assert_time_events_sorted(self, time_events: typ.TimeEvents) -> None:
        for _t in urange(time_events.length - 1):
            ensure_budget(
                required_budget=UInt64(cfg.OP_UP_TIME_EVENT_SORTING),
                fee_source=OpUpFeeSource.AppAccount,  # App funds are not at risk since caller is trusted
            )
            time_i = time_events[_t].native
            time_f = time_events[_t + 1].native
            assert time_f > time_i, err.INVALID_SORTING
            if self.day_count_convention != UInt64(cst.DCC_CONT):
                # The reference implementation requires time periods expressed in days for regular day-count conventions
                assert (time_f - time_i) % UInt64(
                    cst.DAY_2_SEC
                ) == 0, err.INVALID_TIME_PERIOD

    @subroutine
    def assert_is_primary_distribution_open(self) -> None:
        assert (
            self.status_is_active()
            and self.primary_distribution_opening_date
            <= Global.latest_timestamp
            < self.primary_distribution_closure_date
        ), err.PRIMARY_DISTRIBUTION_CLOSED

    @subroutine
    def assert_is_secondary_market_open(self) -> None:
        assert (
            self.status_is_active()
            and self.secondary_market_opening_date
            <= Global.latest_timestamp
            < self.secondary_market_closure_date
        ), err.SECONDARY_MARKET_CLOSED

    @subroutine
    def assert_are_units_fungible(
        self, sender: arc4.Address, receiver: arc4.Address
    ) -> None:
        assert (
            self.account[sender].unit_value == self.account[receiver].unit_value
            and self.account[sender].paid_coupons == self.account[receiver].paid_coupons
        ), err.NON_FUNGIBLE_UNITS

    @subroutine
    def opt_in_denomination_asset(self) -> None:
        itxn.AssetTransfer(
            xfer_asset=self.denomination_asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=Global.min_txn_fee,
        ).submit()

    @subroutine
    def is_payment_executable(self, holding_address: arc4.Address) -> bool:
        return (
            self.account[holding_address].payment_address.native.is_opted_in(
                Asset(self.denomination_asset_id)
            )
            and not self.account[holding_address].suspended.native
        )

    @subroutine
    def pay(self, receiver: arc4.Address, amount: UInt64) -> None:
        itxn.AssetTransfer(
            xfer_asset=self.denomination_asset_id,
            asset_receiver=receiver.native,
            asset_amount=amount,
            fee=Global.min_txn_fee,
        ).submit()

    @subroutine
    def account_units_value(
        self, holding_address: arc4.Address, units: UInt64
    ) -> UInt64:
        return units * self.account[holding_address].unit_value.native

    @subroutine
    def account_total_units_value(self, holding_address: arc4.Address) -> UInt64:
        return self.account_units_value(
            holding_address, self.account[holding_address].units.native
        )

    @subroutine
    def set_time_events(self, time_events: typ.TimeEvents) -> None:
        self.time_events.value = time_events.copy()
        self.primary_distribution_opening_date = time_events[
            cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX
        ].native
        self.primary_distribution_closure_date = time_events[
            cfg.PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX
        ].native
        self.issuance_date = time_events[cfg.ISSUANCE_DATE_IDX].native
        self.maturity_date = time_events[cfg.MATURITY_DATE_IDX].native

    @subroutine
    def days_in(self, time_period: UInt64) -> UInt64:
        return time_period // UInt64(cst.DAY_2_SEC)

    @subroutine
    def reset_account_if_zero_units(self, holding_address: arc4.Address) -> None:
        if self.account[holding_address].units.native == 0:
            self.account[holding_address].unit_value = arc4.UInt64()
            self.account[holding_address].paid_coupons = arc4.UInt64()

    @subroutine
    def end_if_no_circulating_units(self) -> None:
        if self.circulating_units == 0:
            self.status = UInt64(cfg.STATUS_ENDED)

    @subroutine
    def assert_asset_transfer_authorization(
        self,
        sender_holding_address: arc4.Address,
        receiver_holding_address: arc4.Address,
        units: UInt64,
    ) -> None:
        # The reference implementation grants transfer right to D-ASA owners. Other implementations may relay on other roles,
        # external Apps through C2C calls (e.g., an order book), or off-chain transfer agents.
        assert Txn.sender == sender_holding_address.native, err.UNAUTHORIZED
        self.assert_is_not_defaulted()
        self.assert_is_not_suspended()
        self.assert_valid_holding_address(sender_holding_address)
        self.assert_valid_holding_address(receiver_holding_address)
        assert not self.account[sender_holding_address].suspended.native, err.SUSPENDED
        assert not self.account[
            receiver_holding_address
        ].suspended.native, err.SUSPENDED
        assert (
            units <= self.account[sender_holding_address].units.native
        ), err.OVER_TRANSFER

    @subroutine
    def assert_transferred_units_fungibility(
        self,
        sender_holding_address: arc4.Address,
        receiver_holding_address: arc4.Address,
    ) -> None:
        sender_unit_value = self.account[sender_holding_address].unit_value
        if self.account[receiver_holding_address].units.native > 0:
            self.assert_are_units_fungible(
                sender_holding_address, receiver_holding_address
            )
        else:
            self.account[receiver_holding_address].unit_value = sender_unit_value
            self.account[receiver_holding_address].paid_coupons = self.account[
                sender_holding_address
            ].paid_coupons

    @subroutine
    def assert_asset_transfer_preconditions(
        self,
        sender_holding_address: arc4.Address,
        receiver_holding_address: arc4.Address,
        units: UInt64,
    ) -> None:
        self.assert_is_secondary_market_open()
        self.assert_asset_transfer_authorization(
            sender_holding_address,
            receiver_holding_address,
            units,
        )
        self.assert_transferred_units_fungibility(
            sender_holding_address,
            receiver_holding_address,
        )

    @subroutine
    def transfer_units(
        self,
        sender_holding_address: arc4.Address,
        receiver_holding_address: arc4.Address,
        units: UInt64,
    ) -> None:
        self.account[sender_holding_address].units = arc4.UInt64(
            self.account[sender_holding_address].units.native - units
        )
        self.account[receiver_holding_address].units = arc4.UInt64(
            self.account[receiver_holding_address].units.native + units
        )
        self.reset_account_if_zero_units(sender_holding_address)

    @subroutine
    def assert_pay_principal_authorization(self, holding_address: arc4.Address) -> None:
        # The reference implementation does not restrict caller authorization
        assert self.status_is_active(), err.UNAUTHORIZED
        self.assert_is_not_defaulted()
        self.assert_is_not_suspended()
        self.assert_valid_holding_address(holding_address)
        units = self.account[holding_address].units.native
        assert units > 0, err.NO_UNITS
        assert Global.latest_timestamp >= self.maturity_date, err.NOT_MATURE
        # The reference implementation does not assert if there is enough liquidity to repay the principal to all

    @subroutine
    def update_supply_after_principal_payment(
        self, holding_address: arc4.Address
    ) -> None:
        self.circulating_units -= self.account[holding_address].units.native
        self.account[holding_address].units = arc4.UInt64()
        self.end_if_no_circulating_units()

    @arc4.abimethod(create="require")
    def asset_create(self, arranger: arc4.Address, metadata: typ.AssetMetadata) -> None:
        """
        Create a new D-ASA

        Args:
            arranger: D-ASA Arranger Address
            metadata: D-ASA metadata digest (e.g. prospectus digest)
        """
        self.arranger = arranger.native
        self.metadata = metadata.native

    @arc4.baremethod(allow_actions=["UpdateApplication"])
    def asset_update(self) -> None:
        """
        Update D-ASA application.
        """
        # The reference implementation grants the update permissions to the Arranger.
        # Other implementations may disable D-ASA application updatability or change its authorizations.
        # ⚠️ WARNING: Application updates must be executed VERY carefully, as they might introduce breaking changes.
        self.assert_caller_is_arranger()

    @arc4.abimethod
    def asset_config(
        self,
        denomination_asset_id: arc4.UInt64,
        principal: arc4.UInt64,
        minimum_denomination: arc4.UInt64,
        day_count_convention: arc4.UInt8,
        interest_rate: arc4.UInt16,
        coupon_rates: typ.CouponRates,
        time_events: typ.TimeEvents,
        time_periods: typ.TimePeriods,
    ) -> None:
        """
        Configure the Debt Algorand Standard Asset

        Args:
            denomination_asset_id: Denomination asset identifier
            principal: Principal, expressed in denomination asset
            minimum_denomination: Minimum denomination, expressed in denomination asset
            day_count_convention: Day-count convention for interests calculation
            interest_rate: Interest rate in bps
            coupon_rates: Coupon interest rates in bps
            time_events: Time events (strictly ascending order)
            time_periods: Time periods of recurring time events

        Raises:
            UNAUTHORIZED: Not authorized
            ALREADY_CONFIGURED: D-ASA already configured
            INVALID_MINIMUM_DENOMINATION: Minimum denomination is not a divisor of principal
            INVALID_DAY_COUNT_CONVENTION: Invalid day-count convention ID
            INVALID_TIME_EVENTS_LENGTH: Time events length is invalid
            INVALID_TIME: Time events must be set in the future
            INVALID_SORTING: Time events are not sorted correctly
        """
        self.assert_caller_is_arranger()
        assert self.status == cfg.STATUS_EMPTY, err.ALREADY_CONFIGURED

        self.denomination_asset_id = denomination_asset_id.native
        # The reference implementation has on-chain payment agent
        self.opt_in_denomination_asset()

        assert (
            principal.native % minimum_denomination.native == 0
        ), err.INVALID_MINIMUM_DENOMINATION
        self.unit_value = minimum_denomination.native
        self.total_units = principal.native // minimum_denomination.native

        # The reference implementation supports only the Actual/Actual and Continuous day-count conventions
        assert day_count_convention.native in (
            UInt64(cst.DCC_A_A),
            UInt64(cst.DCC_CONT),
        ), err.INVALID_DAY_COUNT_CONVENTION
        self.day_count_convention = day_count_convention.native

        # Set Interest Rate
        self.interest_rate = interest_rate.native

        # Set Coupons
        self.total_coupons = coupon_rates.length
        self.coupon_rates.value = coupon_rates.copy()

        # Set Time Events
        assert (
            time_events.length == self.total_coupons + cfg.TIME_SCHEDULE_LIMITS
        ), err.INVALID_TIME_EVENTS_LENGTH
        assert (
            time_events[cfg.PRIMARY_DISTRIBUTION_OPENING_DATE_IDX].native
            > Global.latest_timestamp
        ), err.INVALID_TIME
        self.assert_time_events_sorted(time_events)
        self.set_time_events(time_events)

        # Set Time Periods
        # The reference implementation does not use time periods
        assert not time_periods.length

        self.status = UInt64(cfg.STATUS_ACTIVE)

    @arc4.abimethod
    def set_secondary_time_events(
        self, secondary_market_time_events: typ.TimeEvents
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
        self.assert_is_not_defaulted()

        assert secondary_market_time_events.length == UInt64(
            cfg.SECONDARY_MARKET_SCHEDULE_LIMITS
        ), err.INVALID_TIME_EVENTS_LENGTH
        self.assert_time_events_sorted(secondary_market_time_events)
        assert (
            self.issuance_date
            <= secondary_market_time_events[
                cfg.SECONDARY_MARKET_OPENING_DATE_IDX
            ].native
        ), err.INVALID_SECONDARY_OPENING_DATE
        assert (
            self.maturity_date
            >= secondary_market_time_events[
                cfg.SECONDARY_MARKET_CLOSURE_DATE_IDX
            ].native
        ), err.INVALID_SECONDARY_CLOSURE_DATE

        self.secondary_market_opening_date = secondary_market_time_events[
            cfg.SECONDARY_MARKET_OPENING_DATE_IDX
        ].native
        self.secondary_market_closure_date = secondary_market_time_events[
            cfg.SECONDARY_MARKET_CLOSURE_DATE_IDX
        ].native
        return typ.SecondaryMarketSchedule(
            secondary_market_opening_date=arc4.UInt64(
                self.secondary_market_opening_date
            ),
            secondary_market_closure_date=arc4.UInt64(
                self.secondary_market_closure_date
            ),
        )

    @arc4.abimethod
    def assign_role(
        self, role_address: arc4.Address, role: arc4.UInt8, config: arc4.DynamicBytes
    ) -> arc4.UInt64:
        """
        Assign a role to an address

        Args:
            role_address: Account Role Address
            role: Role identifier
            config: Role configuration (Optional)

        Returns:
            Timestamp of the role assignment

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_ROLE: Invalid role identifier
            INVALID_ROLE_ADDRESS: Invalid account role address
        """
        self.assert_caller_is_arranger()
        self.assert_is_not_defaulted()
        assert role.native in (
            UInt64(cst.ROLE_ARRANGER),
            UInt64(cst.ROLE_ACCOUNT_MANAGER),
            UInt64(cst.ROLE_PRIMARY_DEALER),
            UInt64(cst.ROLE_TRUSTEE),
            UInt64(cst.ROLE_AUTHORITY),
        ), err.INVALID_ROLE
        match role.native:
            case UInt64(cst.ROLE_ARRANGER):
                self.arranger = role_address.native
            case UInt64(cst.ROLE_ACCOUNT_MANAGER):
                assert (
                    role_address not in self.account_manager
                ), err.INVALID_ROLE_ADDRESS
                self.account_manager[role_address] = typ.RoleConfig.from_bytes(
                    config.native
                )
            case UInt64(cst.ROLE_PRIMARY_DEALER):
                assert role_address not in self.primary_dealer, err.INVALID_ROLE_ADDRESS
                self.primary_dealer[role_address] = typ.RoleConfig.from_bytes(
                    config.native
                )
            case UInt64(cst.ROLE_TRUSTEE):
                assert role_address not in self.trustee, err.INVALID_ROLE_ADDRESS
                self.trustee[role_address] = typ.RoleConfig.from_bytes(config.native)
            case UInt64(cst.ROLE_AUTHORITY):
                assert role_address not in self.authority, err.INVALID_ROLE_ADDRESS
                self.authority[role_address] = typ.RoleConfig.from_bytes(config.native)
            case _:
                op.err()
        return arc4.UInt64(Global.latest_timestamp)

    @arc4.abimethod
    def revoke_role(self, role_address: arc4.Address, role: arc4.UInt8) -> arc4.UInt64:
        """
        Revoke a role from an address

        Args:
            role_address: Account Role Address
            role: Role identifier

        Returns:
            Timestamp of the role revocation

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_ROLE: Invalid role identifier
            INVALID_ROLE_ADDRESS: Invalid account role address
        """
        self.assert_caller_is_arranger()
        self.assert_is_not_defaulted()
        assert role.native in (
            UInt64(cst.ROLE_ACCOUNT_MANAGER),
            UInt64(cst.ROLE_PRIMARY_DEALER),
            UInt64(cst.ROLE_TRUSTEE),
            UInt64(cst.ROLE_AUTHORITY),
        ), err.INVALID_ROLE
        match role.native:
            # Arranger role can not be revoked (just rotated)
            case UInt64(cst.ROLE_ACCOUNT_MANAGER):
                assert role_address in self.account_manager, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_BOX_ID_ACCOUNT_MANAGER + role_address.bytes)
            case UInt64(cst.ROLE_PRIMARY_DEALER):
                assert role_address in self.primary_dealer, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_BOX_ID_PRIMARY_DEALER + role_address.bytes)
            case UInt64(cst.ROLE_TRUSTEE):
                assert role_address in self.trustee, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_BOX_ID_TRUSTEE + role_address.bytes)
            case UInt64(cst.ROLE_AUTHORITY):
                assert role_address in self.authority, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_BOX_ID_AUTHORITY + role_address.bytes)
            case _:
                op.err()
        return arc4.UInt64(Global.latest_timestamp)

    @arc4.abimethod
    def open_account(
        self, holding_address: arc4.Address, payment_address: arc4.Address
    ) -> arc4.UInt64:
        """
        Open D-ASA account

        Args:
            holding_address: Account Holding Address
            payment_address: Account Payment Address

        Returns:
            Timestamp of the account opening

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_caller_is_account_manager()
        assert not self.status_is_ended(), err.UNAUTHORIZED
        self.assert_is_not_defaulted()
        self.assert_is_not_suspended()
        assert holding_address not in self.account, err.INVALID_HOLDING_ADDRESS

        self.account[holding_address] = typ.AccountInfo(
            payment_address=payment_address,
            units=arc4.UInt64(),
            unit_value=arc4.UInt64(),
            paid_coupons=arc4.UInt64(),
            suspended=arc4.Bool(),
        )
        return arc4.UInt64(Global.latest_timestamp)

    @arc4.abimethod
    def close_account(
        self, holding_address: arc4.Address
    ) -> arc4.Tuple[arc4.UInt64, arc4.UInt64]:
        """
        Close D-ASA account

        Args:
            holding_address: Account Holding Address

        Returns:
            Closed units, Timestamp of the account closing

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_caller_is_account_manager()
        self.assert_is_not_defaulted()
        self.assert_valid_holding_address(holding_address)

        closed_units = self.account[holding_address].units.native
        op.Box.delete(cst.PREFIX_BOX_ID_ACCOUNT + holding_address.bytes)
        self.circulating_units -= closed_units
        self.end_if_no_circulating_units()
        return arc4.Tuple(
            (arc4.UInt64(closed_units), arc4.UInt64(Global.latest_timestamp))
        )

    @arc4.abimethod
    def primary_distribution(
        self, holding_address: arc4.Address, units: arc4.UInt64
    ) -> arc4.UInt64:
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
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
            ZERO_UNITS: Can not distribute zero units
            OVER_DISTRIBUTION: Insufficient remaining D-ASA units
            PRIMARY_DISTRIBUTION_CLOSED: Primary distribution is closed
        """
        self.assert_is_primary_distribution_open()
        # The reference implementation grants primary distribution permissions to the Primary Dealer role. Other
        # implementations may relay on other roles or external Apps through C2C calls (e.g., an auction).
        self.assert_caller_is_primary_dealer()
        self.assert_valid_holding_address(holding_address)
        self.assert_is_not_defaulted()
        self.assert_is_not_suspended()
        assert units.native > 0, err.ZERO_UNITS
        assert (
            self.circulating_units + units.native <= self.total_units
        ), err.OVER_DISTRIBUTION

        self.circulating_units += units.native
        self.account[holding_address].units = arc4.UInt64(
            self.account[holding_address].units.native + units.native
        )
        self.account[holding_address].unit_value = arc4.UInt64(self.unit_value)
        return arc4.UInt64(self.total_units - self.circulating_units)

    @arc4.abimethod
    def set_asset_suspension(self, suspended: arc4.Bool) -> arc4.UInt64:
        """
        Set asset suspension status

        Args:
            suspended: Suspension status

        Returns:
            Timestamp of the set asset suspension status

        Raises:
            UNAUTHORIZED: Not authorized
        """
        self.assert_caller_is_authority()
        self.suspended = UInt64(suspended.native)
        return arc4.UInt64(Global.latest_timestamp)

    @arc4.abimethod
    def set_account_suspension(
        self, holding_address: arc4.Address, suspended: arc4.Bool
    ) -> arc4.UInt64:
        """
        Set account suspension status

        Args:
            holding_address: Account Holding Address
            suspended: Suspension status

        Returns:
            Timestamp of the set account suspension status

        Raises:
            UNAUTHORIZED: Not authorized
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_caller_is_authority()
        self.assert_valid_holding_address(holding_address)
        self.account[holding_address].suspended = suspended
        return arc4.UInt64(Global.latest_timestamp)

    @arc4.abimethod
    def set_default_status(self, defaulted: arc4.Bool) -> None:
        """
        Set D-ASA default status

        Args:
            defaulted: Default status

        Raises:
            UNAUTHORIZED: Not authorized
        """
        self.assert_caller_is_trustee()
        self.defaulted = UInt64(defaulted.native)

    @arc4.abimethod(readonly=True)
    def get_asset_info(self) -> typ.AssetInfo:
        """
        Get D-ASA info

        Returns:
            Denomination Asset ID, Outstanding principal, Unit nominal value, Day-count convention, Interest rate, Total
            supply, Circulating supply, Primary Distribution Opening Date, Primary Distribution Closure Date, Issuance
            Date, Maturity Date, Suspended, Defaulted
        """
        return typ.AssetInfo(
            denomination_asset_id=arc4.UInt64(self.denomination_asset_id),
            outstanding_principal=arc4.UInt64(self.circulating_units * self.unit_value),
            unit_value=arc4.UInt64(self.unit_value),
            day_count_convention=arc4.UInt8(self.day_count_convention),
            interest_rate=arc4.UInt16(self.interest_rate),
            total_supply=arc4.UInt64(self.total_units),
            circulating_supply=arc4.UInt64(self.circulating_units),
            primary_distribution_opening_date=arc4.UInt64(
                self.primary_distribution_opening_date
            ),
            primary_distribution_closure_date=arc4.UInt64(
                self.primary_distribution_closure_date
            ),
            issuance_date=arc4.UInt64(self.issuance_date),
            maturity_date=arc4.UInt64(self.maturity_date),
            suspended=arc4.Bool(bool(self.suspended)),
            defaulted=arc4.Bool(bool(self.defaulted)),
        )

    @arc4.abimethod(readonly=True)
    def get_account_info(self, holding_address: arc4.Address) -> typ.AccountInfo:
        """
        Get account info

        Args:
            holding_address: Account Holding Address

        Returns:
            Payment Address, D-ASA units, Unit value, Paid coupons, Suspended

        Raises:
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_valid_holding_address(holding_address)
        return self.account[holding_address]

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
        return typ.TimeEvents(
            arc4.UInt64(self.secondary_market_opening_date),
            arc4.UInt64(self.secondary_market_closure_date),
        )

    @arc4.abimethod(readonly=True)
    def get_asset_metadata(self) -> typ.AssetMetadata:
        return typ.AssetMetadata(self.metadata)
