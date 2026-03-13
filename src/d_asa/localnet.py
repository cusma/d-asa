from __future__ import annotations

import argparse
import os
import struct
import time
from base64 import b64decode
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    PaymentParams,
    SendAppTransactionResult,
    SigningAccount,
)
from algokit_utils.config import config as algokit_config
from algokit_utils.models.network import AlgoClientNetworkConfig
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient

from . import enums
from .artifacts.dasa_client import AccountGetPositionArgs

DEFAULT_LOCALNET_HOST = "localhost"
DEFAULT_LOCALNET_TOKEN = "a" * 64
DEFAULT_ALGOD_PORT = 4001
DEFAULT_KMD_PORT = 4002
DEFAULT_INDEXER_PORT = 8980
DEFAULT_INITIAL_ALGO_FUNDS = AlgoAmount.from_algo(10_000)
ROUND_WARP_MAX_ATTEMPTS = 3


@dataclass(frozen=True, slots=True)
class LocalNetConfig:
    host: str = DEFAULT_LOCALNET_HOST
    token: str = DEFAULT_LOCALNET_TOKEN
    algod_port: int = DEFAULT_ALGOD_PORT
    kmd_port: int = DEFAULT_KMD_PORT
    indexer_port: int = DEFAULT_INDEXER_PORT
    algod_host: str | None = None
    kmd_host: str | None = None
    indexer_host: str | None = None

    @property
    def server(self) -> str:
        return f"http://{self.host}"

    @property
    def algod_server(self) -> str:
        return f"http://{self.algod_host or self.host}"

    @property
    def kmd_server(self) -> str:
        return f"http://{self.kmd_host or self.host}"

    @property
    def indexer_server(self) -> str:
        return f"http://{self.indexer_host or self.host}"

    @property
    def algod_address(self) -> str:
        return f"{self.algod_server}:{self.algod_port}"

    @property
    def kmd_address(self) -> str:
        return f"{self.kmd_server}:{self.kmd_port}"

    @property
    def indexer_address(self) -> str:
        return f"{self.indexer_server}:{self.indexer_port}"

    def algod_client_config(self) -> AlgoClientNetworkConfig:
        return AlgoClientNetworkConfig(
            server=self.algod_server,
            token=self.token,
            port=self.algod_port,
        )

    def indexer_client_config(self) -> AlgoClientNetworkConfig:
        return AlgoClientNetworkConfig(
            server=self.indexer_server,
            token=self.token,
            port=self.indexer_port,
        )

    def kmd_client_config(self) -> AlgoClientNetworkConfig:
        return AlgoClientNetworkConfig(
            server=self.kmd_server,
            token=self.token,
            port=self.kmd_port,
        )


@dataclass(frozen=True, slots=True)
class Currency:
    id: int
    total: int
    decimals: int
    name: str
    unit_name: str
    asa_to_unit: float


@dataclass(kw_only=True)
class DAsaAccountManager(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_ACCOUNT_MANAGER


@dataclass(kw_only=True)
class DAsaPrimaryDealer(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_PRIMARY_DEALER


@dataclass(kw_only=True)
class DAsaTrustee(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_TRUSTEE


@dataclass(kw_only=True)
class DAsaAuthority(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_AUTHORITY


@dataclass(kw_only=True)
class DAsaInterestOracle(SigningAccount):
    @classmethod
    def role_id(cls) -> int:
        return enums.ROLE_OBSERVER


@dataclass(kw_only=True)
class DAsaAccount(SigningAccount):
    holding_address: str
    d_asa_client: Any

    @property
    def payment_address(self) -> str:
        return self.d_asa_client.send.account_get_position(
            AccountGetPositionArgs(
                holding_address=self.holding_address,
            )
        ).abi_return.payment_address

    @property
    def units(self) -> int:
        return self.d_asa_client.send.account_get_position(
            AccountGetPositionArgs(holding_address=self.holding_address)
        ).abi_return.units

    @property
    def suspended(self) -> bool:
        return self.d_asa_client.send.account_get_position(
            AccountGetPositionArgs(holding_address=self.holding_address)
        ).abi_return.suspended


def load_localnet_config(default_host: str = DEFAULT_LOCALNET_HOST) -> LocalNetConfig:
    return LocalNetConfig(
        host=os.getenv("D_ASA_LOCALNET_HOST", default_host),
        token=os.getenv("D_ASA_LOCALNET_TOKEN", DEFAULT_LOCALNET_TOKEN),
        algod_port=int(os.getenv("D_ASA_ALGOD_PORT", str(DEFAULT_ALGOD_PORT))),
        kmd_port=int(os.getenv("D_ASA_KMD_PORT", str(DEFAULT_KMD_PORT))),
        indexer_port=int(os.getenv("D_ASA_INDEXER_PORT", str(DEFAULT_INDEXER_PORT))),
        algod_host=os.getenv("D_ASA_ALGOD_HOST"),
        kmd_host=os.getenv("D_ASA_KMD_HOST"),
        indexer_host=os.getenv("D_ASA_INDEXER_HOST"),
    )


def algorand_client_from_localnet(
    localnet_config: LocalNetConfig | None = None,
) -> AlgorandClient:
    localnet = localnet_config or load_localnet_config()
    algokit_config.configure(
        debug=True,
        populate_app_call_resources=True,
    )
    client = AlgorandClient.from_config(
        algod_config=localnet.algod_client_config(),
        indexer_config=localnet.indexer_client_config(),
        kmd_config=localnet.kmd_client_config(),
    )
    client.set_suggested_params_cache_timeout(0)
    return client


def get_last_round(algod_client: AlgodClient) -> int:
    return int(algod_client.status()["last-round"])  # type: ignore[index]


def get_latest_timestamp(algod_client: AlgodClient) -> int:
    block = algod_client.block_info(get_last_round(algod_client))["block"]  # type: ignore[index]
    return int(block["ts"])  # type: ignore[index]


def round_warp(
    to_round: int | None = None,
    *,
    algorand: AlgorandClient | None = None,
    localnet_config: LocalNetConfig | None = None,
) -> None:
    algorand_client = algorand or algorand_client_from_localnet(localnet_config)
    dispenser = algorand_client.account.localnet_dispenser()
    if to_round is not None:
        last_round = get_last_round(algorand_client.client.algod)
        if to_round <= last_round:
            raise ValueError("to_round must be greater than the latest round")
        n_rounds = to_round - last_round
    else:
        n_rounds = 1

    for _ in range(n_rounds):
        for attempt in range(1, ROUND_WARP_MAX_ATTEMPTS + 1):
            try:
                algorand_client.send.payment(
                    PaymentParams(
                        signer=dispenser.signer,
                        sender=dispenser.address,
                        receiver=dispenser.address,
                        amount=AlgoAmount.from_algo(0),
                    )
                )
                break
            except (TimeoutError, URLError, ConnectionError):
                if attempt == ROUND_WARP_MAX_ATTEMPTS:
                    raise
                wait_for_algod(
                    localnet_config=localnet_config,
                    timeout_seconds=15.0,
                    poll_interval_seconds=1.0,
                )


def time_warp(
    to_timestamp: int,
    *,
    algorand: AlgorandClient | None = None,
    localnet_config: LocalNetConfig | None = None,
) -> None:
    algorand_client = algorand or algorand_client_from_localnet(localnet_config)
    algod_client = algorand_client.client.algod
    algod_client.set_timestamp_offset(to_timestamp - get_latest_timestamp(algod_client))
    round_warp(algorand=algorand_client, localnet_config=localnet_config)
    algod_client.set_timestamp_offset(0)


def wait_for_algod(
    *,
    localnet_config: LocalNetConfig | None = None,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 2.0,
) -> None:
    localnet = localnet_config or load_localnet_config()
    algod_client = AlgodClient(localnet.token, localnet.algod_address)
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            status = algod_client.status()
            if "last-round" in status:
                return
        except Exception as exc:  # pragma: no cover - exercised via CLI/manual flow
            last_error = exc
        time.sleep(poll_interval_seconds)

    message = f"Timed out waiting for algod at {localnet.algod_address}"
    if last_error is not None:
        raise TimeoutError(f"{message}: {last_error}") from last_error
    raise TimeoutError(message)


def wait_for_kmd(
    *,
    localnet_config: LocalNetConfig | None = None,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 2.0,
) -> None:
    localnet = localnet_config or load_localnet_config()
    kmd_client = KMDClient(localnet.token, localnet.kmd_address)
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            kmd_client.list_wallets()
            return
        except Exception as exc:  # pragma: no cover - exercised via CLI/manual flow
            last_error = exc
        time.sleep(poll_interval_seconds)

    message = f"Timed out waiting for kmd at {localnet.kmd_address}"
    if last_error is not None:
        raise TimeoutError(f"{message}: {last_error}") from last_error
    raise TimeoutError(message)


def wait_for_localnet(
    *,
    localnet_config: LocalNetConfig | None = None,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 2.0,
) -> None:
    wait_for_algod(
        localnet_config=localnet_config,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    wait_for_kmd(
        localnet_config=localnet_config,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )


def ensure_funded_role_account(
    algorand: AlgorandClient,
    role_account_class: type[SigningAccount],
    *,
    min_spending_balance: AlgoAmount = DEFAULT_INITIAL_ALGO_FUNDS,
) -> SigningAccount:
    account = algorand.account.random()
    role_account = role_account_class(private_key=account.private_key)
    algorand.account.ensure_funded_from_environment(
        account_to_fund=role_account.address,
        min_spending_balance=min_spending_balance,
    )
    return role_account


def get_event_from_call_result(call_result: SendAppTransactionResult) -> bytes:
    event = call_result.returns[0].tx_info["logs"][-2]
    event_bytes = b64decode(event)
    return event_bytes[4:]


def get_primary_tx_id(call_result: SendAppTransactionResult) -> str:
    tx_ids = getattr(call_result, "tx_ids", None)
    if isinstance(tx_ids, list) and tx_ids:
        return tx_ids[0]

    transaction = getattr(call_result, "transaction", None)
    tx_id = getattr(transaction, "tx_id", None)
    if callable(tx_id):
        return tx_id()
    if isinstance(tx_id, str):
        return tx_id

    raise ValueError("Unable to extract transaction id from call result")


def decode_actus_event(event_bytes: bytes) -> dict[str, int | str]:
    offset = 0

    contract_id = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    event_type = event_bytes[offset]
    offset += 1

    type_name_offset = struct.unpack(">H", event_bytes[offset : offset + 2])[0]
    offset += 2

    event_time = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    payoff = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    currency_id = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    currency_unit_offset = struct.unpack(">H", event_bytes[offset : offset + 2])[0]
    offset += 2

    nominal_value = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]
    offset += 8

    nominal_rate_bps = struct.unpack(">H", event_bytes[offset : offset + 2])[0]
    offset += 2

    nominal_accrued = struct.unpack(">Q", event_bytes[offset : offset + 8])[0]

    type_name_length = struct.unpack(
        ">H", event_bytes[type_name_offset : type_name_offset + 2]
    )[0]
    type_name = event_bytes[
        type_name_offset + 2 : type_name_offset + 2 + type_name_length
    ].decode("utf-8")

    currency_unit_length = struct.unpack(
        ">H", event_bytes[currency_unit_offset : currency_unit_offset + 2]
    )[0]
    currency_unit = event_bytes[
        currency_unit_offset + 2 : currency_unit_offset + 2 + currency_unit_length
    ].decode("utf-8")

    return {
        "contract_id": contract_id,
        "type": event_type,
        "type_name": type_name,
        "time": event_time,
        "payoff": payoff,
        "currency_id": currency_id,
        "currency_unit": currency_unit,
        "nominal_value": nominal_value,
        "nominal_rate_bps": nominal_rate_bps,
        "nominal_accrued": nominal_accrued,
    }


def decode_actus_execution_event(event_bytes: bytes) -> dict[str, int]:
    (
        contract_id,
        event_id,
        event_type,
        scheduled_time,
        applied_at,
        payoff,
        payoff_sign,
        settled_amount,
        currency_id,
        sequence,
    ) = struct.unpack(">QQBQQQBQQQ", event_bytes)

    return {
        "contract_id": contract_id,
        "event_id": event_id,
        "event_type": event_type,
        "scheduled_time": scheduled_time,
        "applied_at": applied_at,
        "payoff": payoff,
        "payoff_sign": payoff_sign,
        "settled_amount": settled_amount,
        "currency_id": currency_id,
        "sequence": sequence,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Utilities for connecting to and waiting on D-ASA LocalNet.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    wait_parser = subcommands.add_parser(
        "wait",
        help="Wait for the LocalNet services required by the showcase.",
    )
    wait_parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Maximum number of seconds to wait.",
    )
    wait_parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between readiness checks.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "wait":
        wait_for_localnet(
            localnet_config=load_localnet_config(),
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
        )


if __name__ == "__main__":
    main()
