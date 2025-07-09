# Subscriptions

[Hyperliquid's Official Subscriptions Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions)

## Overview

The WebSocket Subscriptions interface provides access to real-time data streams from the Hyperliquid exchange. Unlike traditional HTTP endpoints that require polling for updates, subscriptions deliver data continuously as it becomes available, making them ideal for applications requiring live market data, order monitoring, and account tracking.

The `Subscriptions` class offers methods to subscribe to various data feeds including market data, user-specific events, and asset context updates. All subscription methods return a subscription ID and an asyncio queue for receiving messages, enabling efficient real-time data processing.

## Key Features

- **Real-time Market Data**: Live order books, trades, and candlestick updates
- **User Account Monitoring**: Order updates, fills, funding payments, and ledger changes
- **Asset Context Streams**: Live asset pricing and availability information
- **Queue-based Delivery**: Receive messages through asyncio queues for async processing
- **Subscription Management**: Easy subscribe/unsubscribe with unique subscription IDs
- **Flexible Authentication**: Support for both address strings and Account objects
- **Automatic Asset Resolution**: Use asset names or IDs with automatic conversion

## Authentication Methods

The Subscriptions class supports flexible authentication for user-specific subscriptions:

1. **Class-level account** - Set during `Api.create()` and used automatically
2. **Method-level address** - Pass address string directly to methods
3. **Method-level account** - Pass different Account object for specific subscriptions

```python
# Method 1: Class-level account (recommended)
api = await Api.create(account=account)
async with api.ws.run():
    sid, queue = await api.ws.subscriptions.order_updates()  # Uses class account

# Method 2: Direct address
async with api.ws.run():
    sid, queue = await api.ws.subscriptions.order_updates(address="0x...")

# Method 3: Different account per subscription
other_account = Account(address="0x...", secret_key="0x...")
async with api.ws.run():
    sid, queue = await api.ws.subscriptions.order_updates(account=other_account)
```

## Methods Reference

### Market Data Subscriptions
- [**`all_mids()`**](../../reference/subscriptions.md#hl.Subscriptions.all_mids): Subscribe to all mid prices for all actively traded coins
- [**`l2_book()`**](../../reference/subscriptions.md#hl.Subscriptions.l2_book): Subscribe to Level 2 order book updates for a specific asset
- [**`trades()`**](../../reference/subscriptions.md#hl.Subscriptions.trades): Subscribe to trade updates for a specific asset
- [**`candle()`**](../../reference/subscriptions.md#hl.Subscriptions.candle): Subscribe to candlestick updates for a specific asset and interval
- [**`best_bid_offer()`**](../../reference/subscriptions.md#hl.Subscriptions.best_bid_offer): Subscribe to best bid/offer updates for a specific asset

### User Account Subscriptions  
- [**`notification()`**](../../reference/subscriptions.md#hl.Subscriptions.notification): Subscribe to notifications for a user
- [**`web_data2()`**](../../reference/subscriptions.md#hl.Subscriptions.web_data2): Subscribe to comprehensive user account data updates
- [**`order_updates()`**](../../reference/subscriptions.md#hl.Subscriptions.order_updates): Subscribe to order status updates for a user
- [**`user_events()`**](../../reference/subscriptions.md#hl.Subscriptions.user_events): Subscribe to user events (fills, funding, liquidations, cancellations)
- [**`user_fills()`**](../../reference/subscriptions.md#hl.Subscriptions.user_fills): Subscribe to user fill updates
- [**`user_fundings()`**](../../reference/subscriptions.md#hl.Subscriptions.user_fundings): Subscribe to user funding payment updates
- [**`user_non_funding_ledger_updates()`**](../../reference/subscriptions.md#hl.Subscriptions.user_non_funding_ledger_updates): Subscribe to non-funding ledger updates (deposits, withdrawals, transfers)
- [**`user_twap_slice_fills()`**](../../reference/subscriptions.md#hl.Subscriptions.user_twap_slice_fills): Subscribe to user TWAP slice fill updates
- [**`user_twap_history()`**](../../reference/subscriptions.md#hl.Subscriptions.user_twap_history): Subscribe to user TWAP history updates

### Asset Context Subscriptions
- [**`active_asset_ctx()`**](../../reference/subscriptions.md#hl.Subscriptions.active_asset_ctx): Subscribe to active asset context updates for a specific asset
- [**`active_asset_data()`**](../../reference/subscriptions.md#hl.Subscriptions.active_asset_data): Subscribe to active asset data for a user and specific asset

### Subscription Management
- [**`unsubscribe()`**](../../reference/subscriptions.md#hl.Subscriptions.unsubscribe): Unsubscribe from a specific subscription using its ID

## Usage Examples

### Basic Market Data Subscriptions

The SDK supports two approaches for handling multiple subscriptions:

1. **Individual Queues**: Each subscription gets its own queue (good for specific stream processing)
2. **Shared Queues**: Multiple subscriptions share a single queue (recommended for unified processing)

```python
from hl import Api
import asyncio

async def market_data_streams():
    api = await Api.create()

    async with api.ws.run():
        # Option 1: Individual queues (original approach)
        book_sid, book_queue = await api.ws.subscriptions.l2_book(asset="BTC")
        trades_sid, trades_queue = await api.ws.subscriptions.trades(asset="ETH")

        # Process a few messages from each stream
        for _ in range(5):
            # Process book updates
            try:
                book_msg = await asyncio.wait_for(book_queue.get(), timeout=1.0)
                book_data = book_msg["data"]
                bids = book_data["levels"][0]
                asks = book_data["levels"][1]
                print(f"📊 BTC Book: {len(bids)} bids, {len(asks)} asks")
            except asyncio.TimeoutError:
                pass

            # Process trade updates
            try:
                trade_msg = await asyncio.wait_for(trades_queue.get(), timeout=1.0)
                trades = trade_msg["data"]
                print(f"⚡ ETH Trades: {len(trades)} new trades")

                for trade in trades:
                    print(f"  Trade: {trade['sz']} ETH at ${trade['px']}")
            except asyncio.TimeoutError:
                pass

        # Clean up subscriptions
        await api.ws.subscriptions.unsubscribe(book_sid)
        await api.ws.subscriptions.unsubscribe(trades_sid)

asyncio.run(market_data_streams())
```

### Alternative: Shared Queue for Market Data

```python
async def market_data_shared_queue():
    api = await Api.create()

    async with api.ws.run():
        # Option 2: Shared queue (recommended for multiple streams)
        market_queue = asyncio.Queue()

        # Subscribe to multiple streams using shared queue
        book_sid, _ = await api.ws.subscriptions.l2_book(asset="BTC", queue=market_queue)
        trades_sid, _ = await api.ws.subscriptions.trades(asset="ETH", queue=market_queue)
        candle_sid, _ = await api.ws.subscriptions.candle(asset="BTC", interval="1m", queue=market_queue)

        # Process messages from any stream as they arrive
        message_count = 0
        while message_count < 30:  # Process 30 messages then exit
            msg = await market_queue.get()

            if msg["channel"] == "l2Book":
                book = msg["data"]
                bids = book["levels"][0]
                asks = book["levels"][1]
                spread = float(asks[0]["px"]) - float(bids[0]["px"]) if bids and asks else 0
                print(f"📊 {book['coin']} Book: {len(bids)} bids, {len(asks)} asks, spread: ${spread:.2f}")

            elif msg["channel"] == "trades":
                trades = msg["data"]
                if trades:
                    coin = trades[0]["coin"]
                    total_volume = sum(float(t["sz"]) for t in trades)
                    print(f"⚡ {coin} Trades: {len(trades)} trades, {total_volume:.4f} {coin} volume")

            elif msg["channel"] == "candle":
                candle = msg["data"]
                print(f"🕯️ {candle['s']} {candle['i']} candle: O=${candle['o']} H=${candle['h']} L=${candle['l']} C=${candle['c']}")

            message_count += 1

        # Clean up subscriptions
        await api.ws.subscriptions.unsubscribe(book_sid)
        await api.ws.subscriptions.unsubscribe(trades_sid)
        await api.ws.subscriptions.unsubscribe(candle_sid)

asyncio.run(market_data_shared_queue())
```

### User Account Monitoring

```python
from hl import Api, Account
import os

async def account_monitoring():
    # Initialize with account for user-specific subscriptions
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )
    api = await Api.create(account=account)

    async with api.ws.run():
        # Create a shared queue for all account-related subscriptions
        account_queue = asyncio.Queue()

        # Subscribe to multiple account streams using the shared queue
        orders_sid, _ = await api.ws.subscriptions.order_updates(queue=account_queue)
        fills_sid, _ = await api.ws.subscriptions.user_fills(queue=account_queue)
        web_data_sid, _ = await api.ws.subscriptions.web_data2(queue=account_queue)

        # Monitor account activity
        message_count = 0
        while message_count < 100:  # Process 100 messages then exit
            msg = await account_queue.get()

            if msg["channel"] == "orderUpdates":
                updates = msg["data"]
                for update in updates:
                    print(f"📋 Order {update['order']['oid']}: {update['status']}")

            elif msg["channel"] == "userFills":
                fills_data = msg["data"]
                fills = fills_data["fills"]
                print(f"💰 New fills: {len(fills)} trades")

                for fill in fills:
                    print(f"  {fill['coin']}: {fill['sz']} at ${fill['px']}")

            elif msg["channel"] == "webData2":
                data = msg["data"]
                balance = data["clearingHouseState"]["withdrawable"]
                print(f"💳 Account balance: ${balance}")

            message_count += 1

        # Clean up subscriptions
        await api.ws.subscriptions.unsubscribe(orders_sid)
        await api.ws.subscriptions.unsubscribe(fills_sid)
        await api.ws.subscriptions.unsubscribe(web_data_sid)

asyncio.run(account_monitoring())
```

### Real-time Price Monitoring

```python
async def price_monitoring():
    api = await Api.create()

    async with api.ws.run():
        # Monitor all mid prices
        mids_sid, mids_queue = await api.ws.subscriptions.all_mids()

        # Track price changes
        last_prices = {}

        for _ in range(50):  # Monitor 50 updates
            msg = await mids_queue.get()
            mids_data = msg["data"]
            current_mids = mids_data["mids"]

            # Check for significant price changes
            for coin, price_str in current_mids.items():
                price = float(price_str)

                if coin in last_prices:
                    last_price = last_prices[coin]
                    change_pct = ((price - last_price) / last_price) * 100

                    # Alert on significant moves (>1%)
                    if abs(change_pct) > 1.0:
                        direction = "📈" if change_pct > 0 else "📉"
                        print(f"{direction} {coin}: ${last_price:.2f} → ${price:.2f} ({change_pct:+.2f}%)")

                last_prices[coin] = price

asyncio.run(price_monitoring())
```

### Advanced Multi-stream Processing

```python
async def advanced_monitoring():
    api = await Api.create(account=account)

    async with api.ws.run():
        # Create a shared queue for all data streams
        monitoring_queue = asyncio.Queue()

        # Subscribe to multiple streams using the shared queue
        subscription_ids = []

        # Market data streams
        btc_book_sid, _ = await api.ws.subscriptions.l2_book(asset="BTC", queue=monitoring_queue)
        eth_trades_sid, _ = await api.ws.subscriptions.trades(asset="ETH", queue=monitoring_queue)
        all_mids_sid, _ = await api.ws.subscriptions.all_mids(queue=monitoring_queue)

        # User streams
        user_fills_sid, _ = await api.ws.subscriptions.user_fills(queue=monitoring_queue)
        order_updates_sid, _ = await api.ws.subscriptions.order_updates(queue=monitoring_queue)

        # Keep track of subscription IDs for cleanup
        subscription_ids = [btc_book_sid, eth_trades_sid, all_mids_sid, user_fills_sid, order_updates_sid]

        # Process messages as they arrive
        message_count = 0
        while message_count < 200:  # Process 200 messages then exit
            msg = await monitoring_queue.get()

            # Process based on message channel
            if msg["channel"] == "l2Book":
                book = msg["data"]
                if book["coin"] == "BTC":
                    spread = float(book["levels"][1][0]["px"]) - float(book["levels"][0][0]["px"])
                    print(f"📊 BTC spread: ${spread:.2f}")

            elif msg["channel"] == "trades":
                trades = msg["data"]
                if trades and trades[0]["coin"] == "ETH":
                    volume = sum(float(t["sz"]) for t in trades)
                    avg_price = sum(float(t["px"]) for t in trades) / len(trades)
                    print(f"⚡ ETH: {len(trades)} trades, {volume:.4f} ETH vol, avg ${avg_price:.2f}")

            elif msg["channel"] == "allMids":
                mids = msg["data"]["mids"]
                btc_price = float(mids.get("BTC", "0"))
                eth_price = float(mids.get("ETH", "0"))
                print(f"💹 Prices: BTC ${btc_price:.0f}, ETH ${eth_price:.0f}")

            elif msg["channel"] == "userFills":
                fills_data = msg["data"]
                if fills_data["fills"]:
                    print(f"🎯 You have {len(fills_data['fills'])} new fills!")
                    for fill in fills_data["fills"]:
                        pnl = fill.get("closedPnl", "0")
                        if float(pnl) != 0:
                            print(f"  💰 {fill['coin']}: {fill['sz']} at ${fill['px']} (PnL: ${pnl})")

            elif msg["channel"] == "orderUpdates":
                updates = msg["data"]
                for update in updates:
                    status = update["status"]
                    coin = update["order"]["coin"]
                    oid = update["order"]["oid"]

                    if status == "filled":
                        print(f"✅ Order {oid} ({coin}) filled!")
                    elif status == "canceled":
                        print(f"❌ Order {oid} ({coin}) canceled")
                    else:
                        print(f"📋 Order {oid} ({coin}): {status}")

            message_count += 1

        # Clean up all subscriptions
        for sid in subscription_ids:
            await api.ws.subscriptions.unsubscribe(sid)

asyncio.run(advanced_monitoring())
```

## Subscription Details

For complete method signatures and parameters, see the [**API Reference →**](../../reference/subscriptions.md)

### Market Data Subscriptions

#### All Mids
Subscribe to all mid prices for all actively traded coins.

```python
sid, queue = await api.ws.subscriptions.all_mids()

# Message format
{
    "channel": "allMids",
    "data": {
        "mids": {
            "BTC": "65000.0",
            "ETH": "3500.0",
            "SOL": "150.0"
        }
    }
}
```

#### L2 Book
Subscribe to Level 2 order book updates for a specific asset.

```python
# Basic subscription
sid, queue = await api.ws.subscriptions.l2_book(asset="BTC")

# With price aggregation
sid, queue = await api.ws.subscriptions.l2_book(
    asset="BTC",
    n_sig_figs=3,  # Round to 3 significant figures
    mantissa=2     # Group by price levels
)

# Message format
{
    "channel": "l2Book",
    "data": {
        "coin": "BTC",
        "levels": [
            [  # Bids
                {"px": "64990.0", "sz": "0.5", "n": 2},
                {"px": "64980.0", "sz": "1.2", "n": 1}
            ],
            [  # Asks
                {"px": "65010.0", "sz": "0.8", "n": 1},
                {"px": "65020.0", "sz": "2.1", "n": 3}
            ]
        ],
        "time": 1640995200000
    }
}
```

#### Trades
Subscribe to trade updates for a specific asset.

```python
sid, queue = await api.ws.subscriptions.trades(asset="BTC")

# Message format
{
    "channel": "trades",
    "data": [
        {
            "coin": "BTC",
            "side": "B",  # "B" for buy, "A" for sell
            "px": "65000.0",
            "sz": "0.001",
            "time": 1640995200000,
            "hash": "0x...",
            "tid": 123456
        }
    ]
}
```

#### Candles
Subscribe to candlestick updates for a specific asset and interval.

```python
# Available intervals: "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "8h", "12h", "1d", "3d", "1w", "1M"
sid, queue = await api.ws.subscriptions.candle(asset="BTC", interval="1m")

# Message format
{
    "channel": "candle",
    "data": {
        "s": "BTC",
        "i": "1m",
        "t": 1640995200000,  # Start time
        "T": 1640995260000,  # End time
        "o": "64950.0",      # Open
        "h": "65100.0",      # High
        "l": "64900.0",      # Low
        "c": "65050.0",      # Close
        "v": "125.5",        # Volume
        "n": 245             # Number of trades
    }
}
```

### User Account Subscriptions

#### Order Updates
Subscribe to order status updates for a user.

```python
sid, queue = await api.ws.subscriptions.order_updates()

# Message format
{
    "channel": "orderUpdates",
    "data": [
        {
            "order": {
                "coin": "BTC",
                "side": "B",
                "limitPx": "65000.0",
                "sz": "0.001",
                "oid": 123456,
                "timestamp": 1640995200000,
                "origSz": "0.001"
            },
            "status": "filled",
            "statusTimestamp": 1640995205000
        }
    ]
}
```

#### User Fills
Subscribe to user fill updates.

```python
sid, queue = await api.ws.subscriptions.user_fills(aggregate_by_time=True)

# Message format
{
    "channel": "userFills",
    "data": {
        "user": "0x...",
        "fills": [
            {
                "coin": "BTC",
                "px": "65000.0",
                "sz": "0.001",
                "side": "B",
                "time": 1640995200000,
                "oid": 123456,
                "startPosition": "0.0",
                "dir": "Open Long",
                "closedPnl": "0",
                "hash": "0x...",
                "fee": "0.65",
                "feeToken": "USDC"
            }
        ],
        "isSnapshot": false  # Present only in first message
    }
}
```

## Best Practices

1. **Use Context Managers**: Always use `async with api.ws.run():` for proper connection management
2. **Handle Queues Efficiently**: Process messages promptly to prevent queue overflow
3. **Unsubscribe When Done**: Clean up subscriptions to reduce unnecessary traffic
4. **Use Shared Queues**: For multiple subscriptions, consider using a shared queue for unified processing
5. **Handle Snapshots**: First messages often contain `isSnapshot: true` with historical data
6. **Monitor Message Rates**: Be aware of high-frequency streams like trades and book updates
7. **Set Timeouts**: Use `asyncio.wait_for()` to avoid indefinite blocking when appropriate

## Performance Considerations

- **Queue Size Management**: Monitor queue sizes and process messages quickly
- **Subscription Limits**: Limit the number of active subscriptions to manage bandwidth
- **Message Filtering**: Process only relevant messages to reduce CPU usage
- **Memory Usage**: Long-running subscriptions should monitor memory for queue buildup
- **Network Bandwidth**: High-frequency streams can consume significant bandwidth
