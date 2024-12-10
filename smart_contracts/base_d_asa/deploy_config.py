import logging

import algokit_utils
from algosdk.constants import ZERO_ADDRESS
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.base_d_asa.base_d_asa_client import (
        AssetCreateArgs,
        BaseDAsaClient,
        DeployCreate,
    )

    app_client = BaseDAsaClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
        create_args=DeployCreate(
            args=AssetCreateArgs(arranger=ZERO_ADDRESS, metadata=b"")
        ),
    )
