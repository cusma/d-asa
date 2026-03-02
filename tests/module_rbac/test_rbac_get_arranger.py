from algokit_utils import SigningAccount

from smart_contracts.artifacts.mock_rbac_module.mock_rbac_module_client import (
    MockRbacModuleClient,
)


def test_pass_rbac_get_arranger(
    arranger: SigningAccount,
    rbac_client: MockRbacModuleClient,
) -> None:
    assert rbac_client.send.rbac_get_arranger().abi_return == arranger.address
