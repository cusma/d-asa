from algokit_utils import SigningAccount

from smart_contracts.artifacts.mock_module_rbac.mock_rbac_module_client import (
    MockRbacModuleClient,
)


def test_pass_rbac_get_arranger(
    arranger: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    assert rbac_client.send.rbac_get_arranger().abi_return == arranger.address


def test_concrete_pass_rbac_get_arranger(shared_client_empty) -> None:
    assert (
        shared_client_empty.send.rbac_get_arranger().abi_return
        == shared_client_empty.state.global_state.arranger
    )
