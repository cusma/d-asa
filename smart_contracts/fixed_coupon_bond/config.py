from typing import Final

from smart_contracts import config as base_cfg

# State Schema
GLOBAL_BYTES: Final[int] = base_cfg.GLOBAL_BYTES
GLOBAL_UINTS: Final[int] = base_cfg.GLOBAL_UINTS + 2
LOCAL_BYTES: Final[int] = base_cfg.LOCAL_BYTES
LOCAL_UINTS: Final[int] = base_cfg.LOCAL_UINTS
