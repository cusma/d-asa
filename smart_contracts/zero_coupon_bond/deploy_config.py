import logging
import os

import algokit_utils

from smart_contracts import constants as sc_cst

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy() -> None:
    from smart_contracts.artifacts.zero_coupon_bond.zero_coupon_bond_client import (
        AssetCreateArgs,
        AssetMetadata,
        AssetUpdateArgs,
        ZeroCouponBondFactory,
        ZeroCouponBondMethodCallCreateParams,
        ZeroCouponBondMethodCallUpdateParams,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        ZeroCouponBondFactory, default_sender=deployer.address
    )

    factory.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.UpdateApp,
        create_params=ZeroCouponBondMethodCallCreateParams(
            args=AssetCreateArgs(
                arranger=os.environ["ARRANGER_ADDRESS"],
                metadata=AssetMetadata(
                    contract_type=sc_cst.CT_PAM,
                    calendar=sc_cst.CLDR_NC,
                    business_day_convention=sc_cst.BDC_NOS,
                    end_of_month_convention=sc_cst.EOMC_SD,
                    prepayment_effect=sc_cst.PPEF_N,
                    penalty_type=sc_cst.PYTP_N,
                    prospectus_hash=bytes(32),
                    prospectus_url="Zero Coupon Bond Prospectus",
                ),
            ),
        ),
        update_params=ZeroCouponBondMethodCallUpdateParams(
            args=AssetUpdateArgs(
                metadata=AssetMetadata(
                    contract_type=sc_cst.CT_PAM,
                    calendar=sc_cst.CLDR_NC,
                    business_day_convention=sc_cst.BDC_NOS,
                    end_of_month_convention=sc_cst.EOMC_SD,
                    prepayment_effect=sc_cst.PPEF_N,
                    penalty_type=sc_cst.PYTP_N,
                    prospectus_hash=bytes(32),
                    prospectus_url="Zero Coupon Bond Prospectus",
                ),
            ),
        ),
    )
