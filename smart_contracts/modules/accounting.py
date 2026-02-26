# pyright: reportMissingModuleSource=false

from algopy import Account, BoxMap, Global, Txn, UInt64, arc4

from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import enums as enm
from smart_contracts import errors as err
from smart_contracts.modules.rbac import RbacModule


class AccountingModule(RbacModule):
    def __init__(self) -> None:
        super().__init__()

        self.account = BoxMap(
            Account, typ.AccountInfo, key_prefix=cst.PREFIX_ID_ACCOUNT
        )
        self.total_units = UInt64(0)
        self.circulating_units = UInt64(0)
        self.unit_value = UInt64(0)
        self.status = UInt64(enm.STATUS_INACTIVE)

    def status_is_active(self) -> bool:
        return self.status == enm.STATUS_ACTIVE

    def status_is_ended(self) -> bool:
        return self.status == enm.STATUS_ENDED

    def assert_valid_holding_address(self, holding_address: Account) -> None:
        assert holding_address in self.account, err.INVALID_HOLDING_ADDRESS

    def account_units_value(self, holding_address: Account, units: UInt64) -> UInt64:
        return units * self.account[holding_address].unit_value

    def account_total_units_value(self, holding_address: Account) -> UInt64:
        return self.account_units_value(
            holding_address, self.account[holding_address].units
        )

    def outstanding_principal(self) -> UInt64:
        return self.circulating_units * self.unit_value

    def end_if_no_circulating_units(self) -> None:
        if self.circulating_units == UInt64(0):
            self.status = UInt64(enm.STATUS_ENDED)

    def reset_position_if_empty(self, holding_address: Account) -> None:
        if self.account[holding_address].units == UInt64(0):
            self.account[holding_address].unit_value = UInt64(0)
            self.account[holding_address].paid_coupons = UInt64(0)

    def assert_are_units_fungible(self, sender: Account, receiver: Account) -> None:
        assert (
            self.account[sender].unit_value == self.account[receiver].unit_value
            and self.account[sender].paid_coupons == self.account[receiver].paid_coupons
        ), err.NON_FUNGIBLE_UNITS

    def assert_fungible_transfer(self, sender: Account, receiver: Account) -> None:
        sender_unit_value = self.account[sender].unit_value
        if self.account[receiver].units > UInt64(0):
            self.assert_are_units_fungible(sender, receiver)
        else:
            self.account[receiver].unit_value = sender_unit_value
            self.account[receiver].paid_coupons = self.account[sender].paid_coupons

    def debit_units(self, holding_address: Account, units: UInt64) -> None:
        assert units <= self.account[holding_address].units, err.OVER_TRANSFER
        self.account[holding_address].units -= units
        self.reset_position_if_empty(holding_address)

    def credit_units(self, holding_address: Account, units: UInt64) -> None:
        self.account[holding_address].units += units

    def transfer_units(
        self,
        sender_holding_address: Account,
        receiver_holding_address: Account,
        units: UInt64,
    ) -> None:
        self.debit_units(sender_holding_address, units)
        self.credit_units(receiver_holding_address, units)

    def apply_principal_redemption(self, holding_address: Account) -> None:
        redeemed_units = self.account[holding_address].units
        self.circulating_units -= redeemed_units
        self.account[holding_address].units = UInt64(0)
        self.reset_position_if_empty(holding_address)
        self.end_if_no_circulating_units()

    @arc4.abimethod
    def set_account_suspension(
        self, *, holding_address: Account, suspended: bool
    ) -> UInt64:
        """
        Set account suspension status

        Args:
            holding_address: Account Holding Address
            suspended: Suspension status

        Returns:
            Timestamp of the set account suspension status

        Raises:
            UNAUTHORIZED: Not authorized
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_caller_is_authority()
        self.assert_valid_holding_address(holding_address)
        self.account[holding_address].suspended = suspended
        return Global.latest_timestamp

    @arc4.abimethod
    def account_open(
        self, *, holding_address: Account, payment_address: Account
    ) -> UInt64:
        """
        Open D-ASA account

        Args:
            holding_address: Account Holding Address
            payment_address: Account Payment Address

        Returns:
            Timestamp of the account opening

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            SUSPENDED: Suspended
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """

        self.assert_caller_is_account_manager()
        assert not self.status_is_ended(), err.UNAUTHORIZED
        self.assert_is_not_asset_defaulted()
        self.assert_is_not_asset_suspended()
        assert holding_address not in self.account, err.INVALID_HOLDING_ADDRESS

        self.account[holding_address] = typ.AccountInfo(
            payment_address=payment_address,
            units=UInt64(0),
            unit_value=UInt64(0),
            paid_coupons=UInt64(0),
            suspended=False,
        )
        return Global.latest_timestamp

    @arc4.abimethod
    def account_close(self, *, holding_address: Account) -> tuple[UInt64, UInt64]:
        """
        Close D-ASA account

        Args:
            holding_address: Account Holding Address

        Returns:
            Closed units, Timestamp of the account closing

        Raises:
            UNAUTHORIZED: Not authorized
            DEFAULTED: Defaulted
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """

        self.assert_caller_is_account_manager()
        self.assert_is_not_asset_defaulted()
        self.assert_valid_holding_address(holding_address)

        closed_units = self.account[holding_address].units
        del self.account[holding_address]
        self.circulating_units -= closed_units
        self.end_if_no_circulating_units()
        return closed_units, Global.latest_timestamp

    @arc4.abimethod
    def account_update_payment_address(
        self, *, holding_address: Account, payment_address: Account
    ) -> UInt64:
        self.assert_valid_holding_address(holding_address)
        assert Txn.sender == holding_address, err.UNAUTHORIZED
        self.account[holding_address].payment_address = payment_address
        return Global.latest_timestamp

    @arc4.abimethod(readonly=True)
    def account_get_info(self, *, holding_address: Account) -> typ.AccountInfo:
        """
        Get account info

        Args:
            holding_address: Account Holding Address

        Returns:
            Payment Address, D-ASA units, Unit nominal value in denomination asset, Paid coupons, Suspended

        Raises:
            INVALID_HOLDING_ADDRESS: Invalid account holding address
        """
        self.assert_valid_holding_address(holding_address)
        return self.account[holding_address]

    # TODO: This seems contract-type dependent, not enough general for accounting
    # @arc4.abimethod(readonly=True)
    # def account_get_units_value(self, *, holding_address: Account, units: UInt64) -> UInt64:
    #     self.assert_valid_holding_address(holding_address)
    #     assert 0 < units <= self.account[holding_address].units, err.INVALID_UNITS
    #     return self.account_units_value(holding_address, units)
