# State Schema
WRONG_GLOBAL_BYTES = "Wrong Global Bytes allocation"
WRONG_GLOBAL_UINTS = "Wrong Global UInts allocation"
WRONG_LOCAL_BYTES = "Wrong Local Bytes allocation"
WRONG_LOCAL_UINTS = "Wrong Local UInts allocation"

# Common
UNAUTHORIZED = "Not authorized"
DEFAULTED = "Defaulted"
SUSPENDED = "Suspended operations"
INVALID_HOLDING_ADDRESS = "Invalid account holding address"
INVALID_SORTING = "Time events must be sorted in strictly ascending order"
NOT_ENOUGH_FUNDS = "Not enough funds for the payment"
NO_UNITS = "No D-ASA units"

# Contract Config
NOT_CONFIGURED = "D-ASA not configured"
TERMS_NOT_CONFIGURED = "D-ASA terms not configured"
ALREADY_CONFIGURED = "D-ASA already configured"
INVALID_ACTUS_CONFIG = "Invalid ACTUS configuration"
INVALID_DENOMINATION = "Denomination asset is not properly set"
INVALID_DAY_COUNT_CONVENTION = "Invalid day-count convention ID"
INVALID_SETTLEMENT_ASSET = (
    "Different settlement asset not supported, must be equal to denomination asset"
)

# Initial Exchange Date
NOT_EVT_IED = "Not IED event"
PENDING_IED = "IED not yet executed"
INVALID_IED = "IED must be set in the future"

# Schedule
INVALID_EVENT_ID = "Invalid event id"
INVALID_EVENT_TYPE = "Invalid event type"
INVALID_EVENT_CURSOR = "Invalid event cursor"
INVALID_SCHEDULE_PAGE = "Invalid schedule page"
PENDING_ACTUS_EVENT = "ACTUS event not yet executed"
OBSERVED_EVENT_REQUIRED = "Observed event required to execute this action"

# Cashflows
NO_DUE_CASHFLOW = "No due cashflow to pay"

# RBAC
INVALID_ROLE = "Invalid role identifier"
INVALID_ROLE_ADDRESS = "Invalid account role address"

# Primary Distribution
ZERO_UNITS = "Can not distribute zero units"
OVER_DISTRIBUTION = "Insufficient remaining D-ASA units"
PRIMARY_DISTRIBUTION_INCOMPLETE = "Primary distribution is not complete"
PRIMARY_DISTRIBUTION_CLOSED = "Primary distribution is closed"

# Transfer
INVALID_TRANSFER_OPENING = "Transfer opening date must be at or after IED"
SELF_TRANSFER = "Sender and receiver must be different"
NULL_TRANSFER = "Transfer units must be greater than zero"
OVER_TRANSFER = "Insufficient sender units to transfer"
CLOSED_TRANSFER = "Transfer is closed"
