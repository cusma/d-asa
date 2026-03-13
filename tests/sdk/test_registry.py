"""Pin the ACTUS registry constants used by the SDK and AVM."""

from __future__ import annotations

from d_asa.registry import (
    ALLOWED_EVENT_TYPES,
    CASH_EVENT_TYPES,
    CONTRACT_TYPE_IDS,
    EVENT_SCHEDULE_PRIORITY,
    EVENT_TYPE_IDS,
    NON_CASH_EVENT_TYPES,
    REJECTED_EVENT_TYPES,
    SUPPORTED_CONTRACT_TYPES,
)
from smart_contracts import enums


def test_supported_contract_types_match_v1_scope() -> None:
    """Supported types should match the intended fixed-income v1 scope."""
    assert SUPPORTED_CONTRACT_TYPES == frozenset(
        {"PAM", "LAM", "NAM", "ANN", "LAX", "CLM"}
    )


def test_rejected_event_types_exclude_v1_out_of_scope_flows() -> None:
    """Rejected types should cover the event families excluded from v1."""
    assert REJECTED_EVENT_TYPES == frozenset(
        {"PP", "PY", "SC", "CE", "PRD", "TD", "FP"}
    )


def test_contract_type_ids_are_stable() -> None:
    """Contract type ids should remain stable across SDK and AVM layers."""
    assert CONTRACT_TYPE_IDS["PAM"] == enums.CT_PAM
    assert CONTRACT_TYPE_IDS["CLM"] == enums.CT_CLM


def test_event_type_ids_are_stable() -> None:
    """Event ids should remain stable across normalization and execution."""
    assert EVENT_TYPE_IDS["PR"] == enums.EVT_PR
    assert EVENT_TYPE_IDS["PRF"] == enums.EVT_PRF


def test_cash_and_non_cash_sets_cover_allowed_events() -> None:
    """Allowed events should include the shared cash and non-cash subsets."""
    allowed_events = set().union(*ALLOWED_EVENT_TYPES.values())
    assert CASH_EVENT_TYPES.issubset(allowed_events)
    assert NON_CASH_EVENT_TYPES.issubset(allowed_events)


def test_event_priority_matches_actus_sequence() -> None:
    """Event priority should preserve the intended ACTUS ordering."""
    assert EVENT_SCHEDULE_PRIORITY["PR"] < EVENT_SCHEDULE_PRIORITY["IP"]
    assert EVENT_SCHEDULE_PRIORITY["IP"] < EVENT_SCHEDULE_PRIORITY["RR"]
    assert EVENT_SCHEDULE_PRIORITY["RR"] < EVENT_SCHEDULE_PRIORITY["MD"]
