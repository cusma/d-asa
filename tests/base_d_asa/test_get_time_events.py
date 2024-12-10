from algokit_utils import OnCompleteCallParameters

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from tests.utils import DAsaConfig


def test_pass_get_time_events(
    base_d_asa_cfg: DAsaConfig, base_d_asa_client_active: BaseDAsaClient
) -> None:
    time_events = base_d_asa_client_active.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(base_d_asa_client_active.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value
    assert time_events == base_d_asa_cfg.time_events


def test_pass_not_configured(base_d_asa_client_empty: BaseDAsaClient) -> None:
    time_events = base_d_asa_client_empty.get_time_events(
        transaction_parameters=OnCompleteCallParameters(
            boxes=[(base_d_asa_client_empty.app_id, sc_cst.BOX_ID_TIME_EVENTS)]
        )
    ).return_value
    assert not time_events
