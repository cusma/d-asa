# This file is auto-generated, do not modify
# flake8: noqa
# fmt: off
import typing

import algopy

class RoleValidity(algopy.arc4.Struct):
    role_validity_start: algopy.arc4.UIntN[typing.Literal[64]]
    role_validity_end: algopy.arc4.UIntN[typing.Literal[64]]

class MockRbacModule(algopy.arc4.ARC4Client, typing.Protocol):
    """

        RBAC Module for testing
    
    """
    @algopy.arc4.abimethod(allow_actions=['UpdateApplication'])
    def contract_update(
        self,
    ) -> None:
        """
        Update D-ASA application.
        """

    @algopy.arc4.abimethod
    def rbac_rotate_arranger(
        self,
        new_arranger: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Rotate the arranger address.
        """

    @algopy.arc4.abimethod
    def rbac_set_op_daemon(
        self,
        address: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Non-normative helper to set the operation daemon address.
        """

    @algopy.arc4.abimethod
    def rbac_assign_role(
        self,
        role_id: algopy.arc4.UIntN[typing.Literal[8]],
        role_address: algopy.arc4.Address,
        validity: RoleValidity,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Assign a role to an address.
        """

    @algopy.arc4.abimethod
    def rbac_revoke_role(
        self,
        role_id: algopy.arc4.UIntN[typing.Literal[8]],
        role_address: algopy.arc4.Address,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Revoke a role from an address.
        """

    @algopy.arc4.abimethod
    def rbac_contract_suspension(
        self,
        suspended: algopy.arc4.Bool,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Set the asset-wide suspension status.
        """

    @algopy.arc4.abimethod
    def rbac_contract_default(
        self,
        defaulted: algopy.arc4.Bool,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Set D-ASA default status
        """

    @algopy.arc4.abimethod(readonly=True)
    def rbac_get_arranger(
        self,
    ) -> algopy.arc4.Address:
        """
        Get the arranger address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def rbac_get_address_roles(
        self,
        address: algopy.arc4.Address,
    ) -> algopy.arc4.Tuple[algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.Bool]:
        """
        Non-normative helper to get the active roles assigned to an address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def rbac_get_role_validity(
        self,
        role_id: algopy.arc4.UIntN[typing.Literal[8]],
        role_address: algopy.arc4.Address,
    ) -> RoleValidity:
        """
        Get the stored validity interval for a role assignment.
        """
