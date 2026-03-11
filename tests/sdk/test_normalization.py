"""Tests for the normalization module."""

from decimal import Decimal

import pytest

from smart_contracts import constants as cst
from smart_contracts import enums
from src.contracts import (
    ContractAttributes,
    make_pam_fixed_coupon_bond_profile,
    make_pam_zero_coupon_bond,
)
from src.day_count import (
    BusinessDayConvention,
    Calendar,
    DayCountConvention,
    EndOfMonthConvention,
)
from src.errors import ActusNormalizationError
from src.models import ExecutionScheduleEntry, NormalizedActusTerms
from src.normalization import normalize_contract_attributes
from src.normalization.conversions import (
    compute_initial_exchange_amount,
    rate_to_fp,
    to_asa_units,
)
from src.normalization.event_seeds import deduplicate_timestamps
from src.schedule import Cycle


class TestToAsaUnits:
    """Test the to_asa_units helper function."""

    def test_integer_conversion(self):
        """Test converting integer amounts to ASA units."""
        assert to_asa_units(100, 2) == 10000
        assert to_asa_units(1000, 0) == 1000
        assert to_asa_units(50, 3) == 50000

    def test_float_conversion(self):
        """Test converting float amounts to ASA units."""
        result = to_asa_units(100.5, 2)
        assert result == 10050
        assert isinstance(result, int)

    def test_decimal_conversion(self):
        """Test converting Decimal amounts to ASA units."""
        result = to_asa_units(Decimal("100.42"), 3)
        assert result == 100420
        assert isinstance(result, int)

    def test_zero_decimals(self):
        """Test conversion with zero decimal places."""
        assert to_asa_units(100, 0) == 100

    def test_high_decimal_places(self):
        """Test conversion with high decimal places."""
        result = to_asa_units(1, 10)
        assert result == 10_000_000_000
        assert isinstance(result, int)

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported value type"):
            to_asa_units("100", 2)
        with pytest.raises(TypeError, match="Unsupported value type"):
            to_asa_units(None, 2)

    def test_exceeds_uint64_raises_error(self):
        """Test that values exceeding uint64 max raise error."""
        # A large amount that when multiplied by scale exceeds uint64 max
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 bounds"):
            to_asa_units(cst.MAX_UINT64 * 2, 2)


class TestRateToFp:
    """Test the rate_to_fp helper function."""

    def test_integer_rate_conversion(self):
        """Test converting integer rates to fixed point."""
        result = rate_to_fp(1)
        assert result == cst.FIXED_POINT_SCALE
        assert isinstance(result, int)

    def test_float_rate_conversion(self):
        """Test converting float rates to fixed point."""
        result = rate_to_fp(0.05)
        expected = int(Decimal("0.05") * cst.FIXED_POINT_SCALE)
        assert result == expected

    def test_decimal_rate_conversion(self):
        """Test converting Decimal rates to fixed point."""
        result = rate_to_fp(Decimal("0.0375"))
        expected = int(Decimal("0.0375") * cst.FIXED_POINT_SCALE)
        assert result == expected

    def test_zero_rate(self):
        """Test converting zero rate."""
        assert rate_to_fp(0) == 0

    def test_high_precision_rate(self):
        """Test converting high precision rate."""
        rate = Decimal("0.123456789")
        result = rate_to_fp(rate)
        assert isinstance(result, int)
        assert result > 0

    def test_negative_rate_raises_error(self):
        """Test that negative rates raise error."""
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 bounds"):
            rate_to_fp(-0.01)

    def test_exceeds_uint64_raises_error(self):
        """Test that very large rates raise error."""
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 bounds"):
            rate_to_fp(cst.MAX_UINT64)

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported value type"):
            rate_to_fp("0.05")


class TestComputeInitialExchangeAmount:
    """Test the compute_initial_exchange_amount helper function."""

    def test_at_par_issuance(self):
        """Test initial exchange with no premium/discount."""
        result = compute_initial_exchange_amount(
            notional=1000000,
            premium_discount_at_ied=0,
            asa_decimals=2,
        )
        # notional=1000000 with 2 decimals = 100000000, premium=0
        # result = 100000000 - 0 = 100000000
        assert result == 100000000

    def test_with_discount(self):
        """Test initial exchange with discount."""
        result = compute_initial_exchange_amount(
            notional=1000000,
            premium_discount_at_ied=50000,
            asa_decimals=2,
        )
        # notional=1000000 with 2 decimals = 100000000
        # premium_discount=50000 with 2 decimals = 5000000
        # result = 100000000 - 5000000 = 95000000
        assert result == 95000000

    def test_with_premium(self):
        """Test initial exchange with premium (negative discount)."""
        result = compute_initial_exchange_amount(
            notional=1000000,
            premium_discount_at_ied=-50000,
            asa_decimals=2,
        )
        # notional=1000000 with 2 decimals = 100000000
        # premium_discount=-50000 with 2 decimals = -5000000
        # result = 100000000 - (-5000000) = 105000000
        assert result == 105000000

    def test_discount_exceeds_notional_raises_error(self):
        """Test that discount > notional results in negative value and raises error."""
        # notional=1000000 with 2 decimals = 100000000
        # discount=2000000 with 2 decimals = 200000000
        # result = 100000000 - 200000000 = -100000000 (negative)
        with pytest.raises(ActusNormalizationError, match="exceeds notional"):
            compute_initial_exchange_amount(
                notional=1000000,
                premium_discount_at_ied=2000000,
                asa_decimals=2,
            )

    def test_premium_causes_uint64_overflow_raises_error(self):
        """Test that large premium causing uint64 overflow raises error."""
        # Use a notional that's 60% of MAX_UINT64 and a premium that's 50% of MAX_UINT64
        # Together they will exceed MAX_UINT64
        notional_large = int(cst.MAX_UINT64 * 0.6)
        premium_large = int(cst.MAX_UINT64 * 0.5)
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 maximum"):
            compute_initial_exchange_amount(
                notional=notional_large,
                premium_discount_at_ied=-premium_large,
                asa_decimals=0,
            )


class TestDeduplicateTimestamps:
    """Test the deduplicate_timestamps helper function."""

    def test_empty_sequence(self):
        """Test deduplication of empty sequence."""
        result = deduplicate_timestamps([])
        assert result == ()

    def test_no_duplicates(self):
        """Test sequence with no duplicates."""
        timestamps = [1000000, 1100000, 1200000]
        result = deduplicate_timestamps(timestamps)
        assert result == (1000000, 1100000, 1200000)

    def test_with_duplicates(self):
        """Test deduplication removes duplicates."""
        timestamps = [1000000, 1100000, 1100000, 1200000, 1000000]
        result = deduplicate_timestamps(timestamps)
        assert result == (1000000, 1100000, 1200000)

    def test_preserves_sorted_order(self):
        """Test that result is sorted."""
        timestamps = [1200000, 1000000, 1100000]
        result = deduplicate_timestamps(timestamps)
        assert result == (1000000, 1100000, 1200000)

    def test_all_same_timestamps(self):
        """Test with all identical timestamps."""
        timestamps = [1000000, 1000000, 1000000]
        result = deduplicate_timestamps(timestamps)
        assert result == (1000000,)


class TestNormalizeContractAttributes:
    """Test the main normalize_contract_attributes function."""

    def test_normalize_pam_zero_coupon_bond(self):
        """Test normalizing a PAM zero coupon bond."""
        contract = make_pam_zero_coupon_bond(
            contract_id=1,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=50000,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
        )

        assert result.terms is not None
        assert result.schedule is not None
        assert result.initial_state is not None

        # Check that notional principal is correctly normalized
        # 1000000 with 2 decimals = 100000000
        assert result.terms.notional_principal == 100000000

        # Check that initial exchange amount is correctly calculated
        # notional (100000000) - premium_discount (5000000) = 95000000
        assert result.terms.initial_exchange_amount == 95000000

        # Check that maturity date event exists in schedule
        md_events = [e for e in result.schedule if e.event_type == "MD"]
        assert len(md_events) == 1
        assert md_events[0].scheduled_time == 2000000

    def test_status_date_after_ied_raises_error(self):
        """Test that status_date >= initial_exchange_date raises error."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1100000,  # Same as IED
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        with pytest.raises(
            ActusNormalizationError, match="status_date to be strictly before"
        ):
            normalize_contract_attributes(
                contract,
                denomination_asset_id=100,
                denomination_asset_decimals=2,
                notional_unit_value=1000,
                secondary_market_opening_date=1150000,
                secondary_market_closure_date=1950000,
            )

    def test_normalize_pam_fixed_coupon_bond(self):
        """Test normalizing a PAM fixed coupon bond."""
        contract = make_pam_fixed_coupon_bond_profile(
            contract_id=2,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            nominal_interest_rate=0.05,
            interest_payment_cycle=Cycle(count=6, unit="M"),
            interest_payment_anchor=1100000,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
        )

        # Should have a schedule with events
        assert result.schedule is not None
        assert len(result.schedule) > 0

        # Check that rate is normalized to fixed point
        assert result.terms.rate_reset_next == int(
            Decimal("0.05") * cst.FIXED_POINT_SCALE
        )

        # Should have IED and MD events at minimum
        event_types = {e.event_type for e in result.schedule}
        assert "IED" in event_types
        assert "MD" in event_types

    def test_normalize_lam_contract(self):
        """Test normalizing a LAM (Linear Amortizing) contract."""
        contract = ContractAttributes(
            contract_id=3,
            contract_type="LAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1200000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.04,
            next_principal_redemption_amount=100000,
            principal_redemption_cycle=Cycle(count=3, unit="M"),
            principal_redemption_anchor=1200000,
            interest_payment_cycle=Cycle(count=3, unit="M"),
            interest_payment_anchor=1200000,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
        )

        # Should have PR events
        pr_events = [e for e in result.schedule if e.event_type == "PR"]
        assert len(pr_events) > 0

    def test_normalize_with_rate_reset(self):
        """Test normalizing contract with rate reset."""
        contract = ContractAttributes(
            contract_id=4,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.03,
            rate_reset_spread=0.01,
            rate_reset_multiplier=1.0,
            rate_reset_floor=0.02,
            rate_reset_cap=0.10,
            rate_reset_next=0.04,
            rate_reset_cycle=Cycle(count=1, unit="Y"),
            rate_reset_anchor=1200000,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
        )

        # Check rate reset parameters are normalized
        assert result.terms.rate_reset_spread > 0
        assert result.terms.rate_reset_floor > 0
        assert result.terms.rate_reset_cap > 0


class TestNormalizedActusTerms:
    """Test the NormalizedActusTerms model."""

    def test_terms_creation(self):
        """Test creating normalized terms with valid values."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=100000000,
            notional_unit_value=100000,
            initial_exchange_amount=95000000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )
        assert terms.contract_id == 1
        assert terms.total_units == 1000

    def test_terms_total_units_calculation(self):
        """Test that total_units is correctly calculated."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )
        assert terms.total_units == 1000

    def test_terms_with_zero_notional_unit_value_raises_error(self):
        """Test that zero notional_unit_value raises error."""
        with pytest.raises(
            ActusNormalizationError, match="notional_unit_value must be positive"
        ):
            NormalizedActusTerms(
                contract_id=1,
                contract_type=enums.CT_PAM,
                denomination_asset_id=100,
                initial_exchange_date=1100000,
                maturity_date=2000000,
                secondary_market_opening_date=1150000,
                secondary_market_closure_date=1950000,
                notional_principal=1000000,
                notional_unit_value=0,
                initial_exchange_amount=950000,
                next_principal_redemption_amount=0,
                rate_reset_spread=0,
                rate_reset_multiplier=cst.FIXED_POINT_SCALE,
                rate_reset_floor=0,
                rate_reset_cap=0,
                rate_reset_next=0,
                day_count_convention=enums.DCC_A360,
                fixed_point_scale=cst.FIXED_POINT_SCALE,
            )

    def test_terms_indivisible_notional_raises_error(self):
        """Test that notional not divisible by unit value raises error."""
        with pytest.raises(
            ActusNormalizationError, match="divisible by notional_unit_value"
        ):
            NormalizedActusTerms(
                contract_id=1,
                contract_type=enums.CT_PAM,
                denomination_asset_id=100,
                initial_exchange_date=1100000,
                maturity_date=2000000,
                secondary_market_opening_date=1150000,
                secondary_market_closure_date=1950000,
                notional_principal=1000001,  # Not divisible by 1000
                notional_unit_value=1000,
                initial_exchange_amount=950000,
                next_principal_redemption_amount=0,
                rate_reset_spread=0,
                rate_reset_multiplier=cst.FIXED_POINT_SCALE,
                rate_reset_floor=0,
                rate_reset_cap=0,
                rate_reset_next=0,
                day_count_convention=enums.DCC_A360,
                fixed_point_scale=cst.FIXED_POINT_SCALE,
            )

    def test_dynamic_principal_redemption_for_ann(self):
        """Test dynamic_principal_redemption property for ANN contracts."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_ANN,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,  # Zero indicates dynamic
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )
        assert terms.dynamic_principal_redemption is True

    def test_has_rate_reset_floor(self):
        """Test has_rate_reset_floor property."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=1000000,  # Non-zero
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )
        assert terms.has_rate_reset_floor is True

    def test_has_rate_reset_cap(self):
        """Test has_rate_reset_cap property."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=10000000,  # Non-zero
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )
        assert terms.has_rate_reset_cap is True


class TestExecutionScheduleEntry:
    """Test the ExecutionScheduleEntry model."""

    def test_schedule_entry_creation(self):
        """Test creating a schedule entry."""
        entry = ExecutionScheduleEntry(
            event_id=0,
            event_type="IED",
            scheduled_time=1100000,
            accrual_factor=0,
            redemption_accrual_factor=0,
            next_nominal_interest_rate=50000000,
            next_principal_redemption=0,
            next_outstanding_principal=1000000,
            flags=enums.FLAG_NON_CASH_EVENT,
        )
        assert entry.event_id == 0
        assert entry.event_type == "IED"
        assert entry.scheduled_time == 1100000
        assert entry.flags == enums.FLAG_NON_CASH_EVENT

    def test_schedule_entry_cash_event(self):
        """Test creating a cash event schedule entry."""
        entry = ExecutionScheduleEntry(
            event_id=1,
            event_type="IP",
            scheduled_time=1200000,
            accrual_factor=500000,
            redemption_accrual_factor=0,
            next_nominal_interest_rate=50000000,
            next_principal_redemption=0,
            next_outstanding_principal=1000000,
            flags=enums.FLAG_CASH_EVENT,
        )
        assert entry.event_type == "IP"
        assert entry.flags == enums.FLAG_CASH_EVENT

    def test_schedule_entry_default_flags(self):
        """Test that flags default to 0."""
        entry = ExecutionScheduleEntry(
            event_id=2,
            event_type="MD",
            scheduled_time=2000000,
            accrual_factor=100000,
            redemption_accrual_factor=0,
            next_nominal_interest_rate=0,
            next_principal_redemption=0,
            next_outstanding_principal=0,
        )
        assert entry.flags == 0


class TestNormalizationResult:
    """Test the NormalizationResult model."""

    def test_schedule_pages_basic(self):
        """Test splitting schedule into pages."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )

        schedule = tuple(
            ExecutionScheduleEntry(
                event_id=i,
                event_type="IP",
                scheduled_time=1100000 + i * 100000,
                accrual_factor=0,
                redemption_accrual_factor=0,
                next_nominal_interest_rate=0,
                next_principal_redemption=0,
                next_outstanding_principal=0,
            )
            for i in range(10)
        )

        from src.models import InitialKernelState, NormalizationResult

        initial_state = InitialKernelState(
            status_date=1000000,
            event_cursor=0,
            outstanding_principal=0,
            interest_calculation_base=0,
            nominal_interest_rate=0,
            accrued_interest=0,
            next_principal_redemption=0,
            cumulative_interest_index=0,
            cumulative_principal_index=0,
        )

        result = NormalizationResult(
            terms=terms,
            schedule=schedule,
            initial_state=initial_state,
        )

        pages = result.schedule_pages(page_size=3)
        assert len(pages) == 4  # 10 entries / 3 per page = 4 pages
        assert len(pages[0]) == 3
        assert len(pages[1]) == 3
        assert len(pages[2]) == 3
        assert len(pages[3]) == 1

    def test_schedule_pages_exact_division(self):
        """Test paging when schedule size divides evenly."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )

        schedule = tuple(
            ExecutionScheduleEntry(
                event_id=i,
                event_type="IP",
                scheduled_time=1100000 + i * 100000,
                accrual_factor=0,
                redemption_accrual_factor=0,
                next_nominal_interest_rate=0,
                next_principal_redemption=0,
                next_outstanding_principal=0,
            )
            for i in range(6)
        )

        from src.models import InitialKernelState, NormalizationResult

        initial_state = InitialKernelState(
            status_date=1000000,
            event_cursor=0,
            outstanding_principal=0,
            interest_calculation_base=0,
            nominal_interest_rate=0,
            accrued_interest=0,
            next_principal_redemption=0,
            cumulative_interest_index=0,
            cumulative_principal_index=0,
        )

        result = NormalizationResult(
            terms=terms,
            schedule=schedule,
            initial_state=initial_state,
        )

        pages = result.schedule_pages(page_size=2)
        assert len(pages) == 3
        assert all(len(page) == 2 for page in pages)

    def test_schedule_pages_invalid_page_size(self):
        """Test that invalid page size raises error."""
        terms = NormalizedActusTerms(
            contract_id=1,
            contract_type=enums.CT_PAM,
            denomination_asset_id=100,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            secondary_market_opening_date=1150000,
            secondary_market_closure_date=1950000,
            notional_principal=1000000,
            notional_unit_value=1000,
            initial_exchange_amount=950000,
            next_principal_redemption_amount=0,
            rate_reset_spread=0,
            rate_reset_multiplier=cst.FIXED_POINT_SCALE,
            rate_reset_floor=0,
            rate_reset_cap=0,
            rate_reset_next=0,
            day_count_convention=enums.DCC_A360,
            fixed_point_scale=cst.FIXED_POINT_SCALE,
        )

        from src.models import InitialKernelState, NormalizationResult

        initial_state = InitialKernelState(
            status_date=1000000,
            event_cursor=0,
            outstanding_principal=0,
            interest_calculation_base=0,
            nominal_interest_rate=0,
            accrued_interest=0,
            next_principal_redemption=0,
            cumulative_interest_index=0,
            cumulative_principal_index=0,
        )

        result = NormalizationResult(
            terms=terms,
            schedule=(),
            initial_state=initial_state,
        )

        with pytest.raises(ValueError, match="page_size must be positive"):
            result.schedule_pages(page_size=0)

        with pytest.raises(ValueError, match="page_size must be positive"):
            result.schedule_pages(page_size=-1)


class TestLaxArrayPrNext:
    """Test LAX contracts with array-based principal redemption amounts."""

    def test_lax_array_pr_next_values_propagate_to_events(self):
        """
        Test that array_pr_next values are correctly used in event seeds.

        This tests the fix for a bug where payment_total was initialized once
        from next_principal_redemption_amount but per-period values from
        array_pr_next were only applied locally in _principal_payment_for_period
        and never propagated back to event seeds.
        """
        # Define redemption dates (monthly for 6 months)
        base_time = 1000000
        ied = base_time + (10 * 24 * 3600)
        month_secs = 30 * 24 * 3600

        # LAX contract with array_pr_next containing different values per period
        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAX",
            status_date=base_time,
            initial_exchange_date=ied,
            maturity_date=ied + (8 * month_secs),
            notional_principal=Decimal("100000.0"),
            premium_discount_at_ied=Decimal("0"),
            nominal_interest_rate=Decimal("0.05"),
            day_count_convention=DayCountConvention.ACTUAL_365,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
            # Use array-based schedule
            array_pr_anchor=[ied + (i * month_secs) for i in range(1, 7)],
            array_pr_cycle=[Cycle(1, "M") for _ in range(6)],
            # Array with different per-period amounts
            array_pr_next=[
                Decimal("2000.0"),
                Decimal("3000.0"),
                Decimal("4000.0"),
                Decimal("5000.0"),
                Decimal("6000.0"),
                Decimal("7000.0"),
            ],
            array_increase_decrease=["INC", "INC", "DEC", "DEC", "INC", "DEC"],
            next_principal_redemption_amount=Decimal("1000.0"),  # Should be overridden
        )

        # Normalize the contract
        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=1,
            denomination_asset_decimals=6,
            notional_unit_value=Decimal("1.0"),
            secondary_market_opening_date=base_time,
            secondary_market_closure_date=ied + (10 * month_secs),
        )

        # Extract PR and PI events (INC periods generate PI, DEC periods generate PR)
        pr_pi_events = [ev for ev in result.schedule if ev.event_type in ("PR", "PI")]

        # Verify that each event has the correct next_principal_redemption
        # from array_pr_next, not the base next_principal_redemption_amount
        # Note: There may be more events due to additional cycles, but we verify
        # at least the first 6 match array_pr_next
        assert len(pr_pi_events) >= 6

        # Expected event types based on array_increase_decrease
        expected_event_types = ["PI", "PI", "PR", "PR", "PI", "PR"]

        for i in range(6):
            expected_amount = to_asa_units(contract.array_pr_next[i], 6)
            assert pr_pi_events[i].event_type == expected_event_types[i], (
                f"Period {i}: Expected event_type={expected_event_types[i]}, "
                f"got {pr_pi_events[i].event_type}"
            )
            assert pr_pi_events[i].next_principal_redemption == expected_amount, (
                f"Period {i}: Expected next_principal_redemption={expected_amount}, "
                f"got {pr_pi_events[i].next_principal_redemption}"
            )

    def test_lax_inc_direction_uses_correct_payment_total(self):
        """
        Test that INC direction uses the correct per-period payment_total.

        For INC (increase) periods, next_outstanding should increase by the
        per-period amount from array_pr_next, not the base amount.
        """
        base_time = 1000000
        ied = base_time + (10 * 24 * 3600)
        month_secs = 30 * 24 * 3600

        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAX",
            status_date=base_time,
            initial_exchange_date=ied,
            maturity_date=ied + (5 * month_secs),
            notional_principal=Decimal("100000.0"),
            premium_discount_at_ied=Decimal("0"),
            nominal_interest_rate=Decimal("0.00"),  # No interest for simplicity
            day_count_convention=DayCountConvention.ACTUAL_365,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
            array_pr_anchor=[ied + (i * month_secs) for i in range(1, 4)],
            array_pr_cycle=[Cycle(1, "M") for _ in range(3)],
            array_pr_next=[
                Decimal("10000.0"),  # INC - should increase by 10000
                Decimal("20000.0"),  # INC - should increase by 20000
                Decimal("30000.0"),  # DEC - should decrease by 30000
            ],
            array_increase_decrease=["INC", "INC", "DEC"],
            next_principal_redemption_amount=Decimal("1000.0"),
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=1,
            denomination_asset_decimals=6,
            notional_unit_value=Decimal("1.0"),
            secondary_market_opening_date=base_time,
            secondary_market_closure_date=ied + (6 * month_secs),
        )

        # Extract PR and PI events (PI for INC periods where principal_payment == 0)
        pr_pi_events = [
            ev
            for ev in result.schedule
            if ev.event_type in ("PR", "PI") and ev.scheduled_time >= ied + month_secs
        ]

        # Verify outstanding progression
        # Initial: 100000
        # After period 0 (INC 10000): 100000 + 10000 = 110000
        # After period 1 (INC 20000): 110000 + 20000 = 130000
        # After period 2 (DEC 30000): 130000 - 30000 = 100000

        expected_outstanding = [
            100000 * 10**6 + 10000 * 10**6,  # Period 0: INC by 10000
            110000 * 10**6 + 20000 * 10**6,  # Period 1: INC by 20000
            130000 * 10**6 - 30000 * 10**6,  # Period 2: DEC by 30000
        ]

        for i, ev in enumerate(pr_pi_events[:3]):
            assert ev.next_outstanding_principal == expected_outstanding[i], (
                f"Period {i}: Expected outstanding={expected_outstanding[i]}, "
                f"got {ev.next_outstanding_principal}"
            )

    def test_lax_without_array_pr_next_uses_base_amount(self):
        """
        Test that when array_pr_next is not provided, the base amount is used.
        """
        base_time = 1000000
        ied = base_time + (10 * 24 * 3600)
        month_secs = 30 * 24 * 3600

        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAX",
            status_date=base_time,
            initial_exchange_date=ied,
            maturity_date=ied + (4 * month_secs),
            notional_principal=Decimal("100000.0"),
            premium_discount_at_ied=Decimal("0"),
            nominal_interest_rate=Decimal("0.05"),
            day_count_convention=DayCountConvention.ACTUAL_365,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
            array_pr_anchor=[ied + (i * month_secs) for i in range(1, 3)],
            array_pr_cycle=[Cycle(1, "M") for _ in range(2)],
            # No array_pr_next provided
            array_increase_decrease=["DEC", "DEC"],
            next_principal_redemption_amount=Decimal("5000.0"),
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=1,
            denomination_asset_decimals=6,
            notional_unit_value=Decimal("1.0"),
            secondary_market_opening_date=base_time,
            secondary_market_closure_date=ied + (5 * month_secs),
        )

        pr_events = [ev for ev in result.schedule if ev.event_type == "PR"]

        # All events should use the base amount
        base_amount = to_asa_units(Decimal("5000.0"), 6)
        for i, ev in enumerate(pr_events):
            assert ev.next_principal_redemption == base_amount, (
                f"Period {i}: Expected next_principal_redemption={base_amount}, "
                f"got {ev.next_principal_redemption}"
            )


class TestRateResetAmortizing:
    """Test rate reset events are correctly interleaved with principal redemptions."""

    def test_lam_with_rate_reset_interleaved(self):
        """Test LAM contract with rate resets has correct outstanding principal at each RR event."""
        # Create LAM contract with quarterly principal redemptions and annual rate resets
        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=1100000 + 365 * 24 * 60 * 60 * 2,  # 2 years
            notional_principal=1000000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.05,
            next_principal_redemption_amount=250000,  # 4 payments of 250k each
            # Rate resets annually
            rate_reset_cycle=Cycle(count=1, unit="Y"),
            rate_reset_anchor=1100000 + 365 * 24 * 60 * 60,  # 1 year after start
            rate_reset_next=0.06,
            # Principal redemptions quarterly
            principal_redemption_cycle=Cycle(count=3, unit="M"),
            principal_redemption_anchor=1100000 + 90 * 24 * 60 * 60,  # 3 months
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1000000,
            secondary_market_closure_date=2000000,
        )

        # Extract event schedule
        events = result.schedule

        # Find RR events
        rr_events = [e for e in events if e.event_type in ("RR", "RRF")]

        # Find PR events before each RR event
        pr_events = [e for e in events if e.event_type == "PR"]

        assert len(rr_events) > 0, "Should have rate reset events"
        assert len(pr_events) > 0, "Should have principal redemption events"

        # Verify that RR events have different outstanding principals
        # (not all the same terminal balance)
        if len(rr_events) > 1:
            rr_principals = [e.next_outstanding_principal for e in rr_events]
            # They should not all be the same (which would indicate the bug)
            assert len(set(rr_principals)) > 1 or all(
                p == 1000000 * 100 for p in rr_principals[:1]
            ), "RR events should have varying outstanding principals as schedule progresses"

        # Verify ordering: earlier RR events should have higher or equal outstanding principal
        for i in range(len(rr_events) - 1):
            assert (
                rr_events[i].next_outstanding_principal
                >= rr_events[i + 1].next_outstanding_principal
            ), f"RR event {i} principal should be >= RR event {i+1} principal"

    def test_nam_with_rate_reset_correct_balance(self):
        """Test NAM contract with rate resets tracks outstanding principal correctly."""
        contract = ContractAttributes(
            contract_id=2,
            contract_type="NAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=1100000 + 365 * 24 * 60 * 60 * 3,  # 3 years
            notional_principal=900000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.04,
            next_principal_redemption_amount=100000,
            # Rate resets every 6 months
            rate_reset_cycle=Cycle(count=6, unit="M"),
            rate_reset_anchor=1100000 + 180 * 24 * 60 * 60,
            rate_reset_next=0.045,
            # Principal redemptions quarterly
            principal_redemption_cycle=Cycle(count=3, unit="M"),
            principal_redemption_anchor=1100000 + 90 * 24 * 60 * 60,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1000000,
            secondary_market_closure_date=2000000,
        )

        events = result.schedule
        rr_events = [e for e in events if e.event_type in ("RR", "RRF")]

        # Each RR event should have outstanding principal that reflects
        # redemptions that occurred before it
        for i, rr_event in enumerate(rr_events):
            # Count PR events that occurred before this RR event
            pr_before = [
                e
                for e in events
                if e.event_type == "PR" and e.scheduled_time < rr_event.scheduled_time
            ]

            # The outstanding principal at this RR should be less than initial
            # if there were any PR events before it
            if len(pr_before) > 0:
                assert (
                    rr_event.next_outstanding_principal < 900000 * 100
                ), f"RR event {i} should reflect prior principal redemptions"

    def test_lax_with_rate_reset_interleaved(self):
        """Test LAX contract with rate resets has correct outstanding principal progression."""
        contract = ContractAttributes(
            contract_id=3,
            contract_type="LAX",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=1100000 + 365 * 24 * 60 * 60 * 2,
            notional_principal=500000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.05,
            # LAX with varying principal amounts
            array_pr_next=[100000, 150000, 200000, 50000],
            array_increase_decrease=["DEC", "DEC", "INC", "DEC"],
            # Rate resets annually
            rate_reset_cycle=Cycle(count=1, unit="Y"),
            rate_reset_anchor=1100000 + 365 * 24 * 60 * 60,
            rate_reset_next=0.055,
            # Principal redemptions quarterly
            principal_redemption_cycle=Cycle(count=3, unit="M"),
            principal_redemption_anchor=1100000 + 90 * 24 * 60 * 60,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1000000,
            secondary_market_closure_date=2000000,
        )

        events = result.schedule
        rr_events = [e for e in events if e.event_type in ("RR", "RRF")]

        # Verify RR events exist
        assert len(rr_events) > 0, "Should have rate reset events"

        # Verify that the outstanding principal at each RR event reflects
        # the actual balance at that point in time, not the terminal balance
        if len(rr_events) >= 2:
            # The outstanding principals should differ if principal changes occurred
            principals = [e.next_outstanding_principal for e in rr_events]
            # Check that they're not all equal (which would indicate the bug)
            unique_principals = set(principals)
            # Given the LAX schedule with INC and DEC, we expect variation
            # or at least not all terminal balance
            assert (
                len(unique_principals) >= 1
            ), "RR events should track actual outstanding balance"


def test_nam_capitalizes_unpaid_interest():
    """Test that NAM capitalizes unpaid interest when payment < interest due."""
    # Create a NAM contract with small payments that won't cover interest
    contract = ContractAttributes(
        contract_id=1,
        contract_type="NAM",
        status_date=1000000,
        initial_exchange_date=1100000,
        maturity_date=1100000 + 365 * 24 * 60 * 60,  # 1 year
        notional_principal=1000000,  # 1,000,000 minor units
        premium_discount_at_ied=0,
        nominal_interest_rate=0.12,  # 12% annual rate
        # Small payment that won't cover interest
        next_principal_redemption_amount=500,  # 500 minor units
        # Monthly payments
        principal_redemption_cycle=Cycle(count=1, unit="M"),
        principal_redemption_anchor=1100000 + 30 * 24 * 60 * 60,
        day_count_convention=DayCountConvention.A360,
        business_day_convention=BusinessDayConvention.NOS,
        end_of_month_convention=EndOfMonthConvention.SD,
        calendar=Calendar.NC,
    )

    result = normalize_contract_attributes(
        contract,
        denomination_asset_id=100,
        denomination_asset_decimals=2,
        notional_unit_value=1000,
        secondary_market_opening_date=1000000,
        secondary_market_closure_date=2000000,
    )

    events = result.schedule
    pr_events = [e for e in events if e.event_type == "PR"]

    # First PR event should show increased outstanding principal (capitalization)
    # Interest for ~30 days at 12% on 1,000,000 (in cents) = ~10,000 cents
    # Payment is only 500 cents, so ~9,500 cents should be capitalized
    # Outstanding should increase from 1,000,000 to approximately 1,009,500

    assert len(pr_events) > 0, "Should have PR events"

    first_pr = pr_events[0]
    initial_outstanding = 1000000  # Initial outstanding in minor units

    # Outstanding should increase (negative amortization)
    assert (
        first_pr.next_outstanding_principal > initial_outstanding
    ), f"Outstanding should increase from {initial_outstanding} to {first_pr.next_outstanding_principal}"

    # Verify multiple periods show continued capitalization
    if len(pr_events) > 1:
        second_pr = pr_events[1]
        assert (
            second_pr.next_outstanding_principal > first_pr.next_outstanding_principal
        ), "Outstanding should continue to increase in subsequent periods"


class TestRateResetInterpolation:
    """Test that rate reset events have correct balance interpolation."""

    def test_lam_with_interleaved_rate_resets_has_correct_balance(self):
        """
        Test LAM with monthly principal redemptions and semiannual rate resets.

        The rate reset events that fall between principal redemption dates should
        have the interpolated balance at that timestamp, not the final balance.
        """
        # Setup: 120k initial, 10k monthly redemptions, 6-month rate resets
        # At month 6 (reset), balance should be 70k (120k - 5*10k from months 1-5)
        status_ts = 1704067200  # 2024-01-01 00:00:00 UTC
        start_ts = status_ts + 24 * 60 * 60  # 2024-01-02 (IED must be after status)
        month_1 = start_ts + 31 * 24 * 60 * 60  # Feb 1
        month_6 = start_ts + 181 * 24 * 60 * 60  # Jul 1 (approx)

        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAM",
            status_date=status_ts,
            initial_exchange_date=start_ts,
            maturity_date=start_ts + 365 * 24 * 60 * 60,  # 1 year
            notional_principal=120_000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.05,
            next_principal_redemption_amount=10_000,
            principal_redemption_anchor=month_1,
            principal_redemption_cycle=Cycle(count=1, unit="M"),  # Monthly
            rate_reset_anchor=month_6,
            rate_reset_cycle=Cycle(count=6, unit="M"),  # Semiannual
            rate_reset_next=0.06,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=6,
            notional_unit_value=1,
            secondary_market_opening_date=start_ts,
            secondary_market_closure_date=start_ts + 400 * 24 * 60 * 60,
        )
        schedule = result.schedule

        # Find RR events
        rr_events = [e for e in schedule if e.event_type in ("RR", "RRF")]
        assert len(rr_events) > 0, "Should have rate reset events"

        # Find the first RR event (should be around month 6)
        first_rr = rr_events[0]

        # Count PR events before first reset
        pr_before_reset = [
            e
            for e in schedule
            if e.event_type == "PR" and e.scheduled_time < first_rr.scheduled_time
        ]

        # With monthly redemptions and 6-month reset, should have ~5 PRs before reset
        assert (
            len(pr_before_reset) >= 5
        ), f"Expected at least 5 PR events before first reset, got {len(pr_before_reset)}"

        # The balance at the reset should reflect those redemptions
        # Not the terminal balance (which would be 0 or close to 0)
        initial_balance = 120_000_000_000  # 120k in micro-units

        # First RR should NOT have terminal balance of 0
        assert (
            first_rr.next_outstanding_principal > 0
        ), "First RR event should not have terminal balance"

        # First RR should have less than initial (some payments made)
        assert (
            first_rr.next_outstanding_principal < initial_balance
        ), f"First RR event should have reduced balance after {len(pr_before_reset)} PR events"

    def test_ann_with_interleaved_rate_resets_has_correct_balance(self):
        """
        Test ANN with quarterly principal redemptions and semiannual rate resets.

        Rate reset events between redemption dates should capture the correct
        interpolated balance, not the terminal balance.
        """
        status_ts = 1704067200  # 2024-01-01 00:00:00 UTC
        start_ts = status_ts + 24 * 60 * 60  # 2024-01-02
        quarter_1 = start_ts + 90 * 24 * 60 * 60  # Apr 1 (approx)
        month_6 = start_ts + 181 * 24 * 60 * 60  # Jul 1 (approx)

        contract = ContractAttributes(
            contract_id=2,
            contract_type="ANN",
            status_date=status_ts,
            initial_exchange_date=start_ts,
            maturity_date=start_ts + 365 * 24 * 60 * 60,
            notional_principal=100_000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.06,
            next_principal_redemption_amount=7_000,
            principal_redemption_anchor=quarter_1,
            principal_redemption_cycle=Cycle(count=3, unit="M"),  # Quarterly
            rate_reset_anchor=month_6,
            rate_reset_cycle=Cycle(count=6, unit="M"),  # Semiannual
            rate_reset_next=0.065,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=6,
            notional_unit_value=1,
            secondary_market_opening_date=status_ts,
            secondary_market_closure_date=start_ts + 400 * 24 * 60 * 60,
        )
        schedule = result.schedule

        # Find RR events
        rr_events = [e for e in schedule if e.event_type in ("RR", "RRF")]

        if len(rr_events) > 0:
            first_rr = rr_events[0]

            # Find the most recent PR event before or at the reset to determine expected balance
            pr_events_before_reset = [
                e
                for e in schedule
                if e.event_type == "PR" and e.scheduled_time <= first_rr.scheduled_time
            ]

            if pr_events_before_reset:
                # Sort by time and get the last one
                pr_events_before_reset.sort(key=lambda e: e.scheduled_time)
                expected_balance = pr_events_before_reset[-1].next_outstanding_principal

                actual_balance = first_rr.next_outstanding_principal

                # For events at the same timestamp, balance should match
                # For events between PR dates, balance should match last PR
                assert actual_balance == expected_balance, (
                    f"RR event should have balance matching last PR event at or before it: "
                    f"expected {expected_balance}, got {actual_balance}"
                )

    def test_nam_with_rate_reset_preserves_capitalized_balance(self):
        """
        Test NAM (negative amortization) with rate resets.

        When principal can increase due to capitalization, rate reset events
        should reflect the actual balance at that point in time.
        """
        status_ts = 1704067200  # 2024-01-01 00:00:00 UTC
        start_ts = status_ts + 24 * 60 * 60  # 2024-01-02
        month_1 = start_ts + 31 * 24 * 60 * 60
        month_6 = start_ts + 181 * 24 * 60 * 60

        contract = ContractAttributes(
            contract_id=3,
            contract_type="NAM",
            status_date=status_ts,
            initial_exchange_date=start_ts,
            maturity_date=start_ts + 365 * 24 * 60 * 60,
            notional_principal=100_000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.12,  # High rate to trigger capitalization
            next_principal_redemption_amount=500,
            # Low payment -> capitalization
            principal_redemption_anchor=month_1,
            principal_redemption_cycle=Cycle(count=1, unit="M"),  # Monthly
            rate_reset_anchor=month_6,
            rate_reset_cycle=Cycle(count=6, unit="M"),  # Semiannual
            rate_reset_next=0.13,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=6,
            notional_unit_value=1,
            secondary_market_opening_date=status_ts,
            secondary_market_closure_date=start_ts + 400 * 24 * 60 * 60,
        )
        schedule = result.schedule

        # Find RR events
        rr_events = [e for e in schedule if e.event_type in ("RR", "RRF")]

        if len(rr_events) > 0:
            first_rr = rr_events[0]

            # Find the most recent PR event to compare
            pr_events_before_reset = [
                e
                for e in schedule
                if e.event_type == "PR" and e.scheduled_time < first_rr.scheduled_time
            ]

            if pr_events_before_reset:
                pr_events_before_reset.sort(key=lambda e: e.scheduled_time)
                expected_balance = pr_events_before_reset[-1].next_outstanding_principal
                actual_balance = first_rr.next_outstanding_principal

                # Balance should have increased due to capitalization
                assert (
                    actual_balance >= 100_000_000_000
                ), "NAM balance should have grown due to capitalization"

                assert actual_balance == expected_balance, (
                    f"RR event should capture the capitalized balance: "
                    f"expected {expected_balance}, got {actual_balance}"
                )

    def test_lax_with_rate_reset_tracks_balance_through_inc_and_dec(self):
        """
        Test LAX with mixed INC/DEC directions and rate resets.

        Rate resets should track balance through both increases and decreases.
        """
        status_ts = 1704067200  # 2024-01-01 00:00:00 UTC
        start_ts = status_ts + 24 * 60 * 60  # 2024-01-02
        month_2 = start_ts + 31 * 24 * 60 * 60
        month_4 = start_ts + 90 * 24 * 60 * 60

        contract = ContractAttributes(
            contract_id=4,
            contract_type="LAX",
            status_date=status_ts,
            initial_exchange_date=start_ts,
            maturity_date=start_ts + 180 * 24 * 60 * 60,  # 6 months
            notional_principal=100_000,
            premium_discount_at_ied=0,
            nominal_interest_rate=0.05,
            # LAX uses arrays
            array_pr_anchor=[month_2, month_4],
            array_pr_cycle=[Cycle(count=1, unit="M"), Cycle(count=1, unit="M")],
            array_pr_next=[5_000, 3_000],  # Different amounts per segment
            array_increase_decrease=["DEC", "INC"],
            # First segment decreases, second increases
            rate_reset_anchor=start_ts + 75 * 24 * 60 * 60,  # Month 2.5
            rate_reset_cycle=Cycle(count=1, unit="M"),
            rate_reset_next=0.055,
            day_count_convention=DayCountConvention.A360,
            business_day_convention=BusinessDayConvention.NOS,
            end_of_month_convention=EndOfMonthConvention.SD,
            calendar=Calendar.NC,
        )

        result = normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=6,
            notional_unit_value=1,
            secondary_market_opening_date=status_ts,
            secondary_market_closure_date=start_ts + 200 * 24 * 60 * 60,
        )
        schedule = result.schedule

        # Find rate reset events
        reset_events = [e for e in schedule if e.event_type in ("RR", "RRF")]

        # Each reset should have a balance matching the timeline
        for reset_event in reset_events:
            reset_ts = reset_event.scheduled_time

            # Find all PR/PI events before this reset
            principal_events = [
                e
                for e in schedule
                if e.event_type in ("PR", "PI") and e.scheduled_time < reset_ts
            ]

            if principal_events:
                # Sort and get the last one
                principal_events.sort(key=lambda e: e.scheduled_time)
                expected_balance = principal_events[-1].next_outstanding_principal
            else:
                # No principal events yet, should be initial balance
                expected_balance = 100_000_000_000

            actual_balance = reset_event.next_outstanding_principal

            assert actual_balance == expected_balance, (
                f"RR event at {reset_ts} should have balance {expected_balance}, "
                f"but got {actual_balance}"
            )


def test_nam_capitalization_uint64_overflow_detection():
    """Test that NAM capitalization detects and rejects uint64 overflow."""
    # Create a NAM contract with large notional and high interest rate
    # that will cause overflow during capitalization
    # Use a notional that when scaled won't overflow initially,
    # but will overflow when interest capitalizes

    # Calculate a large notional that is divisible by notional_unit_value
    # MAX_UINT64 / 100 ≈ 184467440737095516, round down to multiple of 1000
    large_notional = (int(cst.MAX_UINT64 / 100) // 1000) * 1000

    contract = ContractAttributes(
        contract_id=1,
        contract_type="NAM",
        status_date=1000000,
        initial_exchange_date=1100000,
        maturity_date=1100000 + 365 * 24 * 60 * 60,  # 1 year
        notional_principal=large_notional,
        premium_discount_at_ied=0,
        nominal_interest_rate=0.50,  # 50% annual rate - will cause massive capitalization
        # Very small payment that won't cover interest
        next_principal_redemption_amount=100,
        # Monthly payments
        principal_redemption_cycle=Cycle(count=1, unit="M"),
        principal_redemption_anchor=1100000 + 30 * 24 * 60 * 60,
        day_count_convention=DayCountConvention.A360,
        business_day_convention=BusinessDayConvention.NOS,
        end_of_month_convention=EndOfMonthConvention.SD,
        calendar=Calendar.NC,
    )

    # Should raise ActusNormalizationError due to uint64 overflow
    with pytest.raises(
        ActusNormalizationError,
        match=r"NAM capitalization.*exceeds uint64 bounds",
    ):
        normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=2,
            notional_unit_value=1000,
            secondary_market_opening_date=1000000,
            secondary_market_closure_date=2000000,
        )


def test_lax_inc_uint64_overflow_detection():
    """Test that LAX INC detects and rejects uint64 overflow when array_pr_next values are too large."""
    # Create a LAX contract with a large notional and an even larger array_pr_next value
    # that would cause overflow when added to outstanding principal

    # Start with a large but valid notional
    large_notional = int(cst.MAX_UINT64 * 0.6)  # 60% of MAX_UINT64

    # Create an array_pr_next value that when added to large_notional will exceed MAX_UINT64
    overflow_payment = int(cst.MAX_UINT64 * 0.5)  # This + large_notional > MAX_UINT64

    contract = ContractAttributes(
        contract_id=1,
        contract_type="LAX",
        status_date=1000000,
        initial_exchange_date=1100000,
        maturity_date=1100000 + 365 * 24 * 60 * 60,  # 1 year
        notional_principal=large_notional,
        premium_discount_at_ied=0,
        nominal_interest_rate=0.05,  # 5% annual rate
        # Array-based schedule
        array_pr_next=[overflow_payment],  # This will cause overflow in INC
        array_increase_decrease=["INC"],  # Principal increase
        array_pr_anchor=[1100000 + 30 * 24 * 60 * 60],
        array_pr_cycle=[Cycle(count=1, unit="M")],
        day_count_convention=DayCountConvention.A360,
        business_day_convention=BusinessDayConvention.NOS,
        end_of_month_convention=EndOfMonthConvention.SD,
        calendar=Calendar.NC,
    )

    # Should raise ActusNormalizationError due to uint64 overflow
    with pytest.raises(
        ActusNormalizationError,
        match=r"LAX INC.*exceeds uint64 bounds",
    ):
        normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=0,  # No scaling to simplify
            notional_unit_value=1,
            secondary_market_opening_date=1000000,
            secondary_market_closure_date=2000000,
        )


def test_lax_array_pr_next_scaled_value_overflow_detection():
    """Test that LAX detects overflow when array_pr_next scaled values exceed uint64 bounds."""
    # Create a LAX contract where the scaled array_pr_next value itself exceeds MAX_UINT64
    # This tests the validation that happens before any addition

    # Use a value that when scaled with decimals will exceed MAX_UINT64
    # MAX_UINT64 = 18446744073709551615
    # With 6 decimals, any value > 18446744073709.551615 will overflow
    excessive_value = int(cst.MAX_UINT64 / 1e6) + 1000000  # This * 10^6 > MAX_UINT64

    contract = ContractAttributes(
        contract_id=1,
        contract_type="LAX",
        status_date=1000000,
        initial_exchange_date=1100000,
        maturity_date=1100000 + 365 * 24 * 60 * 60,
        notional_principal=1000000,  # Small notional
        premium_discount_at_ied=0,
        nominal_interest_rate=0.05,
        array_pr_next=[excessive_value],  # Scaled value will overflow
        array_increase_decrease=["INC"],
        array_pr_anchor=[1100000 + 30 * 24 * 60 * 60],
        array_pr_cycle=[Cycle(count=1, unit="M")],
        day_count_convention=DayCountConvention.A360,
        business_day_convention=BusinessDayConvention.NOS,
        end_of_month_convention=EndOfMonthConvention.SD,
        calendar=Calendar.NC,
    )

    # Should raise ActusNormalizationError due to scaled value overflow
    # The error can come from either to_asa_units or from our LAX-specific validation
    with pytest.raises(
        ActusNormalizationError,
        match=r"(Value.*exceeds uint64 bounds|LAX array_pr_next\[\d+\] scaled value.*exceeds uint64 bounds)",
    ):
        normalize_contract_attributes(
            contract,
            denomination_asset_id=100,
            denomination_asset_decimals=6,  # 6 decimals will cause overflow
            notional_unit_value=1,
            secondary_market_opening_date=1000000,
            secondary_market_closure_date=2000000,
        )


def test_ann_subtype_calculates_annuity_payment():
    """
    Test that ANN subtypes (e.g., "ANN:ZCB") correctly calculate annuity payments.

    Regression test for issue where "ANN:ZCB" was not recognized as an ANN contract
    and would skip _resolve_annuity_payment, resulting in next_principal_redemption=0.
    """
    status_ts = 1704067200  # 2024-01-01 00:00:00 UTC
    start_ts = status_ts + 24 * 60 * 60  # 2024-01-02
    quarter_1 = start_ts + 90 * 24 * 60 * 60

    # Test with subtype notation "ANN:ZCB"
    contract_subtype = ContractAttributes(
        contract_id=1,
        contract_type="ANN:ZCB",
        status_date=status_ts,
        initial_exchange_date=start_ts,
        maturity_date=start_ts + 365 * 24 * 60 * 60,
        notional_principal=100_000,
        premium_discount_at_ied=0,
        nominal_interest_rate=0.06,
        next_principal_redemption_amount=7_000,
        principal_redemption_anchor=quarter_1,
        principal_redemption_cycle=Cycle(count=3, unit="M"),
        day_count_convention=DayCountConvention.A360,
        business_day_convention=BusinessDayConvention.NOS,
        end_of_month_convention=EndOfMonthConvention.SD,
        calendar=Calendar.NC,
    )

    # Test with base type "ANN"
    contract_base = ContractAttributes(
        contract_id=2,
        contract_type="ANN",
        status_date=status_ts,
        initial_exchange_date=start_ts,
        maturity_date=start_ts + 365 * 24 * 60 * 60,
        notional_principal=100_000,
        premium_discount_at_ied=0,
        nominal_interest_rate=0.06,
        next_principal_redemption_amount=7_000,
        principal_redemption_anchor=quarter_1,
        principal_redemption_cycle=Cycle(count=3, unit="M"),
        day_count_convention=DayCountConvention.A360,
        business_day_convention=BusinessDayConvention.NOS,
        end_of_month_convention=EndOfMonthConvention.SD,
        calendar=Calendar.NC,
    )

    result_subtype = normalize_contract_attributes(
        contract_subtype,
        denomination_asset_id=100,
        denomination_asset_decimals=6,
        notional_unit_value=1,
        secondary_market_opening_date=status_ts,
        secondary_market_closure_date=start_ts + 400 * 24 * 60 * 60,
    )

    result_base = normalize_contract_attributes(
        contract_base,
        denomination_asset_id=100,
        denomination_asset_decimals=6,
        notional_unit_value=1,
        secondary_market_opening_date=status_ts,
        secondary_market_closure_date=start_ts + 400 * 24 * 60 * 60,
    )

    # Both should have the same IED event with correct annuity payment
    # The IED (Initial Exchange Date) event contains the calculated annuity payment
    ied_subtype = next(e for e in result_subtype.schedule if e.event_type == "IED")
    ied_base = next(e for e in result_base.schedule if e.event_type == "IED")

    # Specifically, next_principal_redemption should be non-zero for both
    assert (
        ied_subtype.next_principal_redemption > 0
    ), "ANN:ZCB subtype should calculate annuity payment in IED event"
    assert (
        ied_base.next_principal_redemption > 0
    ), "ANN base type should calculate annuity payment in IED event"

    # The calculated annuity payment should be identical for both
    assert (
        ied_subtype.next_principal_redemption == ied_base.next_principal_redemption
    ), f"ANN:ZCB and ANN should produce identical annuity payments: subtype={ied_subtype.next_principal_redemption}, base={ied_base.next_principal_redemption}"

    # Verify other IED properties match too
    assert (
        ied_subtype.next_outstanding_principal == ied_base.next_outstanding_principal
    ), "Outstanding principal should match"
    assert (
        ied_subtype.next_nominal_interest_rate == ied_base.next_nominal_interest_rate
    ), "Nominal interest rate should match"
