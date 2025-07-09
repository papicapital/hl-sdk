# WebSocket API

[Hyperliquid's Official Websocket Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket)

## Overview

The WebSocket API provides real-time access to market data, order updates, and account information through persistent connections. The `Ws` class serves as the main interface for WebSocket operations, offering unified access to subscriptions, info queries, and exchange operations over a single WebSocket connection.

Unlike HTTP endpoints that require individual requests for each piece of data, the WebSocket API enables continuous streaming of updates, making it ideal for applications that need real-time market data, order status monitoring, or account state tracking.

The `Ws` class provides three main interfaces:

- **Subscriptions** (`ws.subscriptions`) - Subscribe to real-time data streams
- **Info** (`ws.info`) - Query market and user data via WebSocket
- **Exchange** (`ws.exchange`) - Execute trading operations via WebSocket

## Key Features

- **Real-time Data Streams**: Subscribe to live market data, trades, and order book updates
- **Persistent Connection**: Single WebSocket connection shared across all operations
- **Unified Interface**: Access subscriptions, info queries, and trading through one client
- **Automatic Reconnection**: Built-in connection management and error handling
- **Queue-based Messages**: Receive streaming data through asyncio queues
- **Flexible Authentication**: Support for both address strings and Account objects
- **Connection Management**: Convenient context managers and lifecycle control

## Connection Management

The WebSocket client offers two primary ways to manage the connection lifecycle:

### Using `run()` Context Manager (Recommended)

The `run()` method provides automatic connection management with proper cleanup:

```python
from hl import Api
import asyncio

async def websocket_example():
    api = await Api.create()

    # Connection automatically managed
    async with api.ws.run():
        # Subscribe to real-time data
        sid, queue = await api.ws.subscriptions.l2_book(asset="BTC")

        # Process messages
        for _ in range(10):
            book = await queue.get()
            print(f"BTC book update: {len(book['levels'][0])} bids, {len(book['levels'][1])} asks")

        # Unsubscribe when done
        await api.ws.subscriptions.unsubscribe(sid)
    # Connection automatically closed when context exits

asyncio.run(websocket_example())
```

### Using `run_forever()` for Long-running Applications

For applications that need persistent WebSocket connections, use `run_forever()`:

```python
async def persistent_websocket():
    api = await Api.create()

    # Start WebSocket in background
    # NOTE: You must keep a reference to the created task to prevent it being garbage collected
    ws_task = asyncio.create_task(api.ws.run_forever())

    try:
        # Subscribe to multiple data streams
        sid, queue = await api.ws.subscriptions.l2_book(asset="BTC")

        # Process messages from multiple streams
        while True:
            # Check for book updates
            book = await queue.get()
            print(f"BTC book update: {len(book['levels'][0])} bids, {len(book['levels'][1])} asks")
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Clean shutdown
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass

asyncio.run(persistent_websocket())
```

## WebSocket Interfaces

### Subscriptions Interface

Access real-time data streams through `ws.subscriptions`. This interface provides methods to subscribe to various data feeds and receive continuous updates.

```python
# Market data subscriptions
sid, queue = await api.ws.subscriptions.l2_book(asset="BTC")
sid, queue = await api.ws.subscriptions.trades(asset="ETH")
sid, queue = await api.ws.subscriptions.candle(asset="BTC", interval="1m")

# User-specific subscriptions (requires authentication)
api = await Api.create(account=account)
sid, queue = await api.ws.subscriptions.order_updates()
sid, queue = await api.ws.subscriptions.user_fills()
```

**[📖 Complete Subscriptions Guide →](subscriptions.md)**

### Info Interface

Query market data and user information via WebSocket using the same methods as the HTTP Info endpoint:

```python
# Market data queries
result = await api.ws.info.all_mids()
result = await api.ws.info.l2_book(asset="BTC")

# User data queries (requires authentication)
result = await api.ws.info.user_open_orders()
result = await api.ws.info.user_state()
```

**[📖 Complete Info Guide →](../info.md)**

### Exchange Interface

Execute trading operations via WebSocket using the same methods as the HTTP Exchange endpoint:

```python
# Place orders via WebSocket
result = await api.ws.exchange.place_order(
    asset="BTC",
    is_buy=True,
    size=Decimal("0.001"),
    limit_price=Decimal("65000"),
    order_type=LIMIT_GTC,
    reduce_only=False
)

# Cancel orders
result = await api.ws.exchange.cancel_order(asset="BTC", order_id=123)
```

**[📖 Complete Exchange Guide →](../exchange.md)**

## Authentication

WebSocket authentication works the same as HTTP endpoints:

```python
from hl import Api, Account
import os

# Method 1: Class-level authentication
account = Account(
    address=os.environ["HL_ADDRESS"],
    secret_key=os.environ["HL_SECRET_KEY"]
)
api = await Api.create(account=account)

async with api.ws.run():
    # Uses class account automatically
    sid, queue = await api.ws.subscriptions.order_updates()

# Method 2: Method-level authentication
async with api.ws.run():
    # Pass address directly
    sid, queue = await api.ws.subscriptions.order_updates(address="0x...")

    # Or pass different account
    sid, queue = await api.ws.subscriptions.order_updates(account=other_account)
```

## Message Processing Patterns

### Single Subscription Processing

```python
async def process_single_stream():
    api = await Api.create()

    async with api.ws.run():
        sid, queue = await api.ws.subscriptions.trades(asset="BTC")

        # Process messages sequentially
        while True:
            msg = await queue.get()
            trades = msg["data"]

            for trade in trades:
                print(f"BTC trade: {trade['sz']} at ${trade['px']}")

            # Process only first 100 trades then exit
            if len(trades) >= 100:
                break
```

### Multiple Subscription Processing

```python
async def process_multiple_streams():
    api = await Api.create(account=account)

    async with api.ws.run():
        # Create a shared queue for all subscriptions
        shared_queue = asyncio.Queue()

        # Subscribe to multiple streams using the shared queue
        book_sid, _ = await api.ws.subscriptions.l2_book(asset="BTC", queue=shared_queue)
        fills_sid, _ = await api.ws.subscriptions.user_fills(queue=shared_queue)
        orders_sid, _ = await api.ws.subscriptions.order_updates(queue=shared_queue)

        # Process messages from any stream as they arrive
        message_count = 0
        while message_count < 50:  # Process 50 messages then exit
            msg = await shared_queue.get()

            # Process based on message channel
            if msg["channel"] == "l2Book":
                book_data = msg["data"]
                print(f"📊 Book update for {book_data['coin']}")

            elif msg["channel"] == "userFills":
                fills_data = msg["data"]
                fills = fills_data["fills"]
                print(f"💰 New fills: {len(fills)} trades")

                for fill in fills:
                    print(f"  {fill['coin']}: {fill['sz']} at ${fill['px']}")

            elif msg["channel"] == "orderUpdates":
                updates = msg["data"]
                for update in updates:
                    print(f"📋 Order {update['order']['oid']}: {update['status']}")

            message_count += 1

        # Clean up subscriptions
        await api.ws.subscriptions.unsubscribe(book_sid)
        await api.ws.subscriptions.unsubscribe(fills_sid)
        await api.ws.subscriptions.unsubscribe(orders_sid)
```
