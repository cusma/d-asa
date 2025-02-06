from algokit_utils import AlgorandClient

from tests.utils import get_last_round, get_latest_timestamp, round_warp, time_warp


def test_round_warp(algorand: AlgorandClient) -> None:
    current_round = get_last_round(algorand.client.algod)
    to_round = current_round + 10
    round_warp(to_round)
    current_round = get_last_round(algorand.client.algod)
    assert current_round == to_round

    round_warp()
    current_round = get_last_round(algorand.client.algod)
    assert current_round == to_round + 1


def test_time_warp(algorand: AlgorandClient) -> None:
    current_ts = get_latest_timestamp(algorand.client.algod)
    to_timestamp = current_ts + 420
    time_warp(to_timestamp)
    current_ts = get_latest_timestamp(algorand.client.algod)
    assert current_ts == to_timestamp
