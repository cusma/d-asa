from src.localnet import (
    DEFAULT_ALGOD_PORT,
    DEFAULT_INDEXER_PORT,
    DEFAULT_KMD_PORT,
    DEFAULT_LOCALNET_TOKEN,
    LocalNetConfig,
    load_localnet_config,
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

    config = load_localnet_config(default_host="ignored")

    assert config == LocalNetConfig(
        host="demo-net",
        token="token",
        algod_port=14001,
        kmd_port=14002,
        indexer_port=18980,
    )
    assert config.algod_client_config().server == "http://demo-net"
    assert config.algod_client_config().port == 14001
