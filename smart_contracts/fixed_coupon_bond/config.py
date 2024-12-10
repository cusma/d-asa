from typing import Final

from smart_contracts.base_d_asa import config as base_cfg

# State Schema
GLOBAL_BYTES: Final[int] = base_cfg.GLOBAL_BYTES
GLOBAL_UINTS: Final[int] = base_cfg.GLOBAL_UINTS + 2
LOCAL_BYTES: Final[int] = base_cfg.LOCAL_BYTES
LOCAL_UINTS: Final[int] = base_cfg.LOCAL_UINTS

# Coupon Due Dates
FIRST_COUPON_DATE_IDX: Final[int] = base_cfg.ISSUANCE_DATE_IDX + 1

# Ensure OpCode Budgets, estimated empirically
OP_UP_COUPON_DUE_COUNTING: Final[int] = (
    255  # Depends on the complexity of `count_due_coupons` subroutine
)
