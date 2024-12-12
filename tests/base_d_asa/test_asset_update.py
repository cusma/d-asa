import pytest
from algokit_utils import LogicError, OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts import errors as err
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient


def test_pass_update(base_d_asa_client_active: BaseDAsaClient) -> None:
    base_d_asa_client_active.update_bare()


def test_fail_unauthorized(
    oscar: AddressAndSigner, base_d_asa_client_active: BaseDAsaClient
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        base_d_asa_client_active.update_bare(
            transaction_parameters=OnCompleteCallParameters(signer=oscar.signer)
        )
