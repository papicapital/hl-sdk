import asyncio
import os
from decimal import Decimal
from typing import AsyncGenerator

import pytest

from hl import TESTNET, Account, Universe, Ws
from hl.types import AssetInfo
from tests.conftest import ReplaceValues
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
async def ws_client() -> AsyncGenerator[Ws, None]:
    """Create a Ws client with MockWsTransport for testing."""
    # Create the Ws instance
    ws = Ws(
        network=TESTNET,
        universe=MOCK_UNIVERSE,
        account=TEST_ACCOUNT,
    )

    # Replace the transport with a mock transport
    real_transport = ws._transport
    mock_transport = MockWsTransport(
        real_transport,
        capture_duration=5.0,
    )
    ws._transport = mock_transport

    # Update the transport in all sub-components if they're already initialized
    if ws._subscriptions:
        ws._subscriptions.transport = mock_transport
    if ws._info:
        ws._info.transport = mock_transport
    if ws._exchange:
        ws._exchange.transport = mock_transport

    # Start the mock transport
    mock_transport.start()

    try:
        # Start the WebSocket connection in the background
        async with ws.run():
            yield ws
    finally:
        # Clean up after the context manager exits
        await mock_transport.stop()


async def test_ws_subscriptions_all_mids(ws_client: Ws) -> None:
    """Test subscribing to all mids updates using ws.subscriptions."""
    # Subscribe to all mids
    subscription_id, queue = await ws_client.subscriptions.all_mids()

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


async def test_ws_info_all_mids(ws_client: Ws) -> None:
    """Test getting all mids data using ws.info."""
    # Get all mids data via info endpoint
    result = await ws_client.info.all_mids()

    assert result.is_ok()
    all_mids_data = result.unwrap()

    # Verify the response structure
    assert isinstance(all_mids_data, dict)

    # The response should contain mid prices for various assets
    assert len(all_mids_data) > 0

    # Check that all values are numeric strings
    for coin, price in all_mids_data.items():
        assert isinstance(coin, str)
        assert isinstance(price, str)

    # Verify BTC is in the response (since it's in our mock universe)
    assert "BTC" in all_mids_data


async def test_ws_exchange_transfer_usd(
    ws_client: Ws, replace_values: ReplaceValues
) -> None:
    """Test transferring USD using ws.exchange."""
    # Define transfer parameters
    # Replace sensitive values in the request
    with replace_values(
        ws_client._transport,
        request={"action.nonce": 1751506435976},
    ):
        # Execute the transfer
        result = await ws_client.exchange.transfer_usd(
            to_perp=True,
            amount=Decimal("100.0"),
        )

    assert result.is_ok()
    response = result.unwrap()

    # # Verify the response structure
    assert isinstance(response, dict)
    assert response["status"] == "ok"
    assert "response" in response
    assert response["response"]["type"] == "default"

    # The transfer should be successful
    assert response["status"] == "ok"
