"""ACTUS Contract Registry, defines the valid contract types, event types, and composition."""

from __future__ import annotations

from smart_contracts import enums

SUPPORTED_CONTRACT_TYPES: frozenset[str] = frozenset(
    {"PAM", "LAM", "NAM", "ANN", "LAX", "CLM"}
)

REJECTED_EVENT_TYPES: frozenset[str] = frozenset(
    {"PP", "PY", "SC", "CE", "PRD", "TD", "FP"}
)

ALLOWED_EVENT_TYPES: dict[str, frozenset[str]] = {
    "PAM": frozenset({"IED", "IP", "MD", "RR", "RRF"}),
    "ANN": frozenset({"IED", "IP", "PR", "MD", "RR", "RRF", "IPCB", "PRF"}),
    "NAM": frozenset({"IED", "IP", "PR", "MD", "RR", "RRF", "IPCB"}),
    "LAM": frozenset({"IED", "IP", "PR", "MD", "RR", "RRF", "IPCB"}),
    "LAX": frozenset({"IED", "IP", "PR", "PI", "MD", "RR", "RRF", "IPCB", "PRF"}),
    "CLM": frozenset({"IED", "IP", "PR", "MD", "RR", "RRF"}),
}

CASH_EVENT_TYPES: frozenset[str] = frozenset({"IP", "PR", "MD"})
NON_CASH_EVENT_TYPES: frozenset[str] = frozenset(
    {"IED", "PI", "RR", "RRF", "IPCB", "PRF"}
)

CONTRACT_TYPE_IDS: dict[str, int] = {
    "PAM": enums.CT_PAM,
    "ANN": enums.CT_ANN,
    "NAM": enums.CT_NAM,
    "LAM": enums.CT_LAM,
    "LAX": enums.CT_LAX,
    "CLM": enums.CT_CLM,
}

EVENT_TYPE_IDS: dict[str, int] = {
    "IED": enums.EVT_IED,
    "PR": enums.EVT_PR,
    "PRF": enums.EVT_PRF,
    "IP": enums.EVT_IP,
    "RRF": enums.EVT_RRF,
    "RR": enums.EVT_RR,
    "IPCB": enums.EVT_IPCB,
    "MD": enums.EVT_MD,
}

DAY_COUNT_CONVENTION_IDS: dict[str, int] = {
    "AA": enums.DCC_AA,
    "A360": enums.DCC_A360,
    "A365": enums.DCC_A365,
    "30E360ISDA": enums.DCC_30E360ISDA,
    "30E360": enums.DCC_30E360,
}

EVENT_SCHEDULE_PRIORITY: dict[str, int] = {
    "AD": 0,
    "IED": 1,
    "PR": 4,
    "PI": 5,
    "PP": 6,
    "PY": 7,
    "IP": 8,
    "RR": 10,
    "RRF": 11,
    "IPCB": 12,
    "PRF": 14,
    "FP": 15,
    "PRD": 16,
    "TD": 17,
    "MD": 18,
    "CE": 23,
}
