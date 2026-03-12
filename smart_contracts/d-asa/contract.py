from algopy import StateTotals, Txn

from modules import PaymentAgent, TransferAgent
from smart_contracts import config as cfg
from smart_contracts import errors as err


class DASA(
    PaymentAgent,
    TransferAgent,
    state_totals=StateTotals(
        global_bytes=cfg.GLOBAL_BYTES,
        global_uints=cfg.GLOBAL_UINTS,
        local_bytes=cfg.LOCAL_BYTES,
        local_uints=cfg.LOCAL_UINTS,
    ),
    avm_version=12,
):
    """Debt Algorand Standard Application."""

    def __init__(self) -> None:
        super().__init__()
        assert Txn.global_num_byte_slice == cfg.GLOBAL_BYTES, err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS
