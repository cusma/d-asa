from algopy import Txn, arc4

from smart_contracts.modules.rbac import RbacModule


class MockRbacModule(RbacModule):
    """
    RBAC Module for testing
    """

    def __init__(self) -> None:
        super().__init__()

    @arc4.baremethod(create="require")
    def create(self) -> None:
        self.arranger.value = Txn.sender
