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
from smart_contracts import enums
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

        # Contract Governance
        self.contract_suspended = False

        # Contract Performance
        self.defaulted = False

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

    def _assert_caller_is_arranger(self) -> None:
        assert self._is_arranger(Txn.sender), err.UNAUTHORIZED

    def _assert_valid_arranger_address(self, role_address: Account) -> None:
        assert role_address != Global.zero_address, err.INVALID_ROLE_ADDRRESS

    def _assert_caller_is_account_manager(self) -> None:
        assert self._role_is_active(self.account_manager, Txn.sender), err.UNAUTHORIZED

    def _assert_caller_is_primary_dealer(self) -> None:
        assert self._role_is_active(self.primary_dealer, Txn.sender), err.UNAUTHORIZED

    def _assert_caller_is_trustee(self) -> None:
        assert self._role_is_active(self.trustee, Txn.sender), err.UNAUTHORIZED

    def _assert_caller_is_authority(self) -> None:
        assert self._role_is_active(self.authority, Txn.sender), err.UNAUTHORIZED

    def _assert_caller_is_observer(self) -> None:
        assert self._role_is_active(self.observer, Txn.sender), err.UNAUTHORIZED

    def _assert_is_not_contract_defaulted(self) -> None:
        assert not self.defaulted, err.DEFAULTED

    def _assert_is_not_contract_suspended(self) -> None:
        assert not self.contract_suspended, err.SUSPENDED

    def _assert_valid_role(self, role_id: UInt64) -> None:
        assert role_id in (
            UInt64(enums.ROLE_ARRANGER),
            UInt64(enums.ROLE_OP_DAEMON),
            UInt64(enums.ROLE_ACCOUNT_MANAGER),
            UInt64(enums.ROLE_PRIMARY_DEALER),
            UInt64(enums.ROLE_TRUSTEE),
            UInt64(enums.ROLE_AUTHORITY),
            UInt64(enums.ROLE_OBSERVER),
        ), err.INVALID_ROLE

    def _set_role(
        self, role_id: UInt64, role_address: Account, validity: typ.RoleValidity
    ) -> None:
        # Arranger role is rotated with a dedicated ABI

        if role_id == UInt64(enums.ROLE_ACCOUNT_MANAGER):
            assert role_address not in self.account_manager, err.INVALID_ROLE_ADDRESS
            self.account_manager[role_address] = validity.copy()
            return
        if role_id == UInt64(enums.ROLE_PRIMARY_DEALER):
            assert role_address not in self.primary_dealer, err.INVALID_ROLE_ADDRESS
            self.primary_dealer[role_address] = validity.copy()
            return
        if role_id == UInt64(enums.ROLE_TRUSTEE):
            assert role_address not in self.trustee, err.INVALID_ROLE_ADDRESS
            self.trustee[role_address] = validity.copy()
            return
        if role_id == UInt64(enums.ROLE_AUTHORITY):
            assert role_address not in self.authority, err.INVALID_ROLE_ADDRESS
            self.authority[role_address] = validity.copy()
            return
        if role_id == UInt64(enums.ROLE_OBSERVER):
            assert role_address not in self.observer, err.INVALID_ROLE_ADDRESS
            self.observer[role_address] = validity.copy()

    def _delete_role(self, role_id: UInt64, role_address: Account) -> None:
        assert role_id != UInt64(enums.ROLE_ARRANGER), err.INVALID_ROLE
        if role_id == UInt64(enums.ROLE_ACCOUNT_MANAGER):
            assert role_address in self.account_manager, err.INVALID_ROLE_ADDRESS
            del self.account_manager[role_address]
            return
        if role_id == UInt64(enums.ROLE_PRIMARY_DEALER):
            assert role_address in self.primary_dealer, err.INVALID_ROLE_ADDRESS
            del self.primary_dealer[role_address]
            return
        if role_id == UInt64(enums.ROLE_TRUSTEE):
            assert role_address in self.trustee, err.INVALID_ROLE_ADDRESS
            del self.trustee[role_address]
            return
        if role_id == UInt64(enums.ROLE_AUTHORITY):
            assert role_address in self.authority, err.INVALID_ROLE_ADDRESS
            del self.authority[role_address]
            return
        if role_id == UInt64(enums.ROLE_OBSERVER):
            assert role_address in self.observer, err.INVALID_ROLE_ADDRESS
            del self.observer[role_address]

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def contract_update(self) -> None:
        """
        Update D-ASA application.

        Returns:
            None.

        Raises:
            UNAUTHORIZED: Caller is not the arranger.
        """
        # The reference implementation grants the update permissions to the Arranger.
        # ⚠️ WARNING: Application updates must be executed VERY carefully, as they
        # might introduce breaking changes.
        self._assert_caller_is_arranger()

    @arc4.abimethod
    def rbac_rotate_arranger(self, *, new_arranger: Account) -> UInt64:
        """
        Rotate the arranger address.

        Args:
            new_arranger: New arranger address.

        Returns:
            UNIX timestamp of the role assignment.

        Raises:
            UNAUTHORIZED: Caller is not the current arranger.
            INVALID_ROLE_ADDRESS: Arranger address must not be the global zero address.
        """
        self._assert_caller_is_arranger()
        self._assert_valid_arranger_address(new_arranger)
        self.arranger.value = new_arranger
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_set_op_daemon(self, *, address: Account) -> UInt64:
        """
        Non-normative helper to set the operation daemon address.

        Args:
            address: Operation daemon address.

        Returns:
            UNIX timestamp of the role assignment.

        Raises:
            UNAUTHORIZED: Caller is not the arranger.
        """
        self._assert_caller_is_arranger()
        self.op_daemon.value = address
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_assign_role(
        self, *, role_id: arc4.UInt8, role_address: Account, validity: typ.RoleValidity
    ) -> UInt64:
        """
        Assign a role to an address.

        Args:
            role_id: Role identifier.
            role_address: Account role address.
            validity: Inclusive validity interval for the assignment.

        Returns:
            UNIX timestamp of the role assignment.

        Raises:
            UNAUTHORIZED: Caller is not the arranger.
            DEFAULTED: Asset is defaulted.
            INVALID_ROLE: Role identifier is not supported.
            INVALID_ROLE_ADDRESS: Address is invalid for the requested role.
        """

        self._assert_caller_is_arranger()
        self._assert_is_not_contract_defaulted()
        self._assert_valid_role(role_id.as_uint64())
        self._set_role(role_id.as_uint64(), role_address, validity)
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_revoke_role(self, *, role_id: arc4.UInt8, role_address: Account) -> UInt64:
        """
        Revoke a role from an address.

        Args:
            role_id: Role identifier.
            role_address: Account role address.

        Returns:
            UNIX timestamp of the role revocation.

        Raises:
            UNAUTHORIZED: Caller is not the arranger.
            DEFAULTED: Asset is defaulted.
            INVALID_ROLE: Role identifier is not supported.
            INVALID_ROLE_ADDRESS: Address is not currently assigned to that role.
        """

        self._assert_caller_is_arranger()
        self._assert_is_not_contract_defaulted()
        self._assert_valid_role(role_id.as_uint64())
        self._delete_role(role_id.as_uint64(), role_address)
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_contract_suspension(self, *, suspended: bool) -> UInt64:
        """
        Set the asset-wide suspension status.

        Args:
            suspended: Suspension status to apply.

        Returns:
            UNIX timestamp of the suspension update.

        Raises:
            UNAUTHORIZED: Caller is not an active authority.
        """

        self._assert_caller_is_authority()
        self.contract_suspended = suspended
        return Global.latest_timestamp

    @arc4.abimethod
    def rbac_contract_default(self, *, defaulted: bool) -> UInt64:
        """
        Set D-ASA default status

        Args:
            defaulted: Default status

        Raises:
            UNAUTHORIZED: Not authorized
        """

        self._assert_caller_is_trustee()
        self.defaulted = defaulted
        return Global.latest_timestamp

    @arc4.abimethod(readonly=True)
    def rbac_get_arranger(self) -> Account:
        """
        Get the arranger address.

        Returns:
            Current arranger address.

        Raises:
            None: This method does not raise contract-specific errors.
        """
        return self.arranger.value

    @arc4.abimethod(readonly=True)
    def rbac_get_address_roles(
        self, address: Account
    ) -> tuple[bool, bool, bool, bool, bool]:
        """
        Non-normative helper to get the active roles assigned to an address.

        Args:
            address: Address to query.

        Returns:
            Roles mask in the order: account manager, primary dealer, trustee,
            authority, observer.

        Raises:
            None: This method does not raise contract-specific errors.
        """
        return (
            self._role_is_active(self.account_manager, address),
            self._role_is_active(self.primary_dealer, address),
            self._role_is_active(self.trustee, address),
            self._role_is_active(self.authority, address),
            self._role_is_active(self.observer, address),
        )

    @arc4.abimethod(readonly=True)
    def rbac_get_role_validity(
        self, *, role_id: arc4.UInt8, role_address: Account
    ) -> typ.RoleValidity:
        """
        Get the stored validity interval for a role assignment.

        Args:
            role_id: Role identifier.
            role_address: Account role address.

        Returns:
            Stored role validity interval.

        Raises:
            INVALID_ROLE: Role identifier is not supported.
            INVALID_ROLE_ADDRESS: Address is not assigned to that role.
        """
        role = role_id.as_uint64()
        self._assert_valid_role(role)
        match role:
            case UInt64(enums.ROLE_ARRANGER):
                return typ.RoleValidity(
                    role_validity_start=UInt64(0), role_validity_end=UInt64(0)
                )
            case UInt64(enums.ROLE_ACCOUNT_MANAGER):
                assert self._has_role(
                    self.account_manager, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.account_manager[role_address]
            case UInt64(enums.ROLE_PRIMARY_DEALER):
                assert self._has_role(
                    self.primary_dealer, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.primary_dealer[role_address]
            case UInt64(enums.ROLE_TRUSTEE):
                assert self._has_role(
                    self.trustee, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.trustee[role_address]
            case UInt64(enums.ROLE_AUTHORITY):
                assert self._has_role(
                    self.authority, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.authority[role_address]
            case UInt64(enums.ROLE_OBSERVER):
                assert self._has_role(
                    self.observer, role_address
                ), err.INVALID_ROLE_ADDRESS
                return self.observer[role_address]
            case _:
                op.err(err.INVALID_ROLE)
