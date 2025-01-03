import logging
import os

import algokit_utils
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
    from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
        AssetCreateArgs,
        DeployCreate,
        ZeroCouponBondClient,
    )

    app_client = ZeroCouponBondClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.UpdateApp,
        create_args=DeployCreate(
            args=AssetCreateArgs(
                arranger=os.environ["ARRANGER_ADDRESS"],
                metadata=b"Zero Coupon Bond Prospectus",
            )
        ),
    )
