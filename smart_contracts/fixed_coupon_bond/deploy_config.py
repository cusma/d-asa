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
    from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
        AssetCreateArgs,
        DeployCreate,
        FixedCouponBondClient,
    )

    app_client = FixedCouponBondClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.UpdateApp,
        create_args=DeployCreate(
            args=AssetCreateArgs(
                arranger=os.environ["DEPLOYER_ADDRESS"],
                metadata=b"Fixed Coupon Bond Prospectus",
            )
        ),
    )
