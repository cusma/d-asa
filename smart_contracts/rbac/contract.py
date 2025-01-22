# pyright: reportMissingModuleSource=false
from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    Global,
    GlobalState,
    Txn,
    arc4,
    subroutine,
)

from .. import constants as cst
from .. import errors as err
from .. import types as typ


class RoleBasedAccessControl(ARC4Contract):
    def __init__(self) -> None:
        # Role Based Access Control
        self.arranger = GlobalState(Account(), key=cst.PREFIX_ID_ARRANGER)
        self.account_manager = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_ID_ACCOUNT_MANAGER
        )
        self.primary_dealer = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_ID_PRIMARY_DEALER
        )
        self.trustee = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_ID_TRUSTEE
        )
        self.authority = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_ID_AUTHORITY
        )
        self.interest_oracle = BoxMap(
            arc4.Address, typ.RoleConfig, key_prefix=cst.PREFIX_ID_INTEREST_ORACLE
        )

    @subroutine
    def assert_caller_is_arranger(self) -> None:
        assert Txn.sender == self.arranger.value, err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_account_manager(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.account_manager
            and self.account_manager[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.account_manager[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_primary_dealer(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.primary_dealer
            and self.primary_dealer[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.primary_dealer[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_trustee(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.trustee
            and self.trustee[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.trustee[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_authority(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.authority
            and self.authority[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.authority[caller].role_validity_end
        ), err.UNAUTHORIZED

    @subroutine
    def assert_caller_is_interest_oracle(self) -> None:
        caller = arc4.Address(Txn.sender)
        assert (
            caller in self.interest_oracle
            and self.interest_oracle[caller].role_validity_start
            <= Global.latest_timestamp
            <= self.interest_oracle[caller].role_validity_end
        ), err.UNAUTHORIZED
