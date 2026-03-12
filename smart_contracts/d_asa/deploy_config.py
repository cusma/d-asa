import logging
import os

import algokit_utils
from algosdk.constants import ZERO_ADDRESS

logger = logging.getLogger(__name__)


def _get_arranger_address(*, deployer_address: str) -> str:
    arranger_address = os.getenv("ARRANGER_ADDRESS")
    if not arranger_address or arranger_address == ZERO_ADDRESS:
        logger.info(
            "ARRANGER_ADDRESS is unset or zero; defaulting arranger to DEPLOYER"
        )
        return deployer_address
    return arranger_address


# define deployment behaviour based on supplied app spec
def deploy() -> None:
    from smart_contracts.artifacts.d_asa.dasa_client import (
        ContractCreateArgs,
        DasaFactory,
        DasaMethodCallCreateParams,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer_ = algorand.account.from_environment("DEPLOYER")
    arranger_address = _get_arranger_address(deployer_address=deployer_.address)

    factory = algorand.client.get_typed_app_factory(
        DasaFactory, default_sender=deployer_.address
    )

    factory.deploy(
        create_params=DasaMethodCallCreateParams(
            args=ContractCreateArgs(arranger=arranger_address)
        ),
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )
