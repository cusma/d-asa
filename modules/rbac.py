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
)

from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import errors as err


class RbacModule(ARC4Contract):
    """
    Role-Based Access Control (RBAC) Module

    - Defines and manages roles and permissions for D-ASA RBAC
    - Manages of D-ASA suspension policy
    """

    def __init__(self) -> None:
        # RBAC Roles
        self.arranger = GlobalState(Account(), key=cst.PREFIX_ID_ARRANGER)
        self.op_daemon = GlobalState(Account(), key=cst.PREFIX_ID_OP_DAEMON)
        self.account_manager = BoxMap(
            Account, typ.RoleValidity, key_prefix=cst.PREFIX_ID_ACCOUNT_MANAGER
        )
        self.primary_dealer = BoxMap(
            Account, typ.RoleValidity, key_prefix=cst.PREFIX_ID_PRIMARY_DEALER
        )
        self.trustee = BoxMap(
            Account, typ.RoleValidity, key_prefix=cst.PREFIX_ID_TRUSTEE
        )
        self.authority = BoxMap(
            Account, typ.RoleValidity, key_prefix=cst.PREFIX_ID_AUTHORITY
        )
        self.observer = BoxMap(
            Account, typ.RoleValidity, key_prefix=cst.PREFIX_ID_OBSERVER
        )

        # D-ASA Governance
        self.asset_suspended = False
        self.asset_defaulted = False

    def _is_arranger(self, role_address: Account) -> bool:
        return role_address == self.arranger.value

    def _has_role(self, role_map: typ.RbacRole, role_address: Account) -> bool:
        return role_address in role_map

    def _role_is_active(self, role_map: typ.RbacRole, role_address: Account) -> bool:
        return self._has_role(role_map, role_address) and (
            role_map[role_address].role_validity_start
            <= Global.latest_timestamp
            <= role_map[role_address].role_validity_end
        )

    def assert_caller_is_arranger(self) -> None:
        assert self._is_arranger(Txn.sender), err.UNAUTHORIZED

    def assert_caller_is_account_manager(self) -> None:
        assert self._role_is_active(self.account_manager, Txn.sender), err.UNAUTHORIZED

    def assert_caller_is_primary_dealer(self) -> None:
        assert self._role_is_active(self.primary_dealer, Txn.sender), err.UNAUTHORIZED

    def assert_caller_is_trustee(self) -> None:
        assert self._role_is_active(self.trustee, Txn.sender), err.UNAUTHORIZED

    def assert_caller_is_authority(self) -> None:
        assert self._role_is_active(self.authority, Txn.sender), err.UNAUTHORIZED

    def assert_caller_is_observer(self) -> None:
        assert self._role_is_active(self.observer, Txn.sender), err.UNAUTHORIZED

    def assert_is_not_asset_defaulted(self) -> None:
        assert not self.asset_defaulted, err.DEFAULTED

    def assert_is_not_asset_suspended(self) -> None:
        assert not self.asset_suspended, err.SUSPENDED

    def _assert_valid_role(self, role_id: UInt64) -> None:
        assert role_id in (
            UInt64(cst.ROLE_ARRANGER),
            UInt64(cst.ROLE_ACCOUNT_MANAGER),
            UInt64(cst.ROLE_PRIMARY_DEALER),
            UInt64(cst.ROLE_TRUSTEE),
            UInt64(cst.ROLE_AUTHORITY),
            UInt64(cst.ROLE_OBSERVER),
        ), err.INVALID_ROLE

    def _set_role(
        self, role_id: UInt64, role_address: Account, validity: typ.RoleValidity
    ) -> None:
        if role_id == UInt64(cst.ROLE_ARRANGER):
            self.arranger.value = role_address
            return

        if role_id == UInt64(cst.ROLE_ACCOUNT_MANAGER):
            assert role_address not in self.account_manager, err.INVALID_ROLE_ADDRESS
            self.account_manager[role_address] = validity
            return
        if role_id == UInt64(cst.ROLE_PRIMARY_DEALER):
            assert role_address not in self.primary_dealer, err.INVALID_ROLE_ADDRESS
            self.primary_dealer[role_address] = validity
            return
        if role_id == UInt64(cst.ROLE_TRUSTEE):
            assert role_address not in self.trustee, err.INVALID_ROLE_ADDRESS
            self.trustee[role_address] = validity
            return
        if role_id == UInt64(cst.ROLE_AUTHORITY):
            assert role_address not in self.authority, err.INVALID_ROLE_ADDRESS
            self.authority[role_address] = validity
            return
        if role_id == UInt64(cst.ROLE_OBSERVER):
            assert role_address not in self.observer, err.INVALID_ROLE_ADDRESS
            self.observer[role_address] = validity

    def _delete_role(self, role_id: UInt64, role_address: Account) -> None:
        assert role_id != UInt64(cst.ROLE_ARRANGER), err.INVALID_ROLE
        if role_id == UInt64(cst.ROLE_ACCOUNT_MANAGER):
            assert role_address in self.account_manager, err.INVALID_ROLE_ADDRESS
            del self.account_manager[role_address]
            return
        if role_id == UInt64(cst.ROLE_PRIMARY_DEALER):
            assert role_address in self.primary_dealer, err.INVALID_ROLE_ADDRESS
            del self.primary_dealer[role_address]
            return
        if role_id == UInt64(cst.ROLE_TRUSTEE):
            assert role_address in self.trustee, err.INVALID_ROLE_ADDRESS
            del self.trustee[role_address]
            return
        if role_id == UInt64(cst.ROLE_AUTHORITY):
            assert role_address in self.authority, err.INVALID_ROLE_ADDRESS
            del self.authority[role_address]
            return
        if role_id == UInt64(cst.ROLE_OBSERVER):
            assert role_address in self.observer, err.INVALID_ROLE_ADDRESS
            del self.observer[role_address]

    @arc4.abimethod
    def rbac_rotate_arranger(self, *, new_arranger: Account) -> UInt64:
        """
        Rotate the Arranger address

        Args:
            new_arranger: New Arranger address

        Returns:
            Timestamp of the role assignment
        """
        self.assert_caller_is_arranger()
        self.arranger.value = new_arranger
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_set_op_daemon(self, *, address: Account) -> UInt64:
        """
        Non-Normative: Set the Operation Daemon address

        Args:
            address: Operation Daemon address

        Returns:
            Timestamp of the role assignment
        """
        self.assert_caller_is_arranger()
        self.op_daemon.value = address
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_assign_role(
        self, *, role_id: arc4.UInt8, role_address: Account, config: typ.RoleValidity
    ) -> UInt64:
        """
        Assign a role to an address

        Args:
            role_id: Role Identifier
            role_address: Account Role Address
            validity: Role time validity

        Returns:
            Timestamp of the role assignment

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_ROLE: Invalid role identifier
            INVALID_ROLE_ADDRESS: Invalid account role address
        """

        self.assert_caller_is_arranger()
        self.assert_is_not_asset_defaulted()
        self._assert_valid_role(role_id.as_uint64())
        self._upsert_role(role_id.as_uint64(), role_address, config)
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_revoke_role(self, *, role_id: arc4.UInt8, role_address: Account) -> UInt64:
        """
        Revoke a role from an address

        Args:
            role_id: Role Identifier
            role_address: Account Role Address

        Returns:
            Timestamp of the role revocation

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_ROLE: Invalid role identifier
            INVALID_ROLE_ADDRESS: Invalid account role address
        """

        self.assert_caller_is_arranger()
        self.assert_is_not_asset_defaulted()
        self._assert_valid_role(role_id.as_uint64())
        self._delete_role(role_id.as_uint64(), role_address)
        return Global.latest_timestamp

    @arc4.abimethod  # TODO: Update specs and add test
    def rbac_gov_asset_suspension(self, *, suspended: bool) -> UInt64:
        """
        Set asset suspension status

        Args:
            suspended: Suspension status

        Returns:
            Timestamp of the set asset suspension status

        Raises:
            UNAUTHORIZED: Not authorized
        """

        self.assert_caller_is_authority()
        self.asset_suspended = suspended
        return Global.latest_timestamp

    @arc4.abimethod(readonly=True)
    def rbac_get_arranger(self) -> Account:
        """
        Get Arranger address

        Returns:
            Arranger address
        """
        return self.arranger.value

    @arc4.abimethod(readonly=True)
    def rbac_get_address_roles(
        self, address: Account
    ) -> tuple[bool, bool, bool, bool, bool]:
        """
        Non-normative - Get roles assigned to an address

        Args:
            address: Address to get roles for

        Returns:
            Roles mask: (Account Manager, Primary Dealer, Trustee, Authority, Interest Oracle)
        """
        return (
            self._role_is_active(self.account_manager, address),
            self._role_is_active(self.primary_dealer, address),
            self._role_is_active(self.trustee, address),
            self._role_is_active(self.authority, address),
            self._role_is_active(self.interest_oracle, address),
        )

    @arc4.abimethod(readonly=True)
    def rbac_get_role_config(
        self, *, role_id: arc4.UInt8, role_address: Account
    ) -> typ.RoleConfig:
        """
        Get role configuration

        Args:
            role_id: Role Identifier
            role_address: Account Role Address

        Returns:
            Role configuration
        """
        role = role_id.as_uint64()
        self._assert_valid_role(role)
        match role:
            case UInt64(cst.ROLE_ARRANGER):
                return typ.RoleConfig(
                    role_validity_start=UInt64(0), role_validity_end=UInt64(0)
                )
            case UInt64(cst.ROLE_ACCOUNT_MANAGER):
                assert self._has_role(
                    self.account_manager, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.account_manager[role_address]
            case UInt64(cst.ROLE_PRIMARY_DEALER):
                assert self._has_role(
                    self.primary_dealer, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.primary_dealer[role_address]
            case UInt64(cst.ROLE_TRUSTEE):
                assert self._has_role(
                    self.trustee, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.trustee[role_address]
            case UInt64(cst.ROLE_AUTHORITY):
                assert self._has_role(
                    self.authority, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.authority[role_address]
            case UInt64(cst.ROLE_INTEREST_ORACLE):
                assert self._has_role(
                    self.interest_oracle, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.interest_oracle[role_address]
            case _:
                op.err(err.INVALID_ROLE)
