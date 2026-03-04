from algopy import Txn, arc4

from modules.accounting import AccountingModule


class MockAccountingModule(AccountingModule):
    """
    Accounting Module for testing
    """

    def __init__(self) -> None:
        super().__init__()

    @arc4.baremethod(create="require")
    def create(self) -> None:
        self.arranger.value = Txn.sender
