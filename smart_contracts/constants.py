from typing import Final

################################################################################
# AVM
################################################################################
MAX_UINT64: Final[int] = 2**64 - 1
MAX_ARGS_SIZE: Final[int] = 2048
OP_UP_CONTRACT_CONFIG_BASE_BUDGET: Final[int] = 1_500
OP_UP_CONTRACT_CONFIG_PER_ENTRY_BUDGET: Final[int] = 100
SCHEDULE_PAGE_SIZE: Final[int] = 16

################################################################################
# Conversions
################################################################################
BPS: Final[int] = 10_000
FIXED_POINT_SCALE: Final[int] = 1_000_000_000
DAY_2_SEC: Final[int] = 24 * 60 * 60

################################################################################
# Role Keys Prefix
################################################################################
PREFIX_ID_ARRANGER: Final[bytes] = b"R#Arranger#"
PREFIX_ID_OP_DAEMON: Final[bytes] = b"R#OpDaemon#"
PREFIX_ID_ACCOUNT_MANAGER: Final[bytes] = b"R#AccountManager#"
PREFIX_ID_ACCOUNT: Final[bytes] = b"R#Account#"
PREFIX_ID_PRIMARY_DEALER: Final[bytes] = b"R#PrimaryDealer#"
PREFIX_ID_TRUSTEE: Final[bytes] = b"R#Trustee#"
PREFIX_ID_AUTHORITY: Final[bytes] = b"R#Authority#"
PREFIX_ID_OBSERVER: Final[bytes] = b"R#Observer#"

################################################################################
# ACTUS Schedule Prefix
################################################################################
PREFIX_ID_SCHEDULE_PAGE: Final[bytes] = b"S#"
