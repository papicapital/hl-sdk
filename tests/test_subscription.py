import asyncio
import os
import time
from typing import AsyncGenerator

import pytest

from hl import TESTNET, Account, Universe, WsTransport
from hl.subscriptions import Subscriptions
from hl.types import AllMidsMsg, AssetInfo
from tests.conftest import ReplaceValues, replace_values
from tests.mock_ws_transport import MockWsTransport

# Mock account info for tests
TEST_ACCOUNT = Account(
    address=os.getenv("HL_ADDRESS") or "0x0000000000000000000000000000000000000000",
    secret_key=os.getenv("HL_SECRET_KEY")
    or "0x0000000000000000000000000000000000000000000000000000000000000001",
)

MOCK_UNIVERSE = Universe(
    {3: AssetInfo(id=3, name="BTC", type="PERPETUAL", pxDecimals=1, szDecimals=5)}
)


@pytest.fixture
async def subscriptions_client() -> AsyncGenerator[Subscriptions, None]:
    """Create a Subscriptions client with MockWsTransport for testing (immediate replay)."""
    real_transport = WsTransport(TESTNET)
    mock_transport = MockWsTransport(
        real_transport,
        capture_duration=5.0,
    )

    client = Subscriptions(
        transport=mock_transport, universe=MOCK_UNIVERSE, account=TEST_ACCOUNT
    )

    # Start the mock transport
    mock_transport.start()

    try:
        # Start the WebSocket connection in the background
        async with mock_transport.run():
            yield client
    finally:
        # Clean up after the context manager exits
        await mock_transport.stop()


async def test_all_mids_subscription(subscriptions_client: Subscriptions) -> None:
    """Test subscribing to all mids updates."""
    # Subscribe to all mids
    subscription_id, queue = await subscriptions_client.all_mids()

    # Verify the subscription was created
    assert isinstance(subscription_id, int)
    assert isinstance(queue, asyncio.Queue)

    # Wait up to 6 seconds for a message
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "allMids"
    assert "data" in message
    assert "mids" in message["data"]

    # Verify the mids data structure
    mids = message["data"]["mids"]
    assert isinstance(mids, dict)
    assert len(mids) > 0

    # Check that all values are numeric strings
    for coin, price in mids.items():
        assert isinstance(coin, str)
        assert isinstance(price, str)
        # Price should be convertible to float
        assert float(price) > 0

    # Clean up: unsubscribe
    await subscriptions_client.unsubscribe(subscription_id)


async def test_all_mids_subscription_with_custom_queue(
    subscriptions_client: Subscriptions,
) -> None:
    """Test subscribing to all mids updates with a custom queue."""
    # Create a custom queue
    custom_queue: asyncio.Queue[AllMidsMsg] = asyncio.Queue()

    # Subscribe to all mids with the custom queue
    subscription_id, returned_queue = await subscriptions_client.all_mids(
        queue=custom_queue
    )

    # Verify the subscription was created and returns the same queue
    assert isinstance(subscription_id, int)
    assert returned_queue is custom_queue

    # Clean up: unsubscribe
    await subscriptions_client.unsubscribe(subscription_id)


@pytest.mark.skip(reason="Not sure how to test this")
async def test_notification_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to notification updates."""
    # Subscribe to notification
    with replace_values(
        subscriptions_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        subscription_id, queue = await subscriptions_client.notification()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=106.0)


async def test_web_data2_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to web data 2 updates."""
    # Subscribe to web data 2
    with replace_values(
        subscriptions_client.transport,
        request={"user": TEST_ACCOUNT.address},
    ):
        subscription_id, queue = await subscriptions_client.web_data2()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "webData2"
    assert "data" in message
    assert "clearinghouseState" in message["data"]
    assert isinstance(message["data"]["leadingVaults"], list)
    assert isinstance(message["data"]["totalVaultEquity"], str)


async def test_candle_subscription(subscriptions_client: Subscriptions) -> None:
    """Test subscribing to candle updates."""
    # Subscribe to candle
    subscription_id, queue = await subscriptions_client.candle(
        asset="BTC", interval="1m"
    )

    # Verify the subscription was created
    assert isinstance(subscription_id, int)
    assert isinstance(queue, asyncio.Queue)

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "candle"
    assert "data" in message
    assert message["data"]["s"] == "BTC"


async def test_l2_book_subscription(subscriptions_client: Subscriptions) -> None:
    """Test subscribing to BTC's l2_book updates."""
    # Subscribe to BTC's l2 book
    subscription_id, queue = await subscriptions_client.l2_book(asset="BTC")

    # Verify the subscription was created
    assert isinstance(subscription_id, int)
    assert isinstance(queue, asyncio.Queue)

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "l2Book"
    assert "data" in message

    # Verify the l2 book data structure
    data = message["data"]
    assert "coin" in data
    assert data["coin"] == "BTC"
    assert "levels" in data
    assert "time" in data

    # The l2 book has levels as [bids, asks]
    levels = data["levels"]
    assert isinstance(levels, list)
    assert len(levels) == 2  # Should have bids and asks

    bids, asks = levels
    assert isinstance(bids, list)
    assert isinstance(asks, list)

    # Check structure of a few levels if they exist
    for level_list in [bids[:3], asks[:3]]:  # Check first 3 of each
        for level in level_list:
            assert "px" in level  # price
            assert "sz" in level  # size
            assert "n" in level  # number of orders
            assert isinstance(level["px"], str)
            assert isinstance(level["sz"], str)
            assert isinstance(level["n"], int)
            # Price and size should be convertible to float
            assert float(level["px"]) > 0
            assert float(level["sz"]) >= 0

    # Clean up: unsubscribe
    await subscriptions_client.unsubscribe(subscription_id)


async def test_trades_subscription(subscriptions_client: Subscriptions) -> None:
    """Test subscribing to trades updates."""
    # Subscribe to trades
    subscription_id, queue = await subscriptions_client.trades(asset="BTC")

    # Verify the subscription was created
    assert isinstance(subscription_id, int)
    assert isinstance(queue, asyncio.Queue)

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "trades"
    assert "data" in message
    assert message["data"][0]["coin"] == "BTC"


async def test_order_updates_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to order updates."""
    # Subscribe to order updates
    with replace_values(
        subscriptions_client.transport, request={"user": TEST_ACCOUNT.address}
    ):
        subscription_id, queue = await subscriptions_client.order_updates()

    # Verify the subscription was created
    assert isinstance(subscription_id, int)
    assert isinstance(queue, asyncio.Queue)

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "orderUpdates"
    assert "data" in message
    update = message["data"][0]
    assert update["order"]["coin"] == "BTC"
    assert update["status"] == "open"


async def test_user_events_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to user events updates."""
    # Subscribe to user events
    with replace_values(
        subscriptions_client.transport, request={"user": TEST_ACCOUNT.address}
    ):
        subscription_id, queue = await subscriptions_client.user_events()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "user"
    assert "data" in message
    assert "fills" in message["data"]
    # TODO: Add Type guard and deeper checks


async def test_user_fills_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to user fills updates."""
    # Subscribe to user fills
    with replace_values(
        subscriptions_client.transport,
        request={
            "user": TEST_ACCOUNT.address,
            "0.message.data.user": TEST_ACCOUNT.address,
        },
    ):
        subscription_id, queue = await subscriptions_client.user_fills()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "userFills"
    assert "data" in message
    assert "fills" in message["data"]
    fills = message["data"]["fills"]
    assert isinstance(fills, list)
    assert len(fills) > 0
    fill = fills[0]
    assert fill["coin"] == "BTC"
    assert fill["side"] == "A"


async def test_user_fundings_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to user fundings updates."""
    # Subscribe to user fundings
    with replace_values(
        subscriptions_client.transport,
        request={
            "user": TEST_ACCOUNT.address,
            "0.message.data.user": TEST_ACCOUNT.address,
        },
    ):
        subscription_id, queue = await subscriptions_client.user_fundings()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "userFundings"
    assert "data" in message
    assert "fundings" in message["data"]
    fundings = message["data"]["fundings"]
    assert isinstance(fundings, list)
    funding = fundings[0]
    assert funding["coin"] == "BTC"


async def test_user_non_funding_ledger_updates_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to user non-funding ledger updates."""
    # Subscribe to user non-funding ledger updates
    with replace_values(
        subscriptions_client.transport,
        request={
            "user": TEST_ACCOUNT.address,
            "0.message.data.user": TEST_ACCOUNT.address,
        },
    ):
        (
            subscription_id,
            queue,
        ) = await subscriptions_client.user_non_funding_ledger_updates()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "userNonFundingLedgerUpdates"
    assert "data" in message
    assert "nonFundingLedgerUpdates" in message["data"]
    updates = message["data"]["nonFundingLedgerUpdates"]
    assert isinstance(updates, list)
    # TODO: Add Type guard and deeper checks


async def test_active_asset_ctx_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to active asset context updates."""
    # Subscribe to active asset context
    subscription_id, queue = await subscriptions_client.active_asset_ctx(asset="BTC")

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "activeAssetCtx"
    assert "data" in message
    assert "coin" in message["data"]
    assert message["data"]["coin"] == "BTC"


async def test_active_asset_data_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to active asset data updates."""
    with replace_values(
        subscriptions_client.transport,
        request={
            "user": TEST_ACCOUNT.address,
            "0.message.data.user": TEST_ACCOUNT.address,
            "1.message.data.user": TEST_ACCOUNT.address,
        },
    ):
        # Subscribe to active asset data
        subscription_id, queue = await subscriptions_client.active_asset_data(
            asset="BTC"
        )

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "activeAssetData"
    assert "data" in message
    assert "coin" in message["data"]
    assert message["data"]["coin"] == "BTC"
    assert "leverage" in message["data"]
    assert "maxTradeSzs" in message["data"]
    assert "availableToTrade" in message["data"]


async def test_user_twap_slice_fills_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to user TWAP slice fills updates."""
    with replace_values(
        subscriptions_client.transport,
        request={
            "user": TEST_ACCOUNT.address,
            "0.message.data.user": TEST_ACCOUNT.address,
        },
    ):
        # Subscribe to user TWAP slice fills
        subscription_id, queue = await subscriptions_client.user_twap_slice_fills()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "userTwapSliceFills"
    assert "data" in message
    assert "twapSliceFills" in message["data"]
    twap_slice_fills = message["data"]["twapSliceFills"]
    assert isinstance(twap_slice_fills, list)
    assert len(twap_slice_fills) > 0
    twap_slice_fill = twap_slice_fills[0]
    assert "fill" in twap_slice_fill
    assert "twapId" in twap_slice_fill
    assert "time" in twap_slice_fill["fill"]
    assert "startPosition" in twap_slice_fill["fill"]
    assert "dir" in twap_slice_fill["fill"]
    assert "closedPnl" in twap_slice_fill["fill"]


async def test_user_twap_history_subscription(
    subscriptions_client: Subscriptions, replace_values: ReplaceValues
) -> None:
    """Test subscribing to user TWAP history updates."""
    with replace_values(
        subscriptions_client.transport,
        request={
            "user": TEST_ACCOUNT.address,
            "0.message.data.user": TEST_ACCOUNT.address,
        },
    ):
        # Subscribe to user TWAP history
        subscription_id, queue = await subscriptions_client.user_twap_history()

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "userTwapHistory"
    assert "data" in message
    assert "history" in message["data"]
    history = message["data"]["history"]
    assert isinstance(history, list)
    assert len(history) > 0
    history_item = history[0]
    assert history_item["state"]["coin"] == "BTC"
    assert history_item["state"]["side"] == "B"


async def test_best_bid_offer_subscription(subscriptions_client: Subscriptions) -> None:
    """Test subscribing to best bid offer updates."""
    # Subscribe to best bid offer
    subscription_id, queue = await subscriptions_client.best_bid_offer(asset="BTC")

    # Wait for at least one message (captured for 5 seconds)
    message = await asyncio.wait_for(queue.get(), timeout=6.0)

    # Verify the message structure
    assert isinstance(message, dict)
    assert message["channel"] == "bbo"
    assert message["data"]["coin"] == "BTC"
