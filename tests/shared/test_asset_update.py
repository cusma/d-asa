from typing import Any

import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts import errors as err

from .cases import ContractCase

_UPDATED_PROSPECTUS_URL = "Updated Prospectus"


def test_pass_asset_update(
    contract_case: ContractCase,
    shared_asset_metadata: Any,
    shared_client_active: Any,
) -> None:
    metadata = shared_client_active.send.get_asset_metadata().abi_return
    assert metadata.prospectus_url == shared_asset_metadata.prospectus_url

    updated_metadata = contract_case.asset_metadata_cls(
        contract_type=shared_asset_metadata.contract_type,
        calendar=shared_asset_metadata.calendar,
        business_day_convention=shared_asset_metadata.business_day_convention,
        end_of_month_convention=shared_asset_metadata.end_of_month_convention,
        prepayment_effect=shared_asset_metadata.prepayment_effect,
        penalty_type=shared_asset_metadata.penalty_type,
        prospectus_hash=shared_asset_metadata.prospectus_hash,
        prospectus_url=_UPDATED_PROSPECTUS_URL,
    )
    shared_client_active.send.update.asset_update(
        contract_case.asset_update_args_cls(metadata=updated_metadata)
    )

    metadata = shared_client_active.send.get_asset_metadata().abi_return
    assert metadata.prospectus_url == _UPDATED_PROSPECTUS_URL


def test_fail_unauthorized(
    contract_case: ContractCase,
    no_role_account: SigningAccount,
    shared_asset_metadata: Any,
    shared_client_active: Any,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        shared_client_active.send.update.asset_update(
            contract_case.asset_update_args_cls(metadata=shared_asset_metadata),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
