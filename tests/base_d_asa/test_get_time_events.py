from smart_contracts.artifacts.base_d_asa.base_d_asa_client import BaseDAsaClient
from tests.utils import DAsaConfig


def test_pass_get_time_events(
    base_d_asa_cfg: DAsaConfig, base_d_asa_client_active: BaseDAsaClient
) -> None:
    time_events = base_d_asa_client_active.send.get_time_events().abi_return
    assert time_events == base_d_asa_cfg.time_events


def test_pass_not_configured(base_d_asa_client_empty: BaseDAsaClient) -> None:
    time_events = base_d_asa_client_empty.send.get_time_events().abi_return
    assert not time_events
