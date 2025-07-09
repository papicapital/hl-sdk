# Exchange Endpoint

[Hyperliquid's Official Exchange Endpoint Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint)

## Overview

The Exchange endpoint provides comprehensive trading and account management functionality for the Hyperliquid platform. This endpoint handles all operations that require cryptographic signatures and interact with on-chain assets, including order placement, position management, asset transfers, and account configuration.

The `Exchange` class serves as the primary interface for executing trades, managing positions, and performing account operations. All methods require proper authentication through cryptographic signatures and work with both perpetual and spot markets. The class handles the complexity of transaction signing, parameter validation, and communication with the Hyperliquid exchange infrastructure.

## Key Features

- **Order Management**: Place, modify, and cancel orders with full control over execution parameters
- **Position Control**: Manage leverage, margin, and position sizing across all markets
- **Asset Transfers**: Send assets between addresses, wallets, and external chains
- **Account Configuration**: Set up sub-accounts, agents, referrers, and vault functionality
- **TWAP Orders**: Execute time-weighted average price orders for large positions
- **Staking Operations**: Stake and delegate HYPE tokens for network participation
- **Cross-Product Support**: Unified interface for both perpetual and spot trading
- **Batch Operations**: Execute multiple orders or modifications in single transactions


## Methods Reference

### Order Management
- [**`place_orders()`**](../reference/exchange.md#hl.Exchange.place_orders): Place multiple orders in a single transaction
- [**`place_order()`**](../reference/exchange.md#hl.Exchange.place_order): Place a single order with specified parameters
- [**`cancel_orders()`**](../reference/exchange.md#hl.Exchange.cancel_orders): Cancel multiple orders by their order IDs
- [**`cancel_order()`**](../reference/exchange.md#hl.Exchange.cancel_order): Cancel a single order by its order ID
- [**`cancel_orders_by_id()`**](../reference/exchange.md#hl.Exchange.cancel_orders_by_id): Cancel multiple orders by their client order IDs
- [**`cancel_order_by_id()`**](../reference/exchange.md#hl.Exchange.cancel_order_by_id): Cancel a single order by its client order ID
- [**`schedule_cancellation()`**](../reference/exchange.md#hl.Exchange.schedule_cancellation): Schedule automatic cancellation of all open orders at a future time
- [**`modify_order()`**](../reference/exchange.md#hl.Exchange.modify_order): Modify an existing order's parameters
- [**`modify_orders()`**](../reference/exchange.md#hl.Exchange.modify_orders): Modify multiple orders in a single transaction

### Position & Risk Management
- [**`update_leverage()`**](../reference/exchange.md#hl.Exchange.update_leverage): Update the leverage setting for a specific asset
- [**`update_margin()`**](../reference/exchange.md#hl.Exchange.update_margin): Add or remove margin from an isolated position
- [**`adjust_margin()`**](../reference/exchange.md#hl.Exchange.adjust_margin): Adjust isolated margin to achieve a target leverage ratio

### Asset Transfers
- [**`send_usd()`**](../reference/exchange.md#hl.Exchange.send_usd): Send USDC to another address on the Hyperliquid chain
- [**`send_spot()`**](../reference/exchange.md#hl.Exchange.send_spot): Send spot assets to another address
- [**`withdraw_funds()`**](../reference/exchange.md#hl.Exchange.withdraw_funds): Withdraw USDC to Arbitrum or other supported chains
- [**`transfer_usd()`**](../reference/exchange.md#hl.Exchange.transfer_usd): Transfer USDC between spot and perpetual trading accounts
- [**`transfer_tokens()`**](../reference/exchange.md#hl.Exchange.transfer_tokens): Transfer tokens between spot and perpetual accounts for specific DEXes
- [**`transfer_vault_funds()`**](../reference/exchange.md#hl.Exchange.transfer_vault_funds): Transfer USDC between personal account and trading vaults
- [**`transfer_account_funds()`**](../reference/exchange.md#hl.Exchange.transfer_account_funds): Transfer funds between main account and sub-accounts

### TWAP Orders
- [**`place_twap()`**](../reference/exchange.md#hl.Exchange.place_twap): Place a time-weighted average price order
- [**`cancel_twap()`**](../reference/exchange.md#hl.Exchange.cancel_twap): Cancel an active TWAP order

### Staking & Delegation
- [**`stake_tokens()`**](../reference/exchange.md#hl.Exchange.stake_tokens): Stake HYPE tokens for network participation
- [**`unstake_tokens()`**](../reference/exchange.md#hl.Exchange.unstake_tokens): Unstake HYPE tokens from the network
- [**`delegate_tokens()`**](../reference/exchange.md#hl.Exchange.delegate_tokens): Delegate or undelegate HYPE tokens to validators

### Authorization & Access Control
- [**`approve_agent()`**](../reference/exchange.md#hl.Exchange.approve_agent): Authorize an API wallet or agent to trade on behalf of the account
- [**`approve_builder()`**](../reference/exchange.md#hl.Exchange.approve_builder): Approve maximum builder fees for specific addresses

### Account Management
- [**`set_referrer()`**](../reference/exchange.md#hl.Exchange.set_referrer): Set a referral code for fee discounts
- [**`register_referrer()`**](../reference/exchange.md#hl.Exchange.register_referrer): Register as a referrer to earn commissions
- [**`create_vault()`**](../reference/exchange.md#hl.Exchange.create_vault): Create a new trading vault
- [**`create_sub_account()`**](../reference/exchange.md#hl.Exchange.create_sub_account): Create a new sub-account for portfolio separation
- [**`reserve_weight()`**](../reference/exchange.md#hl.Exchange.reserve_weight): Purchase additional rate limit weight for high-frequency trading

## Usage Examples

### Authentication Requirements

All Exchange methods require authentication and will automatically use the account provided during `Api.create()` or the account passed to individual methods:

```python
# Class-level authentication (recommended)
api = await Api.create(account=account)
result = await api.exchange.place_order(...)  # Uses class account

# Method-level authentication
result = await api.exchange.place_order(..., account=different_account)
```


### Basic Order Management

```python
from decimal import Decimal
from hl import Api, Account, Cloid, LIMIT_GTC, LIMIT_IOC, LIMIT_ALO
from hl.types import is_resting_status, is_error_status, is_filled_status
import os

async def basic_trading():
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )
    api = await Api.create(account=account)

    # Place a single limit order using predefined constants
    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        limit_price=Decimal("65000"),
        order_type=LIMIT_GTC,  # Using predefined constant
        reduce_only=False
    )

    if result.is_ok():
        response = result.unwrap()
        # Check individual order statuses, not just top-level status
        statuses = response["response"]["data"]["statuses"]
        for status in statuses:
            if is_resting_status(status):
                oid = status["resting"]["oid"]
                print(f"Order {oid} is resting on the book")
            elif is_error_status(status):
                error = status["error"]
                print(f"Order failed: {error}")
            elif is_filled_status(status):
                fill = status["filled"]
                print(f"Order {fill['oid']} filled {fill['totalSz']} at {fill['avgPx']}")

    # Place multiple orders at once
    orders = [
        {
            "asset": "BTC",
            "is_buy": True,
            "size": Decimal("0.001"),
            "limit_price": Decimal("64000"),
            "order_type": LIMIT_GTC,  # Good till canceled
            "reduce_only": False
        },
        {
            "asset": "ETH",
            "is_buy": False,
            "size": Decimal("0.1"),
            "limit_price": Decimal("3500"),
            "order_type": LIMIT_IOC,  # Immediate or cancel
            "reduce_only": False
        }
    ]

    result = await api.exchange.place_orders(order_requests=orders)
    if result.is_ok():
        response = result.unwrap()
        # Handle multiple order statuses
        statuses = response["response"]["data"]["statuses"]
        for i, status in enumerate(statuses):
            print(f"Order {i+1} result:")
            if is_resting_status(status):
                oid = status["resting"]["oid"]
                print(f"  Resting as order {oid}")
            elif is_error_status(status):
                error = status["error"]
                print(f"  Failed: {error}")
            elif is_filled_status(status):
                fill = status["filled"]
                print(f"  Filled {fill['totalSz']} at {fill['avgPx']}")

asyncio.run(basic_trading())
```

### Position and Risk Management

```python
async def manage_positions():
    api = await Api.create(account=account)

    # Update leverage for BTC position
    result = await api.exchange.update_leverage(
        asset="BTC",
        leverage=10,
        margin_mode="cross"
    )

    if result.is_ok():
        print("Leverage updated successfully")

    # Add margin to isolated position
    result = await api.exchange.update_margin(
        asset="ETH",
        amount=Decimal("1000")  # Add $1000 USDC
    )

    # Target specific leverage ratio for isolated position
    result = await api.exchange.adjust_margin(
        asset="BTC",
        leverage=Decimal("5.0")
    )

asyncio.run(manage_positions())
```

### Asset Transfers and Withdrawals

```python
async def handle_transfers():
    api = await Api.create(account=account)

    # Send USDC to another address
    result = await api.exchange.send_usd(
        amount=Decimal("100"),
        destination="0x742d35Cc6634C0532925a3b8D2D0e92B5b6B5..."
    )

    # Transfer between spot and perp accounts
    result = await api.exchange.transfer_usd(
        amount=Decimal("500"),
        to_perp=True  # Move from spot to perp
    )

    # Withdraw to external chain (Arbitrum)
    result = await api.exchange.withdraw_funds(
        amount=Decimal("1000"),
        destination="0x742d35Cc6634C0532925a3b8D2D0e92B5b6B5..."
    )

    if result.is_ok():
        print("Withdrawal initiated")

asyncio.run(handle_transfers())
```

### Order Cancellation and Modification

```python
from hl import LIMIT_GTC

async def manage_orders():
    api = await Api.create(account=account)

    # Cancel specific order by ID
    result = await api.exchange.cancel_order(
        asset="BTC",
        order_id=12345
    )

    # Cancel by client order ID
    my_cloid = Cloid.from_int(123456)
    result = await api.exchange.cancel_order_by_id(
        asset="BTC",
        client_order_id=my_cloid
    )

    # Schedule cancellation of all orders in 5 minutes
    from datetime import datetime, timedelta
    future_time = datetime.now() + timedelta(minutes=5)
    result = await api.exchange.schedule_cancellation(time=future_time)

    # Modify an existing order
    result = await api.exchange.modify_order(
        order_id=12345,
        asset="BTC",
        is_buy=True,
        size=Decimal("0.002"),  # New size
        limit_price=Decimal("66000"),  # New price
        order_type=LIMIT_GTC,  # New order type
        reduce_only=False
    )

asyncio.run(manage_orders())
```

## Order Types

Based on [Hyperliquid's official order type documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-types), the `hl-sdk` supports several order types for different trading strategies:

### Core Order Types

1. **Limit Orders** - Execute at specified price or better
2. **Stop Market Orders** - Market orders triggered when price reaches stop price
3. **Stop Limit Orders** - Limit orders triggered when price reaches stop price

### Limit Orders

Limit orders execute at your specified price or better and rest on the order book until filled or canceled.

```python
from decimal import Decimal
from hl import LIMIT_GTC, LIMIT_IOC, LIMIT_ALO

# Place a limit buy order using predefined constants
result = await api.exchange.place_order(
    asset="BTC",
    is_buy=True,
    size=Decimal("0.001"),
    limit_price=Decimal("65000"),  # Buy at $65,000 or lower
    order_type=LIMIT_GTC,  # Using predefined constant
    reduce_only=False
)

# Alternative: specify order type explicitly
result = await api.exchange.place_order(
    asset="BTC",
    is_buy=True,
    size=Decimal("0.001"),
    limit_price=Decimal("65000"),
    order_type={"type": "limit", "tif": "Gtc"},  # Explicit format
    reduce_only=False
)
```

#### Time in Force (TIF) Options

- **`"Gtc"` (Good Till Canceled)**: Order remains active until filled or manually canceled
- **`"Ioc"` (Immediate or Cancel)**: Execute immediately, cancel any unfilled portion
- **`"Alo"` (Add Liquidity Only)**: Only execute if it adds liquidity to the order book (Post Only)

```python
# Using predefined constants (recommended)
from hl import LIMIT_GTC, LIMIT_IOC, LIMIT_ALO

gtc_order = LIMIT_GTC    # Most common - rests on book
ioc_order = LIMIT_IOC    # Fill immediately or cancel
alo_order = LIMIT_ALO    # Post-only, adds liquidity

# Or specify explicitly
gtc_order = {"type": "limit", "tif": "Gtc"}
ioc_order = {"type": "limit", "tif": "Ioc"}
alo_order = {"type": "limit", "tif": "Alo"}
```

### Trigger Orders

Stop orders are triggered when the mark price reaches your specified trigger price. According to [Hyperliquid's TP/SL documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/take-profit-and-stop-loss-orders-tp-sl), these orders use the mark price for triggering and can be configured as market or limit orders.

#### Stop Market Orders

Stop market orders execute immediately as market orders when triggered, with a **10% slippage tolerance**.

```python
# Stop loss: Sell BTC if price drops to $64,000 (-10%)
result = await api.exchange.place_order(
    asset="BTC",
    is_buy=False,  # Sell order
    size=Decimal("0.001"),
    limit_price=Decimal("64000"),  # Price to which 10% slippage tolerance is applied
    order_type={
        "type": "trigger",
        "price": Decimal("64000"),  # Trigger price
        "is_market": True,          # Execute as market order (10% slippage tolerance)
        "trigger": "sl"             # Stop loss
    },
    reduce_only=True  # Only reduce existing position
)
```

#### Stop Limit Orders

Stop limit orders execute as limit orders when triggered, allowing you to control slippage by setting a specific limit price.

```python
# Stop limit order - executes as limit order when triggered
result = await api.exchange.place_order(
    asset="BTC",
    is_buy=False,  # Sell order
    size=Decimal("0.001"),
    limit_price=Decimal("63900"),  # Limit price used when triggered
    order_type={
        "type": "trigger",
        "price": Decimal("64000"),  # Trigger at $64,000
        "is_market": False,         # Execute as limit order at limit_price
        "trigger": "sl"             # Stop loss
    },
    reduce_only=True
)
```

#### Take Profit Orders

Take profit orders secure gains when price reaches your target. They can be market or limit orders.

```python
# Take profit with limit execution for price control
result = await api.exchange.place_order(
    asset="BTC",
    is_buy=False,  # Sell order
    size=Decimal("0.001"),
    limit_price=Decimal("70000"),  # Exact limit price when triggered
    order_type={
        "type": "trigger",
        "price": Decimal("70000"),  # Trigger at $70,000
        "is_market": False,         # Use limit price for controlled execution
        "trigger": "tp"             # Take profit
    },
    reduce_only=True
)
```

#### Stop Order Parameters

- **`type`**: Set to `"trigger"` for stop orders
- **`price`**: The mark price that activates the stop order
- **`is_market`**:
    - `True`: Execute as market order when triggered (10% slippage tolerance)
    - `False`: Execute as limit order when triggered (using the `limit_price`)
- **`trigger`**: Order purpose
    - `"sl"` (Stop Loss): Limit losses on existing positions
    - `"tp"` (Take Profit): Secure profits on existing positions

### Practical Order Type Usage

```python
from hl import LIMIT_GTC
from hl.types import is_resting_status, is_error_status, is_filled_status

async def demonstrate_order_types():
    api = await Api.create(account=account)

    # 1. Limit order - buy BTC at specific price or better
    limit_result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        limit_price=Decimal("65000"),
        order_type=LIMIT_GTC,  # Good till canceled
        reduce_only=False
    )

    # 2. Stop market order - guaranteed execution with 10% slippage tolerance
    stop_market_result = await api.exchange.place_order(
        asset="BTC",
        is_buy=False,
        size=Decimal("0.001"),
        limit_price=Decimal("64000"),  # Price to which 10% slippage tolerance is applied
        order_type={
            "type": "trigger",
            "price": Decimal("64000"),  # Triggered by mark price
            "is_market": True,          # Market execution (10% slippage tolerance)
            "trigger": "sl"             # Stop loss
        },
        reduce_only=True  # Only reduce existing position
    )

    # 3. Stop limit order - controlled execution price
    stop_limit_result = await api.exchange.place_order(
        asset="BTC",
        is_buy=False,
        size=Decimal("0.001"),
        limit_price=Decimal("63900"),  # Execute at this price when triggered
        order_type={
            "type": "trigger",
            "price": Decimal("64000"),  # Trigger price (mark price)
            "is_market": False,         # Use limit_price for execution
            "trigger": "sl"             # Stop loss
        },
        reduce_only=True
    )

    # 4. Take profit limit order - secure gains with price control
    take_profit_result = await api.exchange.place_order(
        asset="BTC",
        is_buy=False,
        size=Decimal("0.001"),
        limit_price=Decimal("70000"),  # Exact execution price
        order_type={
            "type": "trigger",
            "price": Decimal("70000"),  # Trigger when mark price reaches this
            "is_market": False,         # Use limit price for controlled execution
            "trigger": "tp"             # Take profit
        },
        reduce_only=True
    )

    # Handle order statuses using type guards
    if limit_result.is_ok():
        response = limit_result.unwrap()
        statuses = response["response"]["data"]["statuses"]
        for status in statuses:
            if is_resting_status(status):
                print(f"Limit order resting: {status['resting']['oid']}")
            elif is_error_status(status):
                print(f"Limit order failed: {status['error']}")
            elif is_filled_status(status):
                print(f"Limit order filled: {status['filled']}")

asyncio.run(demonstrate_order_types())
```

## Order Response Handling

**Important**: The top-level `status` field in the response does not indicate whether individual orders succeeded or failed. Instead, you must check the `statuses` list in the response data, which contains the actual result for each order.

### Response Structure

```python
{
    "status": "ok",  # Only indicates API call succeeded, not order success
    "response": {
        "type": "order",
        "data": {
            "statuses": [  # Check this for actual order results
                {"resting": {"oid": 123}},     # Order resting on book
                {"error": "Insufficient funds"}, # Order failed
                {"filled": {"oid": 124, "totalSz": "0.001", "avgPx": "65000"}}  # Order filled
            ]
        }
    }
}
```

### Handling Order Statuses with Type Guards

The SDK provides type guards for type-safe status checking:

```python
from hl.types import is_resting_status, is_error_status, is_filled_status

async def handle_order_response():
    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        limit_price=Decimal("65000"),
        order_type=LIMIT_GTC,
        reduce_only=False
    )

    if result.is_ok():
        response = result.unwrap()
        statuses = response["response"]["data"]["statuses"]

        for status in statuses:
            if is_resting_status(status):
                # Type is narrowed to OrderResponseDataStatusResting
                oid = status["resting"]["oid"]
                cloid = status["resting"].get("cloid")
                print(f"Order {oid} is resting on the book")

            elif is_error_status(status):
                # Type is narrowed to OrderResponseDataStatusError
                error_message = status["error"]
                print(f"Order failed: {error_message}")

            elif is_filled_status(status):
                # Type is narrowed to OrderResponseDataStatusFilled
                fill_data = status["filled"]
                oid = fill_data["oid"]
                size = fill_data["totalSz"]
                avg_price = fill_data["avgPx"]
                print(f"Order {oid} filled {size} at avg price {avg_price}")
```

### Alternative: Using Match Statements

You can also use Python's match statements for handling order statuses:

```python
async def handle_with_match():
    result = await api.exchange.place_order(...)

    if result.is_ok():
        response = result.unwrap()
        statuses = response["response"]["data"]["statuses"]

        for status in statuses:
            match status:
                case {"resting": {"oid": oid}}:
                    print(f"Order {oid} is resting")
                case {"error": error}:
                    print(f"Order failed: {error}")
                case {"filled": {"oid": oid, "totalSz": size, "avgPx": price}}:
                    print(f"Order {oid} filled {size} at {price}")
```

### Batch Order Handling

When placing multiple orders, the `statuses` list will contain one entry per order:

```python
async def handle_batch_orders():
    orders = [
        {"asset": "BTC", "is_buy": True, "size": Decimal("0.001"), 
         "limit_price": Decimal("65000"), "order_type": LIMIT_GTC, "reduce_only": False},
        {"asset": "ETH", "is_buy": False, "size": Decimal("0.1"), 
         "limit_price": Decimal("3500"), "order_type": LIMIT_IOC, "reduce_only": False}
    ]

    result = await api.exchange.place_orders(order_requests=orders)

    if result.is_ok():
        response = result.unwrap()
        statuses = response["response"]["data"]["statuses"]

        for i, status in enumerate(statuses):
            print(f"Order {i+1} ({orders[i]['asset']}) result:")

            if is_resting_status(status):
                oid = status["resting"]["oid"]
                print(f"  ✓ Resting as order {oid}")

            elif is_error_status(status):
                error = status["error"]
                print(f"  ✗ Failed: {error}")

            elif is_filled_status(status):
                fill = status["filled"]
                print(f"  ✓ Filled {fill['totalSz']} at {fill['avgPx']}")
```

## Error Handling

All Exchange methods return `Result[T, ApiError]` types for explicit error handling. However, a successful API call (`result.is_ok()`) doesn't guarantee order success - you must check individual order statuses.

```python
from hl import LIMIT_GTC
from hl.types import is_resting_status, is_error_status, is_filled_status

async def safe_trading():
    api = await Api.create(account=account)

    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        limit_price=Decimal("65000"),
        order_type=LIMIT_GTC,
        reduce_only=False
    )

    if result.is_ok():
        response = result.unwrap()

        # API call succeeded, but check individual order status
        statuses = response["response"]["data"]["statuses"]
        for status in statuses:
            if is_resting_status(status):
                oid = status["resting"]["oid"]
                print(f"✓ Order {oid} successfully placed and resting")

            elif is_error_status(status):
                error = status["error"]
                print(f"✗ Order failed: {error}")
                # Handle order-specific error (insufficient funds, etc.)

            elif is_filled_status(status):
                fill = status["filled"]
                print(f"✓ Order {fill['oid']} filled {fill['totalSz']} at {fill['avgPx']}")
    else:
        # API call failed (network, authentication, etc.)
        error = result.unwrap_err()
        print(f"API call failed: {error.message}")
        # Handle API-level error - perhaps retry or alert
```

### Two-Level Error Handling

There are two levels of errors to handle:

1. **API-level errors** (network, authentication, malformed requests)
2. **Order-level errors** (insufficient funds, invalid parameters, market conditions)

```python
async def comprehensive_error_handling():
    result = await api.exchange.place_orders(order_requests=[
        {"asset": "BTC", "is_buy": True, "size": Decimal("0.001"), 
         "limit_price": Decimal("65000"), "order_type": LIMIT_GTC, "reduce_only": False},
        {"asset": "NONEXISTENT", "is_buy": True, "size": Decimal("0.001"), 
         "limit_price": Decimal("100"), "order_type": LIMIT_GTC, "reduce_only": False}
    ])

    if result.is_ok():
        response = result.unwrap()
        statuses = response["response"]["data"]["statuses"]

        for i, status in enumerate(statuses):
            if is_resting_status(status):
                print(f"Order {i+1}: Successfully placed")
            elif is_error_status(status):
                error = status["error"]
                print(f"Order {i+1}: Failed - {error}")
            elif is_filled_status(status):
                print(f"Order {i+1}: Immediately filled")

    else:
        error = result.unwrap_err()
        print(f"API Error: {error.message}")
```

