import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err
from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
    SetDefaultStatusArgs,
)
from tests.utils import DAsaTrustee


def test_pass_set_default_status(
    trustee: DAsaTrustee,
    rbac_client: MockRbacModuleClient,
) -> None:
    assert not rbac_client.state.global_state.asset_defaulted
    rbac_client.send.set_default_status(
        SetDefaultStatusArgs(defaulted=True),
        params=CommonAppCallParams(sender=trustee.address),
    )
    assert rbac_client.state.global_state.asset_defaulted


def test_fail_unauthorized(
    no_role_account: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rbac_client.send.set_default_status(
            SetDefaultStatusArgs(defaulted=True),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_concrete_pass_set_default_status(
    shared_trustee,
    shared_client_active,
) -> None:
    shared_client_active.send.set_default_status(
        (True,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    assert shared_client_active.state.global_state.asset_defaulted

    shared_client_active.send.set_default_status(
        (False,),
        params=CommonAppCallParams(sender=shared_trustee.address),
    )
    assert not shared_client_active.state.global_state.asset_defaulted


def test_concrete_fail_unauthorized(
    no_role_account: SigningAccount,
    shared_client_active,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_active.send.set_default_status(
            (True,),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
