from __future__ import annotations

from collections.abc import Callable

import pytest
from algokit_utils import AlgorandClient, SigningAccount

from src.artifacts.dasa_client import DasaClient
from src.localnet import Currency, DAsaAccountManager, DAsaPrimaryDealer
from src.showcase import (
    SHOWCASE_BUILDERS,
    PamShowcaseScenario,
    run_showcase_scenario,
)
from tests.pam.pam_test_support import format_lifecycle_trace


@pytest.mark.parametrize(
    "build_scenario",
    SHOWCASE_BUILDERS,
    ids=("fcb", "zcb"),
)
@pytest.mark.showcase
def test_pam_lifecycle_showcase(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: Currency,
    d_asa_client: DasaClient,
    pam_primary_dealer: DAsaPrimaryDealer,
    pam_account_manager: DAsaAccountManager,
    build_scenario: Callable[[AlgorandClient, Currency], PamShowcaseScenario],
) -> None:
    trace = run_showcase_scenario(
        algorand=algorand,
        bank=bank,
        currency=currency,
        d_asa_client=d_asa_client,
        pam_primary_dealer=pam_primary_dealer,
        pam_account_manager=pam_account_manager,
        build_scenario=build_scenario,
    )

    print()
    print(format_lifecycle_trace(trace))
