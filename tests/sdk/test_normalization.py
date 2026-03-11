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
from src.errors import ActusNormalizationError
from src.models import ExecutionScheduleEntry, NormalizedActusTerms
from src.normalization import (
    _compute_initial_exchange_amount,
    _deduplicate_timestamps,
    _rate_to_fp,
    _to_asa_units,
    normalize_contract_attributes,
)
from src.schedule import Cycle


class TestToAsaUnits:
    """Test the _to_asa_units helper function."""

    def test_integer_conversion(self):
        """Test converting integer amounts to ASA units."""
        assert _to_asa_units(100, 2) == 10000
        assert _to_asa_units(1000, 0) == 1000
        assert _to_asa_units(50, 3) == 50000

    def test_float_conversion(self):
        """Test converting float amounts to ASA units."""
        result = _to_asa_units(100.5, 2)
        assert result == 10050
        assert isinstance(result, int)

    def test_decimal_conversion(self):
        """Test converting Decimal amounts to ASA units."""
        result = _to_asa_units(Decimal("100.42"), 3)
        assert result == 100420
        assert isinstance(result, int)

    def test_zero_decimals(self):
        """Test conversion with zero decimal places."""
        assert _to_asa_units(100, 0) == 100

    def test_high_decimal_places(self):
        """Test conversion with high decimal places."""
        result = _to_asa_units(1, 10)
        assert result == 10_000_000_000
        assert isinstance(result, int)

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported value type"):
            _to_asa_units("100", 2)
        with pytest.raises(TypeError, match="Unsupported value type"):
            _to_asa_units(None, 2)

    def test_exceeds_uint64_raises_error(self):
        """Test that values exceeding uint64 max raise error."""
        # A large amount that when multiplied by scale exceeds uint64 max
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 bounds"):
            _to_asa_units(cst.MAX_UINT64 * 2, 2)


class TestRateToFp:
    """Test the _rate_to_fp helper function."""

    def test_integer_rate_conversion(self):
        """Test converting integer rates to fixed point."""
        result = _rate_to_fp(1)
        assert result == cst.FIXED_POINT_SCALE
        assert isinstance(result, int)

    def test_float_rate_conversion(self):
        """Test converting float rates to fixed point."""
        result = _rate_to_fp(0.05)
        expected = int(Decimal("0.05") * cst.FIXED_POINT_SCALE)
        assert result == expected

    def test_decimal_rate_conversion(self):
        """Test converting Decimal rates to fixed point."""
        result = _rate_to_fp(Decimal("0.0375"))
        expected = int(Decimal("0.0375") * cst.FIXED_POINT_SCALE)
        assert result == expected

    def test_zero_rate(self):
        """Test converting zero rate."""
        assert _rate_to_fp(0) == 0

    def test_high_precision_rate(self):
        """Test converting high precision rate."""
        rate = Decimal("0.123456789")
        result = _rate_to_fp(rate)
        assert isinstance(result, int)
        assert result > 0

    def test_negative_rate_raises_error(self):
        """Test that negative rates raise error."""
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 bounds"):
            _rate_to_fp(-0.01)

    def test_exceeds_uint64_raises_error(self):
        """Test that very large rates raise error."""
        with pytest.raises(ActusNormalizationError, match="exceeds uint64 bounds"):
            _rate_to_fp(cst.MAX_UINT64)

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported value type"):
            _rate_to_fp("0.05")


class TestComputeInitialExchangeAmount:
    """Test the _compute_initial_exchange_amount helper function."""

    def test_at_par_issuance(self):
        """Test initial exchange with no premium/discount."""
        result = _compute_initial_exchange_amount(
            notional=1000000,
            premium_discount_at_ied=0,
            asa_decimals=2,
        )
        # notional=1000000 with 2 decimals = 100000000, premium=0
        # result = 100000000 - 0 = 100000000
        assert result == 100000000

    def test_with_discount(self):
        """Test initial exchange with discount."""
        result = _compute_initial_exchange_amount(
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
        result = _compute_initial_exchange_amount(
            notional=1000000,
            premium_discount_at_ied=-50000,
            asa_decimals=2,
        )
        # notional=1000000 with 2 decimals = 100000000
        # premium_discount=-50000 with 2 decimals = -5000000
        # result = 100000000 - (-5000000) = 105000000
        assert result == 105000000


class TestDeduplicateTimestamps:
    """Test the _deduplicate_timestamps helper function."""

    def test_empty_sequence(self):
        """Test deduplication of empty sequence."""
        result = _deduplicate_timestamps([])
        assert result == ()

    def test_no_duplicates(self):
        """Test sequence with no duplicates."""
        timestamps = [1000000, 1100000, 1200000]
        result = _deduplicate_timestamps(timestamps)
        assert result == (1000000, 1100000, 1200000)

    def test_with_duplicates(self):
        """Test deduplication removes duplicates."""
        timestamps = [1000000, 1100000, 1100000, 1200000, 1000000]
        result = _deduplicate_timestamps(timestamps)
        assert result == (1000000, 1100000, 1200000)

    def test_preserves_sorted_order(self):
        """Test that result is sorted."""
        timestamps = [1200000, 1000000, 1100000]
        result = _deduplicate_timestamps(timestamps)
        assert result == (1000000, 1100000, 1200000)

    def test_all_same_timestamps(self):
        """Test with all identical timestamps."""
        timestamps = [1000000, 1000000, 1000000]
        result = _deduplicate_timestamps(timestamps)
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
