"""Tests for the contracts module."""

from decimal import Decimal

import pytest

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
from src.errors import UnsupportedActusFeatureError
from src.schedule import Cycle


class TestContractAttributes:
    """Test ContractAttributes dataclass validation and creation."""

    def test_basic_contract_creation(self):
        """Test creating a basic valid contract."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
        )
        assert contract.contract_id == 1
        assert contract.contract_type == "PAM"
        assert contract.notional_principal == 1000000
        assert contract.nominal_interest_rate == 0

    def test_contract_with_interest(self):
        """Test creating a contract with interest attributes."""
        contract = ContractAttributes(
            contract_id=2,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=10000,
            nominal_interest_rate=0.05,
            interest_payment_cycle=Cycle(count=3, unit="M"),
            interest_payment_anchor=1100000,
        )
        assert contract.nominal_interest_rate == 0.05
        assert contract.premium_discount_at_ied == 10000
        assert contract.interest_payment_cycle.count == 3
        assert contract.interest_payment_cycle.unit == "M"

    def test_contract_with_day_count_conventions(self):
        """Test contract with various day count conventions."""
        for dcc in [
            DayCountConvention.A360,
            DayCountConvention.A365,
            DayCountConvention.AA,
            DayCountConvention.THIRTY_E_360,
            DayCountConvention.THIRTY_E_360_ISDA,
        ]:
            contract = ContractAttributes(
                contract_id=1,
                contract_type="PAM",
                status_date=1000000,
                initial_exchange_date=1100000,
                maturity_date=2000000,
                notional_principal=1000000,
                premium_discount_at_ied=0,
                day_count_convention=dcc,
            )
            assert contract.day_count_convention == dcc

    def test_contract_with_business_day_conventions(self):
        """Test contract with supported business day conventions."""
        # Test supported BDC
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
            business_day_convention=BusinessDayConvention.NOS,
        )
        assert contract.business_day_convention == BusinessDayConvention.NOS

    def test_unsupported_contract_type_raises_error(self):
        """Test that unsupported contract types raise an error."""
        with pytest.raises(
            UnsupportedActusFeatureError, match="Unsupported ACTUS contract type"
        ):
            ContractAttributes(
                contract_id=1,
                contract_type="INVALID",
                status_date=1000000,
                initial_exchange_date=1100000,
                maturity_date=2000000,
                notional_principal=1000000,
                premium_discount_at_ied=0,
            )

    def test_unsupported_business_day_convention_raises_error(self):
        """Test that unsupported business day conventions raise an error."""
        with pytest.raises(
            UnsupportedActusFeatureError, match="Unsupported business day convention"
        ):
            ContractAttributes(
                contract_id=1,
                contract_type="PAM",
                status_date=1000000,
                initial_exchange_date=1100000,
                maturity_date=2000000,
                notional_principal=1000000,
                premium_discount_at_ied=0,
                business_day_convention=BusinessDayConvention.CSF,  # Rejected BDC
            )

    def test_supported_contract_types(self):
        """Test all supported contract types."""
        for contract_type in ["PAM", "LAM", "NAM", "ANN", "LAX", "CLM"]:
            contract = ContractAttributes(
                contract_id=1,
                contract_type=contract_type,
                status_date=1000000,
                initial_exchange_date=1100000,
                maturity_date=2000000,
                notional_principal=1000000,
                premium_discount_at_ied=0,
            )
            assert contract.contract_type == contract_type

    def test_contract_with_subtype_notation(self):
        """Test contract with subtype notation like PAM:ZCB."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM:ZCB",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=50000,
        )
        assert contract.contract_type == "PAM:ZCB"

    def test_contract_with_rate_reset_parameters(self):
        """Test contract with rate reset parameters."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
            rate_reset_spread=0.02,
            rate_reset_multiplier=1.5,
            rate_reset_floor=0.01,
            rate_reset_cap=0.10,
            rate_reset_next=0.05,
            rate_reset_cycle=Cycle(count=6, unit="M"),
            rate_reset_anchor=1200000,
        )
        assert contract.rate_reset_spread == 0.02
        assert contract.rate_reset_multiplier == 1.5
        assert contract.rate_reset_floor == 0.01
        assert contract.rate_reset_cap == 0.10
        assert contract.rate_reset_next == 0.05

    def test_contract_with_principal_redemption(self):
        """Test contract with principal redemption parameters."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
            next_principal_redemption_amount=100000,
            principal_redemption_cycle=Cycle(count=1, unit="Q"),
            principal_redemption_anchor=1200000,
        )
        assert contract.next_principal_redemption_amount == 100000
        assert contract.principal_redemption_cycle.count == 1
        assert contract.principal_redemption_cycle.unit == "Q"

    def test_contract_with_decimal_values(self):
        """Test contract with Decimal values for high precision."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=Decimal("1000000.00"),
            premium_discount_at_ied=Decimal("5000.50"),
            nominal_interest_rate=Decimal("0.0375"),
        )
        assert contract.notional_principal == Decimal("1000000.00")
        assert contract.premium_discount_at_ied == Decimal("5000.50")
        assert contract.nominal_interest_rate == Decimal("0.0375")

    def test_contract_with_lax_arrays(self):
        """Test LAX contract with array schedules."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="LAX",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
            array_pr_anchor=[1200000, 1300000, 1400000],
            array_pr_cycle=[Cycle(1, "M"), Cycle(1, "M"), Cycle(1, "M")],
            array_pr_next=[10000, 20000, 30000],
            array_increase_decrease=["DEC", "DEC", "DEC"],
        )
        assert len(contract.array_pr_anchor) == 3
        assert len(contract.array_pr_cycle) == 3
        assert len(contract.array_pr_next) == 3
        assert len(contract.array_increase_decrease) == 3


class TestMakePamZeroCouponBond:
    """Test the make_pam_zero_coupon_bond helper function."""

    def test_basic_zero_coupon_bond(self):
        """Test creating a basic zero coupon bond."""
        contract = make_pam_zero_coupon_bond(
            contract_id=100,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=50000,
        )
        assert contract.contract_id == 100
        assert contract.contract_type == "PAM:ZCB"
        assert contract.notional_principal == 1000000
        assert contract.premium_discount_at_ied == 50000
        assert contract.nominal_interest_rate == 0
        assert contract.maturity_date == 2000000

    def test_zero_coupon_bond_with_custom_conventions(self):
        """Test ZCB with custom day count and business day conventions."""
        contract = make_pam_zero_coupon_bond(
            contract_id=101,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=500000,
            premium_discount_at_ied=25000,
            day_count_convention=DayCountConvention.AA,
            business_day_convention=BusinessDayConvention.SCF,
            end_of_month_convention=EndOfMonthConvention.EOM,
            calendar=Calendar.MF,
        )
        assert contract.day_count_convention == DayCountConvention.AA
        assert contract.business_day_convention == BusinessDayConvention.SCF
        assert contract.end_of_month_convention == EndOfMonthConvention.EOM
        assert contract.calendar == Calendar.MF

    def test_zero_coupon_bond_with_no_discount(self):
        """Test ZCB with no premium/discount (at par)."""
        contract = make_pam_zero_coupon_bond(
            contract_id=102,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
        )
        assert contract.premium_discount_at_ied == 0

    def test_zero_coupon_bond_with_float_values(self):
        """Test ZCB with float values."""
        contract = make_pam_zero_coupon_bond(
            contract_id=103,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000.0,
            premium_discount_at_ied=75000.5,
        )
        assert contract.notional_principal == 1000000.0
        assert contract.premium_discount_at_ied == 75000.5


class TestMakePamFixedCouponBondProfile:
    """Test the make_pam_fixed_coupon_bond_profile helper function."""

    def test_basic_fixed_coupon_bond(self):
        """Test creating a basic fixed coupon bond."""
        contract = make_pam_fixed_coupon_bond_profile(
            contract_id=200,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            nominal_interest_rate=0.05,
            interest_payment_cycle=Cycle(count=6, unit="M"),
            interest_payment_anchor=1100000,
        )
        assert contract.contract_id == 200
        assert contract.contract_type == "PAM:FCB"
        assert contract.notional_principal == 1000000
        assert contract.nominal_interest_rate == 0.05
        assert contract.interest_payment_cycle.count == 6
        assert contract.interest_payment_cycle.unit == "M"
        assert contract.interest_payment_anchor == 1100000

    def test_fixed_coupon_bond_quarterly_payments(self):
        """Test FCB with quarterly interest payments."""
        contract = make_pam_fixed_coupon_bond_profile(
            contract_id=201,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=2000000,
            nominal_interest_rate=0.04,
            interest_payment_cycle=Cycle(count=1, unit="Q"),
            interest_payment_anchor=1100000,
        )
        assert contract.interest_payment_cycle.count == 1
        assert contract.interest_payment_cycle.unit == "Q"
        assert contract.nominal_interest_rate == 0.04

    def test_fixed_coupon_bond_with_custom_conventions(self):
        """Test FCB with custom conventions."""
        contract = make_pam_fixed_coupon_bond_profile(
            contract_id=202,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1500000,
            nominal_interest_rate=0.035,
            interest_payment_cycle=Cycle(count=1, unit="Y"),
            interest_payment_anchor=1100000,
            day_count_convention=DayCountConvention.THIRTY_E_360,
            business_day_convention=BusinessDayConvention.SCMF,
            end_of_month_convention=EndOfMonthConvention.EOM,
            calendar=Calendar.MF,
        )
        assert contract.day_count_convention == DayCountConvention.THIRTY_E_360
        assert contract.business_day_convention == BusinessDayConvention.SCMF
        assert contract.end_of_month_convention == EndOfMonthConvention.EOM
        assert contract.calendar == Calendar.MF

    def test_fixed_coupon_bond_with_decimal_rate(self):
        """Test FCB with Decimal interest rate."""
        contract = make_pam_fixed_coupon_bond_profile(
            contract_id=203,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=Decimal("1000000"),
            nominal_interest_rate=Decimal("0.0425"),
            interest_payment_cycle=Cycle(count=3, unit="M"),
            interest_payment_anchor=1100000,
        )
        assert contract.nominal_interest_rate == Decimal("0.0425")

    def test_fixed_coupon_bond_monthly_payments(self):
        """Test FCB with monthly interest payments."""
        contract = make_pam_fixed_coupon_bond_profile(
            contract_id=204,
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=750000,
            nominal_interest_rate=0.06,
            interest_payment_cycle=Cycle(count=1, unit="M"),
            interest_payment_anchor=1100000,
        )
        assert contract.interest_payment_cycle.count == 1
        assert contract.interest_payment_cycle.unit == "M"
        assert contract.nominal_interest_rate == 0.06


class TestContractAttributesDefaults:
    """Test default values for ContractAttributes."""

    def test_default_interest_values(self):
        """Test that interest-related defaults are correct."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
        )
        assert contract.nominal_interest_rate == 0
        assert contract.rate_reset_spread == 0
        assert contract.rate_reset_multiplier == 1
        assert contract.rate_reset_floor == 0
        assert contract.rate_reset_cap == 0

    def test_default_conventions(self):
        """Test that convention defaults are correct."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
        )
        assert contract.day_count_convention == DayCountConvention.A360
        assert contract.business_day_convention == BusinessDayConvention.NOS
        assert contract.end_of_month_convention == EndOfMonthConvention.SD
        assert contract.calendar == Calendar.NC

    def test_default_optional_fields(self):
        """Test that optional fields default to None."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
        )
        assert contract.principal_redemption_cycle is None
        assert contract.principal_redemption_anchor is None
        assert contract.interest_payment_anchor is None
        assert contract.interest_payment_cycle is None
        assert contract.rate_reset_next is None
        assert contract.array_pr_anchor is None
        assert contract.array_pr_cycle is None
        assert contract.array_pr_next is None
        assert contract.array_increase_decrease is None


class TestContractImmutability:
    """Test that ContractAttributes is immutable (frozen=True)."""

    def test_contract_is_frozen(self):
        """Test that contract attributes cannot be modified after creation."""
        contract = ContractAttributes(
            contract_id=1,
            contract_type="PAM",
            status_date=1000000,
            initial_exchange_date=1100000,
            maturity_date=2000000,
            notional_principal=1000000,
            premium_discount_at_ied=0,
        )
        with pytest.raises(AttributeError):
            contract.contract_id = 2
        with pytest.raises(AttributeError):
            contract.notional_principal = 2000000
