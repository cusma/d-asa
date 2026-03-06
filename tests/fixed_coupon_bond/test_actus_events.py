from datetime import datetime, timezone

from algokit_utils import (
    AlgorandClient,
    AssetOptInParams,
    AssetTransferParams,
    CommonAppCallParams,
    SendParams,
    SigningAccount,
)

from smart_contracts import constants as sc_cst
from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
    AssetConfigArgs,
    AssetCreateArgs,
    AssetMetadata,
    FixedCouponBondFactory,
    PayCouponArgs,
    PayPrincipalArgs,
    PrimaryDistributionArgs,
    RbacAssignRoleArgs,
)
from tests import conftest_helpers as helpers
from tests import utils

# Configuration
PRINCIPAL = 10_000_00  # 10,000 EUR with 2 decimals
MINIMUM_DENOMINATION = 100_00  # 100 EUR with 2 decimals
TOTAL_COUPONS = 20
COUPON_PER_YEAR = 4
NOMINAL_RATE = 200  # 2% in BPS
COUPON_RATE = NOMINAL_RATE // COUPON_PER_YEAR  # 0.5% per coupon = 50 BPS
INTEREST_RATE = TOTAL_COUPONS * COUPON_RATE
COUPON_PERIOD = 90 * sc_cst.DAY_2_SEC  # 3 months = 90 days
ISSUANCE_DATE = 1893369600  # Mon Dec 31 2029 00:00:00 GMT+0000


def test_actus_events(
    algorand: AlgorandClient,
    bank: SigningAccount,
    currency: utils.Currency,
    arranger: SigningAccount,
) -> None:
    """
    Test ACTUS events (IP, PR) for a fixed coupon bond.

    All dates are calculated relative to the LocalNet time.
    """

    # Time schedule (all dates relative to current time)
    current_ts = utils.get_latest_timestamp(algorand.client.algod)

    # Primary distribution (before issuance date)
    primary_opening = current_ts + 1 * sc_cst.DAY_2_SEC
    primary_closure = primary_opening + 7 * sc_cst.DAY_2_SEC

    # Generate coupon dates (every 3 months starting from issuance)
    coupon_dates = [
        ISSUANCE_DATE + i * COUPON_PERIOD for i in range(1, TOTAL_COUPONS + 1)
    ]

    # Maturity: 1 second after the last coupon
    maturity_date = coupon_dates[-1] + 1

    time_events = [
        primary_opening,
        primary_closure,
        ISSUANCE_DATE,
        *coupon_dates,
        maturity_date,
    ]

    # Create and configure D-ASA
    asset_metadata = AssetMetadata(
        contract_type=sc_cst.CT_PAM,
        calendar=sc_cst.CLDR_NC,
        business_day_convention=sc_cst.BDC_NOS,
        end_of_month_convention=sc_cst.EOMC_SD,
        prepayment_effect=sc_cst.PPEF_N,
        penalty_type=sc_cst.PYTP_N,
        prospectus_hash=bytes(32),
        prospectus_url="Fixed Coupon Bond Test",
    )

    client = helpers.create_and_fund_client(
        algorand,
        FixedCouponBondFactory,
        arranger,
        AssetCreateArgs(arranger=arranger.address, metadata=asset_metadata),
    )

    # Configure asset (this also opts the contract into the settlement asset)
    coupon_rates = [COUPON_RATE] * TOTAL_COUPONS

    client.send.asset_config(
        AssetConfigArgs(
            denomination_asset_id=currency.id,
            settlement_asset_id=currency.id,
            principal=PRINCIPAL,
            principal_discount=0,
            minimum_denomination=MINIMUM_DENOMINATION,
            day_count_convention=sc_cst.DCC_CONT,
            interest_rate=INTEREST_RATE,
            coupon_rates=coupon_rates,
            time_events=time_events,
            time_periods=[],
        )
    )

    # Fund the D-ASA contract with settlement asset
    total_funds = PRINCIPAL * (sc_cst.BPS + INTEREST_RATE) // sc_cst.BPS

    # Transfer denomination assets to the contract
    algorand.send.asset_transfer(
        AssetTransferParams(
            asset_id=currency.id,
            amount=total_funds,
            receiver=client.app_address,
            sender=bank.address,
            signer=bank.signer,
        )
    )

    # Create primary dealer
    primary_dealer = helpers.create_role_account(
        algorand,
        utils.DAsaPrimaryDealer,
        client,
        utils.set_role_config(primary_opening, primary_closure),
        RbacAssignRoleArgs,
    )

    # Create an account to receive units
    account_manager = helpers.create_role_account(
        algorand,
        utils.DAsaAccountManager,
        client,
        rbac_assign_role_args_class=RbacAssignRoleArgs,
    )

    # Time warp to primary distribution
    utils.time_warp(primary_opening)

    # Create account
    investor = algorand.account.random()
    algorand.account.ensure_funded_from_environment(
        account_to_fund=investor.address,
        min_spending_balance=utils.AlgoAmount.from_algo(10),
    )

    # Opt-in to currency
    algorand.send.asset_opt_in(
        AssetOptInParams(
            asset_id=currency.id,
            sender=investor.address,
            signer=investor.signer,
        )
    )

    # Open account on D-ASA
    from smart_contracts.artifacts.fixed_coupon_bond.fixed_coupon_bond_client import (
        AccountOpenArgs,
    )

    client.send.account_open(
        AccountOpenArgs(
            holding_address=investor.address,
            payment_address=investor.address,
        ),
        params=CommonAppCallParams(
            sender=account_manager.address, signer=account_manager.signer
        ),
    )

    # Create DAsaAccount wrapper
    investor_account = utils.DAsaAccount(
        holding_address=investor.address,
        d_asa_client=client,
        private_key=investor.private_key,
    )

    # Primary distribution - this will emit IED event
    units_to_distribute = PRINCIPAL // MINIMUM_DENOMINATION  # All units

    print("\n" + "=" * 80)
    print("ACTUS EVENTS FOR FIXED COUPON BOND")
    print("=" * 80)
    print("\nBond Configuration:")
    print(f"  Principal: {PRINCIPAL * currency.asa_to_unit:.2f} EUR")
    print(f"  Total Coupons: {TOTAL_COUPONS}")
    print(f"  Interest Rate per Coupon: {COUPON_RATE / 100:.2f}%")
    print(f"  Total Interest Rate: {INTEREST_RATE / 100:.2f}%")
    print(f"  Coupon Period: {COUPON_PERIOD // sc_cst.DAY_2_SEC} days")
    print(
        f"  Issuance Date: {datetime.fromtimestamp(ISSUANCE_DATE, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    print(
        f"  Maturity Date: {datetime.fromtimestamp(maturity_date, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    print("\n" + "=" * 80)

    client.send.primary_distribution(
        PrimaryDistributionArgs(
            holding_address=investor_account.holding_address,
            units=units_to_distribute,
        ),
        params=CommonAppCallParams(
            sender=primary_dealer.address, signer=primary_dealer.signer
        ),
    )

    # Time warp to issuance
    utils.time_warp(ISSUANCE_DATE)

    # Pay all coupons
    print("\n2. IP (Interest Payment) Events:")
    total_interest_paid = 0
    for coupon_idx in range(1, TOTAL_COUPONS + 1):
        # Time warp to coupon date
        coupon_date = coupon_dates[coupon_idx - 1]
        utils.time_warp(coupon_date)

        # Pay coupon - this will emit IP event
        result_ip = client.send.pay_coupon(
            PayCouponArgs(
                holding_address=investor_account.holding_address,
                payment_info=b"",
            ),
            params=CommonAppCallParams(max_fee=utils.max_fee_per_coupon(TOTAL_COUPONS)),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )

        # Extract and print IP event
        ip_event_bytes = utils.get_event_from_call_result(result_ip)
        ip_event = utils.decode_actus_event(ip_event_bytes)

        # Accumulate total interest
        total_interest_paid += ip_event["payoff"]

        print(f"\n   Coupon {coupon_idx}/{TOTAL_COUPONS}:")
        print(f"     Type: {ip_event['type_name']}")
        print(
            f"     Time: {datetime.fromtimestamp(ip_event['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC ({ip_event['time']})"
        )
        print(
            f"     Payoff: {ip_event['payoff'] * currency.asa_to_unit:.2f} {ip_event['currency_unit']}"
        )
        print(
            f"     Nominal Value: {ip_event['nominal_value'] * currency.asa_to_unit:.2f} {ip_event['currency_unit']}"
        )

    # Time warp to maturity
    utils.time_warp(maturity_date)

    # Pay principal - this will emit PR event
    result_pr = client.send.pay_principal(
        PayPrincipalArgs(
            holding_address=investor_account.holding_address,
            payment_info=b"",
        ),
    )

    # Extract and print PR event
    pr_event_bytes = utils.get_event_from_call_result(result_pr)
    pr_event = utils.decode_actus_event(pr_event_bytes)

    print("\n3. PR (Principal Redemption) Event:")
    print(f"   Type: {pr_event['type_name']}")
    print(
        f"   Time: {datetime.fromtimestamp(pr_event['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC ({pr_event['time']})"
    )
    print(
        f"   Payoff: {pr_event['payoff'] * currency.asa_to_unit:.2f} {pr_event['currency_unit']}"
    )
    print(
        f"   Nominal Value: {pr_event['nominal_value'] * currency.asa_to_unit:.2f} {pr_event['currency_unit']}"
    )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Events: {TOTAL_COUPONS + 1} ({TOTAL_COUPONS} IP + 1 PR)")
    print(f"Total Interest Paid: {total_interest_paid * currency.asa_to_unit:.2f} EUR")
    print(f"Principal Redeemed: {pr_event['payoff'] * currency.asa_to_unit:.2f} EUR")
    print(
        f"Total Cashflow: {(total_interest_paid + pr_event['payoff']) * currency.asa_to_unit:.2f} EUR"
    )
    print("=" * 80 + "\n")
