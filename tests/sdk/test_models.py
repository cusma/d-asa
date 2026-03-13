from __future__ import annotations

from src.d_asa.models import (
    ExecutionScheduleEntry,
    InitialKernelState,
    NormalizationResult,
    NormalizedActusTerms,
)


def test_schedule_pages_chunk_entries() -> None:
    terms = NormalizedActusTerms(
        contract_id=42,
        contract_type=0,
        denomination_asset_id=1,
        initial_exchange_date=1,
        maturity_date=2,
        secondary_market_opening_date=0,
        secondary_market_closure_date=0,
        notional_principal=100_000,
        notional_unit_value=1_000,
        initial_exchange_amount=100_000,
        next_principal_redemption_amount=0,
        rate_reset_spread=0,
        rate_reset_multiplier=1_000_000_000,
        rate_reset_floor=0,
        rate_reset_cap=0,
        rate_reset_next=0,
        day_count_convention=2,
        fixed_point_scale=1_000_000_000,
    )
    schedule = tuple(
        ExecutionScheduleEntry(
            event_id=index,
            event_type="IP",
            scheduled_time=index + 1,
            accrual_factor=1,
            redemption_accrual_factor=0,
            next_nominal_interest_rate=0,
            next_principal_redemption=0,
            next_outstanding_principal=100_000,
            flags=0,
        )
        for index in range(5)
    )
    state = InitialKernelState(
        status_date=0,
        event_cursor=0,
        outstanding_principal=0,
        interest_calculation_base=0,
        nominal_interest_rate=0,
        accrued_interest=0,
        next_principal_redemption=0,
        cumulative_interest_index=0,
        cumulative_principal_index=0,
    )
    result = NormalizationResult(terms=terms, schedule=schedule, initial_state=state)

    pages = result.schedule_pages(2)
    assert len(pages) == 3
    assert pages[0][0].event_id == 0
    assert pages[-1][-1].event_id == 4
