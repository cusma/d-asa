import logging
import os

import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts import constants as sc_cst

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
        AssetMetadata,
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
                metadata=AssetMetadata(
                    contract_type=sc_cst.CT_PAM,
                    calendar=sc_cst.CLDR_NC,
                    business_day_convention=sc_cst.BDC_NOS,
                    end_of_month_convention=sc_cst.EOMC_SD,
                    prepayment_effect=sc_cst.PPEF_N,
                    penalty_type=sc_cst.PYTP_N,
                    prospectus_hash=bytes(0),
                    prospectus_url=b"Zero Coupon Bond Prospectus",
                ),
            )
        ),
    )
