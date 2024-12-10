from typing import Final

# State Schema
GLOBAL_BYTES: Final[int] = 2
GLOBAL_UINTS: Final[int] = 16
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# Status
STATUS_EMPTY: Final[int] = 0
STATUS_ACTIVE: Final[int] = 100
STATUS_ENDED: Final[int] = 200

# Time Schedule Limits
TIME_SCHEDULE_LIMITS: Final[int] = 4
PRIMARY_DISTRIBUTION_OPENING_DATE_IDX: Final[int] = 0
PRIMARY_DISTRIBUTION_CLOSURE_DATE_IDX: Final[int] = 1
ISSUANCE_DATE_IDX: Final[int] = 2
MATURITY_DATE_IDX: Final[int] = -1

# Secondary Market Schedule Limits
SECONDARY_MARKET_SCHEDULE_LIMITS: Final[int] = 2
SECONDARY_MARKET_OPENING_DATE_IDX: Final[int] = 0
SECONDARY_MARKET_CLOSURE_DATE_IDX: Final[int] = -1

# Ensure OpCode Budgets, estimated empirically
OP_UP_TIME_EVENT_SORTING: Final[int] = (
    65  # Depends on the complexity of `assert_time_events_sorted` subroutine
)
