from typing import Final

################################################################################
# AVM Contract Status  # TODO: Use Contract Performance instead
################################################################################
STATUS_INACTIVE: Final[int] = 0
STATUS_PENDING_IED: Final[int] = 50
STATUS_ACTIVE: Final[int] = 100
STATUS_ENDED: Final[int] = 200

################################################################################
# ACTUS Contract Types
################################################################################
CT_PAM: Final[int] = 0
CT_ANN: Final[int] = 1
CT_NAM: Final[int] = 2
CT_LAM: Final[int] = 3
CT_LAX: Final[int] = 4
CT_CLM: Final[int] = 5

################################################################################
# ACTUS Event types
################################################################################
EVT_AD: Final[int] = 0
EVT_IED: Final[int] = 1
EVT_PR: Final[int] = 3
EVT_PRF: Final[int] = 5
EVT_PY: Final[int] = 6
EVT_PP: Final[int] = 7
EVT_IP: Final[int] = 8
EVT_RRF: Final[int] = 11
EVT_RR: Final[int] = 12
EVT_IPCB: Final[int] = 18
EVT_MD: Final[int] = 19

################################################################################
# Event flags
################################################################################
FLAG_CASH_EVENT: Final[int] = 1 << 0
FLAG_NON_CASH_EVENT: Final[int] = 1 << 1
FLAG_OBSERVED_EVENT: Final[int] = 1 << 2
FLAG_INITIAL_PRF: Final[int] = 1 << 3

################################################################################
# Day-count Conventions
################################################################################
DCC_AA: Final[int] = 0
DCC_A360: Final[int] = 1
DCC_A365: Final[int] = 2
DCC_30E360ISDA: Final[int] = 3
DCC_30E360: Final[int] = 4

################################################################################
# Calendar
################################################################################
CLDR_NC: Final[int] = 0
CLDR_MF: Final[int] = 1
CLDR_CUST: Final[int] = 255

################################################################################
# Business Day Convention
################################################################################
BDC_NOS: Final[int] = 0
BDC_SCF: Final[int] = 1
BDC_SCMF: Final[int] = 2
BDC_CSF: Final[int] = 3
BDC_CSMF: Final[int] = 4
BDC_SCP: Final[int] = 5
BDC_SCMP: Final[int] = 6
BDC_CSP: Final[int] = 7
BDC_CSMP: Final[int] = 8

################################################################################
# End of Month Convention
################################################################################
EOMC_SD: Final[int] = 0
EOMC_EOM: Final[int] = 1

################################################################################
# Prepayment Effect
################################################################################
PPEF_N: Final[int] = 0
PPEF_A: Final[int] = 1
PPEF_M: Final[int] = 2

################################################################################
# Penalty Type
################################################################################
PYTP_N: Final[int] = 0
PYTP_A: Final[int] = 1
PYTP_R: Final[int] = 2
PYTP_I: Final[int] = 3

################################################################################
# Contract Performance
################################################################################
PRF_PERFORMANT: Final[int] = 0
PRF_DELAYED: Final[int] = 1
PRF_DELINQUENT: Final[int] = 2
PRF_DEFAULTED: Final[int] = 3
PRF_MATURED: Final[int] = 4
PRF_TERMINATED: Final[int] = 5

################################################################################
# Role IDs
################################################################################
ROLE_ARRANGER: Final[int] = 20
ROLE_OP_DAEMON: Final[int] = 25
ROLE_ACCOUNT_MANAGER: Final[int] = 40
ROLE_PRIMARY_DEALER: Final[int] = 50
ROLE_TRUSTEE: Final[int] = 60
ROLE_AUTHORITY: Final[int] = 70
ROLE_OBSERVER: Final[int] = 80

################################################################################
# Payoff Sign
################################################################################
PAYOFF_SIGN_POSITIVE: Final[int] = 1
PAYOFF_SIGN_NEGATIVE: Final[int] = 255
