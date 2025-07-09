import os
from datetime import datetime, timezone
from typing import AsyncGenerator, TypeGuard

import pytest

from hl import TESTNET, Account, Cloid, HttpTransport, Info, Universe
from hl.errors import HttpError, NotFoundError, StatusError, UnexpectedSchemaError
from hl.types import (
    AssetInfo,
    DelegatorDeltaCDeposit,
    DelegatorDeltaDelegate,
    DelegatorDeltaWithdrawal,
)
from tests.conftest import ReplaceValues
from tests.mock_http_transport import MockHttpTransport

# Mock account info for tests


TEST_ACCOUNT = Account(
    address=os.getenv("HL_ADDRESS", "0x0000000000000000000000000000000000000000"),
    secret_key=os.getenv(
        "HL_SECRET_KEY",
        "0x0000000000000000000000000000000000000000000000000000000000000001",
    ),
)

MOCK_UNIVERSE = Universe(
    {3: AssetInfo(id=3, name="BTC", type="PERPETUAL", pxDecimals=1, szDecimals=5)}
)

SUB_ACCOUNT_ADDRESS = os.getenv(
    "SUB_ACCOUNT_ADDRESS", "0x0000000000000000000000000000000000000001"
)
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS", "0x0000000000000000000000000000000000000002")


@pytest.fixture
async def info_client() -> AsyncGenerator[Info, None]:
    """Create an Info client for testing."""
    real_transport = HttpTransport(TESTNET, "info")
    mock_transport = MockHttpTransport(real_transport)
    client = Info(
        transport=mock_transport, universe=MOCK_UNIVERSE, account=TEST_ACCOUNT
    )

    # Start the mock transport
    mock_transport.start()
    yield client
    mock_transport.stop()


async def test_all_mids(info_client: Info) -> None:
    """Test fetching all mids."""
    result = await info_client.all_mids()
    response = result.unwrap()

    assert isinstance(response, dict)
    assert len(response) > 0

    # Check that some known coins are in the response
    expected_coins = ["BTC", "ETH"]
    for coin in expected_coins:
        if coin in response:  # Use a guard clause to satisfy mypy
            assert isinstance(response[coin], str)
            # Price should be convertible to float
            assert float(response[coin]) > 0


async def test_all_mids_with_dex(info_client: Info) -> None:
    """Test fetching all mids with a dex."""
    result = await info_client.all_mids(dex="pluto")
    response = result.unwrap()
    assert isinstance(response, dict)
    assert "pluto:ABC" in response


async def test_all_mids_with_unknown_dex(info_client: Info) -> None:
    """Test fetching all mids with an unknown dex."""
    result = await info_client.all_mids(dex="NOT_A_DEX")
    error = result.unwrap_err()
    assert isinstance(error, NotFoundError)


async def test_user_open_orders(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user open orders."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_open_orders()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 1


async def test_user_open_orders_with_address(replace_values: ReplaceValues) -> None:
    """Test fetching user open orders with an unauthenticated api client and address."""
    real_transport = HttpTransport(TESTNET, "info")
    mock_transport = MockHttpTransport(real_transport)
    info_client = Info(transport=mock_transport)

    mock_transport.start()
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_open_orders(address=TEST_ACCOUNT.address)
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 1
    mock_transport.stop()


async def test_user_open_orders_with_account(replace_values: ReplaceValues) -> None:
    """Test fetching user open orders with an authenticated api client and account."""
    real_transport = HttpTransport(TESTNET, "info")
    mock_transport = MockHttpTransport(real_transport)
    info_client = Info(transport=mock_transport, account=TEST_ACCOUNT)

    mock_transport.start()
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_open_orders()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 1
    mock_transport.stop()


async def test_multiple_api_calls(info_client: Info) -> None:
    """Test that multiple API calls in a single test are captured in one fixture."""
    # Make multiple different API calls
    all_mids_result = await info_client.all_mids()
    assert all_mids_result.is_ok()
    all_mids = all_mids_result.unwrap()
    assert isinstance(all_mids, dict)
    assert len(all_mids) > 0

    meta_result = await info_client.perpetual_meta()
    assert meta_result.is_ok()
    meta = meta_result.unwrap()
    assert isinstance(meta, dict)
    assert "universe" in meta

    spot_meta_result = await info_client.spot_meta()
    assert spot_meta_result.is_ok()
    spot_meta = spot_meta_result.unwrap()
    assert isinstance(spot_meta, dict)
    assert "universe" in spot_meta


async def test_user_frontend_open_orders(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user frontend open orders."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_frontend_open_orders()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 1


async def test_user_historical_orders(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user historical orders."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_historical_orders()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 34


async def test_user_fills(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching user fills."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_fills()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 2
        assert response[0]["coin"] == "BTC"


async def test_user_fills_by_time(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user fills by time."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_fills_by_time(
            start=datetime(2025, 6, 15, 16, 30, 0),
            end=datetime(2025, 6, 15, 16, 48, 0),
        )
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 1
        assert response[0]["coin"] == "BTC"


async def test_user_fills_by_time_aggregate_by_time(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user fills by time."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_fills_by_time(
            start=datetime(2025, 6, 15, 18, 5, 0),
            end=datetime(2025, 6, 15, 18, 30, 0),
            # TODO: How exactly can we create a test case for this?
            # Currently, only a single fill is returned regardless of aggregate_by_time's value
            aggregate_by_time=True,
        )
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 1
        assert response[0]["coin"] == "DOGE"


async def test_user_rate_limit(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user rate limit."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_rate_limit()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, dict)
        assert isinstance(response["cumVlm"], str)
        assert isinstance(response["nRequestsUsed"], int)
        assert isinstance(response["nRequestsCap"], int)


async def test_order_status(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching order status."""
    order_id = 33845539264
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.order_status(order_id=order_id)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert "status" in response
    assert response["status"] == "order"
    assert response["order"]["order"]["oid"] == order_id
    assert response["order"]["status"] == "open"


async def test_order_status_with_cloid(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching order status with the client order id."""
    cloid = Cloid.from_int(1337)
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.order_status(order_id=cloid)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert "status" in response
    assert response["status"] == "order"
    assert response["order"]["status"] == "open"
    assert response["order"]["order"]["cloid"] == cloid.to_raw()


async def test_order_status_with_unknown_cloid(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching order status with the client order id."""
    cloid = Cloid.from_int(501)
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.order_status(order_id=cloid)
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, StatusError)
        assert error.expected == "order"
        assert error.actual == "unknownOid"


async def test_l2_book(info_client: Info) -> None:
    """Test fetching the L2 book for a coin."""
    result = await info_client.l2_book(asset="ETH")
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, dict)
    assert "levels" in response
    assert len(response["levels"]) == 2  # Bids and asks

    # Check the structure of the response
    bids, asks = response["levels"]
    assert len(bids) > 0
    assert len(asks) > 0

    # Check that the first bid and ask have the expected fields
    first_bid = bids[0]
    first_ask = asks[0]
    assert "px" in first_bid
    assert "sz" in first_bid
    assert "px" in first_ask
    assert "sz" in first_ask


async def test_l2_book_with_unknown_asset(info_client: Info) -> None:
    """Test fetching the L2 book for a coin."""
    result = await info_client.l2_book(asset="NOT_A_COIN")
    assert result.is_err()
    error = result.unwrap_err()
    assert isinstance(error, NotFoundError)


async def test_candle_snapshot(info_client: Info) -> None:
    """Test fetching a candle snapshot."""
    result = await info_client.candle_snapshot(
        asset="BTC",
        interval="1m",
        start=datetime(2025, 6, 15, 18, 0, 0),
        end=datetime(2025, 6, 15, 18, 2, 59),
    )
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 3
    assert response[0]["s"] == "BTC"


async def test_candle_snapshot_without_end(info_client: Info) -> None:
    """Test fetching a candle snapshot."""
    result = await info_client.candle_snapshot(
        asset="BTC",
        interval="1m",
        start=datetime(2025, 6, 15, 18, 42, 0),
    )
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 5
    assert response[0]["s"] == "BTC"


async def test_max_builder_fee(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address, "builder": TEST_ACCOUNT.address},
    ):
        result = await info_client.max_builder_fee(builder=TEST_ACCOUNT.address)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, int)
    assert response == 0


async def test_user_twap_slice_fills(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user TWAP slice fills."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_twap_slice_fills()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert response[0]["twapId"] == 6552


async def test_user_sub_accounts(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching subaccounts."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
        response={
            "0.subAccountUser": SUB_ACCOUNT_ADDRESS,
            "0.master": TEST_ACCOUNT.address,
        },
    ):
        result = await info_client.user_sub_accounts()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0]["name"] == "testplsignore"
    assert response[0]["subAccountUser"] == SUB_ACCOUNT_ADDRESS


async def test_user_sub_accounts_empty(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching subaccounts when there are no subaccounts."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_sub_accounts()
        assert result.is_ok()
        response = result.unwrap()
        assert isinstance(response, list)
        assert len(response) == 0


async def test_vault_details(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching vault details."""
    with replace_values(
        info_client.transport,
        request={"vaultAddress": VAULT_ADDRESS},
        response={
            "vaultAddress": VAULT_ADDRESS,
            "leader": TEST_ACCOUNT.address,
        },
    ):
        result = await info_client.vault_details(vault_address=VAULT_ADDRESS)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["name"] == "MyTestVault2"
    assert response["vaultAddress"] == VAULT_ADDRESS


async def test_user_vault_equities(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user vault equities."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_vault_equities()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 2
    assert response[0]["equity"] == "20000.0"


async def test_user_role(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching user role."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_role()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["role"] == "user"


async def test_user_role_with_address(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user role with an address."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_role(address=TEST_ACCOUNT.address)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["role"] == "user"


async def test_user_role_with_vault_address(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user role with a vault address."""
    with replace_values(
        info_client.transport,
        request={"user": VAULT_ADDRESS},
    ):
        result = await info_client.user_role(address=VAULT_ADDRESS)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["role"] == "vault"


async def test_user_role_with_sub_account_address(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user role with a sub account address."""
    with replace_values(
        info_client.transport,
        request={"user": SUB_ACCOUNT_ADDRESS},
        response={
            "data.master": TEST_ACCOUNT.address,
        },
    ):
        result = await info_client.user_role(address=SUB_ACCOUNT_ADDRESS)
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["role"] == "subAccount"
    assert response["data"]["master"] == TEST_ACCOUNT.address.lower()


async def test_user_portfolio(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching user portfolio."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_portfolio()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 8
    assert response[0][0] == "day"


async def test_user_referral_without_code(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user referral."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_referral()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["referredBy"] is None
    assert response["referrerState"]["stage"] == "needToCreateCode"


async def test_user_referral_with_code(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user referral with a code."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_referral()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["referrerState"]["stage"] == "ready"


async def test_user_fees(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching user fees."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_fees()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["activeReferralDiscount"] == "0.0"


async def test_user_delegations(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user delegations."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_delegations()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0]["validator"] == "0x8888c8c2c539d56919d20ac58305a5000b26fb67"


async def test_user_delegator_summary(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user delegator summary."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_delegator_summary()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert response["delegated"] == "0.0"
    assert response["undelegated"] == "0.0"
    assert response["totalPendingWithdrawal"] == "0.0"
    assert response["nPendingWithdrawals"] == 0


def is_delegate_delta(
    delta: DelegatorDeltaDelegate | DelegatorDeltaWithdrawal | DelegatorDeltaCDeposit,
) -> TypeGuard[DelegatorDeltaDelegate]:
    """Type guard to check if delta is a DelegatorDeltaDelegate."""
    return "delegate" in delta


def is_withdrawal_delta(
    delta: DelegatorDeltaDelegate | DelegatorDeltaWithdrawal | DelegatorDeltaCDeposit,
) -> TypeGuard[DelegatorDeltaWithdrawal]:
    """Type guard to check if delta is a DelegatorDeltaWithdrawal."""
    return "withdrawal" in delta


def is_cdeposit_delta(
    delta: DelegatorDeltaDelegate | DelegatorDeltaWithdrawal | DelegatorDeltaCDeposit,
) -> TypeGuard[DelegatorDeltaCDeposit]:
    """Type guard to check if delta is a DelegatorDeltaCDeposit."""
    return "cDeposit" in delta


async def test_user_delegator_history(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user delegator history."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_delegator_history()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 6

    # Check delegate item
    first_item = response[0]
    assert "delta" in first_item
    delta = first_item["delta"]

    # Type guard: if "delegate" key exists, it's a DelegatorDeltaDelegate
    if is_delegate_delta(delta):
        assert not delta["delegate"]["isUndelegate"]
    else:
        raise AssertionError("Expected delegate delta")

    # Check withdrawal item
    second_item = response[1]
    assert "delta" in second_item
    delta = second_item["delta"]

    # Type guard: if "withdrawal" key exists, it's a DelegatorDeltaWithdrawal
    if is_withdrawal_delta(delta):
        assert delta["withdrawal"]["phase"] == "finalized"
    else:
        raise AssertionError("Expected withdrawal delta")


async def test_user_delegator_rewards(info_client: Info) -> None:
    """Test fetching user delegator rewards."""
    result = await info_client.user_delegator_rewards(
        address="0x8888c8c2c539d56919d20ac58305a5000b26fb67",
    )
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert response[0]["source"] == "delegation"
    assert response[1]["source"] == "commission"


##############
# Perpetuals #
##############


async def test_perpetual_meta(info_client: Info) -> None:
    """Test fetching the meta data."""
    result = await info_client.perpetual_meta()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, dict)
    assert "universe" in response
    assert "marginTables" in response


async def test_perpetual_meta_and_asset_ctxs(info_client: Info) -> None:
    """Test fetching the perpetual meta data and asset contexts."""
    result = await info_client.perpetual_meta_and_asset_ctxs()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 2
    meta, asset_ctxs = response
    assert "universe" in meta
    assert "marginTables" in meta
    assert isinstance(asset_ctxs, list)


async def test_user_state(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching user state."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_state()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert "marginSummary" in response
    assert "crossMarginSummary" in response
    assert "crossMaintenanceMarginUsed" in response
    assert "withdrawable" in response
    assert "assetPositions" in response
    assert "time" in response


async def test_user_funding(info_client: Info, replace_values: ReplaceValues) -> None:
    """Test fetching user funding."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_funding(
            start=datetime(2025, 6, 13, 5, 0, 0),
            end=datetime(2025, 6, 17, 5, 0, 0),
        )
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0]["delta"]["type"] == "funding"
    assert response[0]["delta"]["coin"] == "BTC"


async def test_user_non_funding_ledger_updates(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching user non-funding ledger updates."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.user_non_funding_ledger_updates(
            start=datetime(2025, 6, 13, 5, 0, 0),
            end=datetime(2025, 6, 17, 5, 0, 0),
        )
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, list)
    assert response[0]["delta"]["type"] == "spotTransfer"


async def test_funding_history(info_client: Info) -> None:
    """Test fetching funding history."""
    result = await info_client.funding_history(
        asset="BTC", start=datetime(2025, 6, 13, 5, 0, 0)
    )
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert response[0]["coin"] == "BTC"


async def test_funding_history_with_end(info_client: Info) -> None:
    """Test fetching user funding history."""
    end = datetime(2025, 6, 13, 12, 0, 0, tzinfo=timezone.utc)
    result = await info_client.funding_history(
        asset="BTC",
        start=datetime(2025, 6, 13, 5, 0, 0, tzinfo=timezone.utc),
        end=end,
    )
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert response[0]["coin"] == "BTC"
    assert all(
        datetime.fromtimestamp(entry["time"] // 1000, tz=timezone.utc) < end
        for entry in response
    )


async def test_predicted_fundings(info_client: Info) -> None:
    """Test fetching predicted fundings."""
    result = await info_client.predicted_fundings()
    assert result.is_ok()
    response = result.unwrap()
    coin, venues = response[1]
    assert coin == "AAVE"
    assert isinstance(venues, list)
    assert len(venues) == 3
    venue, funding_rate = venues[0]
    assert venue == "BinPerp"
    assert isinstance(funding_rate, dict)
    assert funding_rate["fundingRate"] == "0.00005069"
    assert funding_rate["nextFundingTime"] == 1750176000000


async def test_perpetuals_at_open_interest_cap(info_client: Info) -> None:
    """Test fetching perpetuals at open interest cap."""
    result = await info_client.perpetuals_at_open_interest_cap()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0] == "HYPE"


async def test_perpetual_deploy_auction_status(info_client: Info) -> None:
    """Test fetching perpetual deploy auction status."""
    result = await info_client.perpetual_deploy_auction_status()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, dict)
    assert isinstance(response["startTimeSeconds"], int)
    assert isinstance(response["durationSeconds"], int)
    assert isinstance(response["startGas"], str)
    assert response["currentGas"] is None
    assert isinstance(response["endGas"], str)


async def test_perpetual_dexs(info_client: Info) -> None:
    """Test fetching perpetual dexs."""
    result = await info_client.perpetual_dexs()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert response[0] is None
    assert response[1] is not None
    assert isinstance(response[1]["name"], str)
    assert isinstance(response[1]["full_name"], str)


########
# Spot #
########


async def test_spot_meta(info_client: Info) -> None:
    """Test fetching spot meta."""
    result = await info_client.spot_meta()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, dict)
    assert response["universe"][0]["name"] == "PURR/USDC"
    assert response["tokens"][0]["name"] == "USDC"


async def test_spot_meta_and_asset_ctxs(info_client: Info) -> None:
    """Test fetching spot meta and asset ctxs."""
    result = await info_client.spot_meta_and_asset_ctxs()
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, list)
    assert len(response) == 2
    meta, asset_ctxs = response
    assert isinstance(meta, dict)
    assert "universe" in meta
    assert meta["universe"][0]["name"] == "PURR/USDC"
    assert isinstance(asset_ctxs, list)
    assert asset_ctxs[0]["coin"] == "PURR/USDC"


async def test_spot_user_state(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching spot user state."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.spot_user_state()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert "balances" in response
    assert isinstance(response["balances"], list)
    assert len(response["balances"]) == 1
    assert response["balances"][0]["coin"] == "USDC"


async def test_spot_deploy_auction_status(
    info_client: Info, replace_values: ReplaceValues
) -> None:
    """Test fetching spot deploy auction status."""
    with replace_values(
        info_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        result = await info_client.spot_deploy_auction_status()
        assert result.is_ok()
        response = result.unwrap()
    assert isinstance(response, dict)
    assert isinstance(response["gasAuction"], dict)
    assert isinstance(response["gasAuction"]["startTimeSeconds"], int)
    assert isinstance(response["gasAuction"]["durationSeconds"], int)
    assert isinstance(response["gasAuction"]["startGas"], str)
    assert response["gasAuction"]["currentGas"] is None
    assert isinstance(response["gasAuction"]["endGas"], str)


@pytest.mark.skip(reason="Testnet API returns 500 error")
async def test_token_details(info_client: Info) -> None:
    """Test fetching token details."""
    usdc_token_id = "0x6d1e7cde53ba9467b783cb7c530ce054"
    result = await info_client.token_details(token_id=usdc_token_id)
    assert result.is_ok()
    response = result.unwrap()
    assert isinstance(response, dict)
    assert response["name"] == "USDC"


async def test_user_open_orders_with_malformed_address(info_client: Info) -> None:
    result = await info_client.user_open_orders(address="0x00000000000000")
    assert result.is_err()
    error = result.unwrap_err()
    assert isinstance(error, HttpError)
    assert error.status_code == 422
