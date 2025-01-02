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
INVALID_TIME_EVENTS_LENGTH = "Time events length is invalid"
INVALID_SORTING = "Time events must be sorted in strictly ascending order"
PENDING_COUPON_PAYMENT = "Pending due coupon payment"
NOT_ENOUGH_FUNDS = "Not enough funds for the payment"
NO_UNITS = "No D-ASA units"

# Asset Config
ALREADY_CONFIGURED = "D-ASA already configured"
INVALID_DENOMINATION = "Denomination asset is not properly set"
INVALID_MINIMUM_DENOMINATION = "Minimum denomination is not a divisor of principal"
INVALID_DAY_COUNT_CONVENTION = "Invalid day-count convention ID"
INVALID_INTEREST_RATE = "Interest rate is not properly defined"
INVALID_TIME = "Time events must be set in the future"
INVALID_TIME_PERIOD = "Time periods in Actual/Actual day count convention must be multiples of a day (in seconds)"
INVALID_TIME_PERIODS = "Time periods are not properly defined"
INVALID_TIME_PERIOD_DURATION = (
    "Time period durations must be strictly greater than zero"
)
INVALID_TIME_PERIOD_REPETITIONS = "Time period repetitions are not properly defined"
INVALID_COUPON_RATES = "Coupon rates are not properly defined"

# Set Secondary Time Events
INVALID_SECONDARY_OPENING_DATE = "Invalid secondary market opening date"
INVALID_SECONDARY_CLOSURE_DATE = "Invalid secondary market closure date"

# Open and Close Account
INVALID_ROLE = "Invalid role identifier"
INVALID_ROLE_ADDRESS = "Invalid account role address"

# Primary Distribution
ZERO_UNITS = "Can not distribute zero units"
OVER_DISTRIBUTION = "Insufficient remaining D-ASA units"
PRIMARY_DISTRIBUTION_CLOSED = "Primary distribution is closed"

# Asset Transfer
SECONDARY_MARKET_CLOSED = "Secondary market is closed"
OVER_TRANSFER = "Insufficient sender units to transfer"
NON_FUNGIBLE_UNITS = "Sender and receiver units are not fungible"

# Pay Coupon
NO_DUE_COUPON = "No due coupon to pay"

# Pay Principal
NOT_MATURE = "Not mature"

# Get Account Units Current Value
NO_PRIMARY_DISTRIBUTION = "Primary distribution not yet executed"

# Get Accrued Interest Amount
INVALID_UNITS = "Invalid amount of units for the account"
