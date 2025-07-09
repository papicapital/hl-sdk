# Hyperliquid SDK for Python

The `hl-sdk` is an unofficial Python client library for interacting with the [Hyperliquid](https://hyperliquid.xyz) API. It provides a modern, async-first interface for trading perpetual futures and spot assets on the Hyperliquid decentralized exchange.

## Why hl-sdk?

While Hyperliquid provides an official Python SDK, we developed `hl-sdk` to address specific needs:

- **Async-First Design**: Built from the ground up with `async/await` support for high-performance applications
- **Complete Type Safety**: Full type annotations for all methods, requests, and responses with zero `Any` types
- **100% API Coverage**: Every documented Hyperliquid API endpoint is implemented
- **Intuitive Interface**: Consistent method naming and clear separation between info, exchange, and WebSocket operations
- **Modern Python**: Leverages Python 3.11+ features for cleaner, more maintainable code

## Installation

Install `hl-sdk` using your preferred package manager:

=== "pip"

    ```bash
    pip install hl-sdk
    ```

=== "uv"

    ```bash
    uv add hl-sdk
    ```

!!! info "Package vs Module Name"
    The package is named `hl-sdk` but the module you import is simply `hl`:

    ```python
    from hl import Api, Account
    ```

## Quick Examples

### Info Endpoint - Get Market Data

Retrieve current market prices for all assets:

```python
import asyncio
from hl import Api

async def get_market_data():
    # Initialize API without authentication for public endpoints
    api = await Api.create()

    # Get current mid prices for all assets
    result = await api.info.all_mids()

    if result.is_ok():
        mids = result.unwrap()
        for asset, price in mids.items():
            print(f"{asset}: ${price}")
    else:
        print(f"Error: {result.unwrap_err()}")

asyncio.run(get_market_data())
```

### Exchange Endpoint - Place an Order

Place a limit order (requires authentication):

```python
import asyncio
import os
from decimal import Decimal
from hl import Api, Account, LIMIT_GTC

async def place_order():
    # Create account from environment variables
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    # Initialize API with authentication
    api = await Api.create(account=account)

    # Place a limit buy order for 0.001 BTC at $60,000
    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        limit_price=Decimal("60000"),
        order_type=LIMIT_GTC,  # Good till canceled
        reduce_only=False
    )

    if result.is_ok():
        response = result.unwrap()
        print(f"Order placed: {response}")
    else:
        print(f"Error: {result.unwrap_err()}")

asyncio.run(place_order())
```

### WebSocket Info Call - Real-time Queries

Use WebSocket for efficient repeated queries:

```python
import asyncio
from hl import Api, Account

async def ws_info_example():
    api = await Api.create()

    # Use WebSocket context manager
    async with api.ws.run():
        # Get L2 order book via WebSocket
        result = await api.ws.info.l2_book(asset="ETH")

        if result.is_ok():
            book = result.unwrap()
            print(f"Best bid: ${book['levels'][0][0]['px']}")
            print(f"Best ask: ${book['levels'][1][0]['px']}")

asyncio.run(ws_info_example())
```

### WebSocket Subscription - Stream Real-time Data

Subscribe to live market updates:

```python
import asyncio
from hl import Api

async def stream_prices():
    api = await Api.create()

    async with api.ws.run():
        # Subscribe to all mid-price updates
        subscription_id, queue = await api.ws.subscriptions.all_mids()

        print("Streaming live prices (Ctrl+C to stop)...")

        # Process updates as they arrive
        while True:
            msg = await queue.get()

            # The message structure varies by subscription type
            # For all_mids, it's a dict of asset -> price
            print(f"Price update: {msg}")

asyncio.run(stream_prices())
```

### WebSocket Order Updates (Authenticated)

Monitor your order status in real-time:

```python
import asyncio
import os
from hl import Api, Account

async def monitor_orders():
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    api = await Api.create(account=account)

    async with api.ws.run():
        # Subscribe to order updates for your account
        subscription_id, queue = await api.ws.subscriptions.order_updates()

        print("Monitoring order updates...")

        while True:
            update = await queue.get()
            print(f"Order update: {update}")

asyncio.run(monitor_orders())
```

## Core Concepts

- **Async-First**: All API calls are asynchronous. Use `await` for all operations.
- **Result Type**: Methods return `Result[T, ApiError]` for explicit error handling.
- **Authentication**: Create an `Account` object with your address and private key for authenticated endpoints.
- **WebSocket Context**: Use `async with api.ws.run()` to manage WebSocket connections.

## Next Steps

- Read the [Guides](./guides/index.md) for a comprehensive introduction
- Explore the [API Reference](./reference/index.md) for detailed documentation
- Check out [Examples](https://github.com/papicapital/hl-sdk/tree/main/examples) for more complex use cases
- Join our [GitHub Discussions](https://github.com/papicapital/hl-sdk/discussions) for support

## Support

For bugs, feature requests, or contributions, visit our [GitHub repository](https://github.com/papicapital/hl-sdk).

Join our community:
- [Discord Community - Papi's Pit](https://discord.gg/rDAG9RTsbj) for real-time chat and community support

