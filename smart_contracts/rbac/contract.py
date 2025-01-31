# pyright: reportMissingModuleSource=false
from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    Global,
    GlobalState,
    Txn,
    UInt64,
    arc4,
    op,
    subroutine,
)

from .. import abi_types as typ
from .. import constants as cst
from .. import errors as err


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

    @arc4.abimethod
    def assign_role(
        self, role_address: arc4.Address, role: arc4.UInt8, config: arc4.DynamicBytes
    ) -> arc4.UInt64:
        """
        Assign a role to an address

        Args:
            role_address: Account Role Address
            role: Role identifier
            config: Role configuration (Optional)

        Returns:
            Timestamp of the role assignment

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_ROLE: Invalid role identifier
            INVALID_ROLE_ADDRESS: Invalid account role address
        """
        self.assert_caller_is_arranger()
        assert role.native in (
            UInt64(cst.ROLE_ARRANGER),
            UInt64(cst.ROLE_ACCOUNT_MANAGER),
            UInt64(cst.ROLE_PRIMARY_DEALER),
            UInt64(cst.ROLE_TRUSTEE),
            UInt64(cst.ROLE_AUTHORITY),
            UInt64(cst.ROLE_INTEREST_ORACLE),
        ), err.INVALID_ROLE
        match role.native:
            case UInt64(cst.ROLE_ARRANGER):
                self.arranger.value = role_address.native
            case UInt64(cst.ROLE_ACCOUNT_MANAGER):
                assert (
                    role_address not in self.account_manager
                ), err.INVALID_ROLE_ADDRESS
                self.account_manager[role_address] = typ.RoleConfig.from_bytes(
                    config.native
                )
            case UInt64(cst.ROLE_PRIMARY_DEALER):
                assert role_address not in self.primary_dealer, err.INVALID_ROLE_ADDRESS
                self.primary_dealer[role_address] = typ.RoleConfig.from_bytes(
                    config.native
                )
            case UInt64(cst.ROLE_TRUSTEE):
                assert role_address not in self.trustee, err.INVALID_ROLE_ADDRESS
                self.trustee[role_address] = typ.RoleConfig.from_bytes(config.native)
            case UInt64(cst.ROLE_AUTHORITY):
                assert role_address not in self.authority, err.INVALID_ROLE_ADDRESS
                self.authority[role_address] = typ.RoleConfig.from_bytes(config.native)
            case UInt64(cst.ROLE_INTEREST_ORACLE):
                assert (
                    role_address not in self.interest_oracle
                ), err.INVALID_ROLE_ADDRESS
                self.interest_oracle[role_address] = typ.RoleConfig.from_bytes(
                    config.native
                )
            case _:
                op.err()
        return arc4.UInt64(Global.latest_timestamp)

    @arc4.abimethod
    def revoke_role(self, role_address: arc4.Address, role: arc4.UInt8) -> arc4.UInt64:
        """
        Revoke a role from an address

        Args:
            role_address: Account Role Address
            role: Role identifier

        Returns:
            Timestamp of the role revocation

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_ROLE: Invalid role identifier
            INVALID_ROLE_ADDRESS: Invalid account role address
        """
        self.assert_caller_is_arranger()
        assert role.native in (
            UInt64(cst.ROLE_ACCOUNT_MANAGER),
            UInt64(cst.ROLE_PRIMARY_DEALER),
            UInt64(cst.ROLE_TRUSTEE),
            UInt64(cst.ROLE_AUTHORITY),
            UInt64(cst.ROLE_INTEREST_ORACLE),
        ), err.INVALID_ROLE
        match role.native:
            # Arranger role can not be revoked (just rotated)
            case UInt64(cst.ROLE_ACCOUNT_MANAGER):
                assert role_address in self.account_manager, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_ID_ACCOUNT_MANAGER + role_address.bytes)
            case UInt64(cst.ROLE_PRIMARY_DEALER):
                assert role_address in self.primary_dealer, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_ID_PRIMARY_DEALER + role_address.bytes)
            case UInt64(cst.ROLE_TRUSTEE):
                assert role_address in self.trustee, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_ID_TRUSTEE + role_address.bytes)
            case UInt64(cst.ROLE_AUTHORITY):
                assert role_address in self.authority, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_ID_AUTHORITY + role_address.bytes)
            case UInt64(cst.ROLE_INTEREST_ORACLE):
                assert role_address in self.interest_oracle, err.INVALID_ROLE_ADDRESS
                op.Box.delete(cst.PREFIX_ID_INTEREST_ORACLE + role_address.bytes)
            case _:
                op.err()
        return arc4.UInt64(Global.latest_timestamp)
