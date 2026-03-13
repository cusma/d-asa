from types import SimpleNamespace
from urllib.error import URLError

from d_asa.localnet import (
    DEFAULT_ALGOD_PORT,
    DEFAULT_INDEXER_PORT,
    DEFAULT_KMD_PORT,
    DEFAULT_LOCALNET_TOKEN,
    LocalNetConfig,
    load_localnet_config,
    wait_for_localnet,
)


def test_load_localnet_config_uses_defaults_for_demo_host(monkeypatch) -> None:
    monkeypatch.delenv("D_ASA_LOCALNET_HOST", raising=False)
    monkeypatch.delenv("D_ASA_LOCALNET_TOKEN", raising=False)
    monkeypatch.delenv("D_ASA_ALGOD_PORT", raising=False)
    monkeypatch.delenv("D_ASA_KMD_PORT", raising=False)
    monkeypatch.delenv("D_ASA_INDEXER_PORT", raising=False)

    config = load_localnet_config(default_host="host.docker.internal")

    assert config == LocalNetConfig(
        host="host.docker.internal",
        token=DEFAULT_LOCALNET_TOKEN,
        algod_port=DEFAULT_ALGOD_PORT,
        kmd_port=DEFAULT_KMD_PORT,
        indexer_port=DEFAULT_INDEXER_PORT,
    )


def test_load_localnet_config_reads_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("D_ASA_LOCALNET_HOST", "demo-net")
    monkeypatch.setenv("D_ASA_LOCALNET_TOKEN", "token")
    monkeypatch.setenv("D_ASA_ALGOD_PORT", "14001")
    monkeypatch.setenv("D_ASA_KMD_PORT", "14002")
    monkeypatch.setenv("D_ASA_INDEXER_PORT", "18980")
    monkeypatch.setenv("D_ASA_ALGOD_HOST", "algod-net")
    monkeypatch.setenv("D_ASA_KMD_HOST", "kmd-net")
    monkeypatch.setenv("D_ASA_INDEXER_HOST", "indexer-net")

    config = load_localnet_config(default_host="ignored")

    assert config == LocalNetConfig(
        host="demo-net",
        token="token",
        algod_port=14001,
        kmd_port=14002,
        indexer_port=18980,
        algod_host="algod-net",
        kmd_host="kmd-net",
        indexer_host="indexer-net",
    )
    assert config.algod_client_config().server == "http://algod-net"
    assert config.algod_client_config().port == 14001
    assert config.kmd_client_config().server == "http://kmd-net"
    assert config.indexer_client_config().server == "http://indexer-net"


def test_round_warp_retries_on_transient_algod_timeout(monkeypatch) -> None:
    wait_calls: list[tuple[float, float]] = []

    def fake_wait_for_algod(
        *,
        localnet_config: LocalNetConfig | None = None,
        timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 2.0,
    ) -> None:
        del localnet_config
        wait_calls.append((timeout_seconds, poll_interval_seconds))

    class FakeSend:
        def __init__(self) -> None:
            self.calls = 0

        def payment(self, params: object) -> None:
            del params
            self.calls += 1
            if self.calls == 1:
                raise URLError(TimeoutError("timed out"))

    fake_send = FakeSend()
    fake_algorand = SimpleNamespace(
        account=SimpleNamespace(
            localnet_dispenser=lambda: SimpleNamespace(signer=object(), address="ADDR")
        ),
        send=fake_send,
    )

    monkeypatch.setattr("d_asa.localnet.wait_for_algod", fake_wait_for_algod)

    from d_asa.localnet import round_warp

    round_warp(algorand=fake_algorand)  # type: ignore[arg-type]

    assert fake_send.calls == 2
    assert wait_calls == [(15.0, 1.0)]


def test_wait_for_localnet_checks_algod_then_kmd(monkeypatch) -> None:
    calls: list[str] = []

    def fake_wait_for_algod(**_: object) -> None:
        calls.append("algod")

    def fake_wait_for_kmd(**_: object) -> None:
        calls.append("kmd")

    monkeypatch.setattr("d_asa.localnet.wait_for_algod", fake_wait_for_algod)
    monkeypatch.setattr("d_asa.localnet.wait_for_kmd", fake_wait_for_kmd)

    wait_for_localnet()

    assert calls == ["algod", "kmd"]
