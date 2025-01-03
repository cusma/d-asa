from typing import Final

# Conversions
BPS: Final[int] = 10_000

# Day-count Conventions
DAY_2_SEC: Final[int] = 24 * 3_600
DCC_30_360: Final[int] = 10
DCC_30_365: Final[int] = 30
DCC_A_360: Final[int] = 50
DCC_A_365: Final[int] = 70
DCC_A_A: Final[int] = 100
DCC_CONT: Final[int] = 255

# Role IDs
ROLE_ARRANGER: Final[int] = 20
ROLE_LENDER: Final[int] = 30
ROLE_ACCOUNT_MANAGER: Final[int] = 40
ROLE_PRIMARY_DEALER: Final[int] = 50
ROLE_TRUSTEE: Final[int] = 60
ROLE_AUTHORITY: Final[int] = 70
ROLE_INTEREST_ORACLE: Final[int] = 80

# Role Keys Prefix
PREFIX_ID_ARRANGER: Final[bytes] = b"R20#"
PREFIX_ID_ACCOUNT: Final[bytes] = b"R30#"
PREFIX_ID_ACCOUNT_MANAGER: Final[bytes] = b"R40#"
PREFIX_ID_PRIMARY_DEALER: Final[bytes] = b"R50#"
PREFIX_ID_TRUSTEE: Final[bytes] = b"R60#"
PREFIX_ID_AUTHORITY: Final[bytes] = b"R70#"
PREFIX_ID_INTEREST_ORACLE: Final[bytes] = b"R80#"

# Box IDs
BOX_ID_COUPON_RATES: Final[bytes] = b"couponRates"
BOX_ID_TIME_EVENTS: Final[bytes] = b"timeEvents"
BOX_ID_TIME_PERIODS: Final[bytes] = b"timePeriods"
