# Api Class

The `Api` class is the central entry point for interacting with Hyperliquid through `hl-sdk`. It provides a unified interface to all SDK functionality while automatically managing shared resources like authentication and asset metadata.

## Overview

The `Api` class serves as a coordinating facade that:

- **Unifies Access**: Provides a single point of access to all Hyperliquid functionality
- **Manages Authentication**: Automatically propagates account credentials to all components
- **Handles Asset Metadata**: Fetches and shares Universe data across the SDK
- **Coordinates Components**: Ensures info, exchange, and WebSocket clients work together seamlessly

Rather than managing separate clients for different endpoints, the `Api` class gives you everything you need through three main properties:

- **`api.info`** - Market data, user information, and exchange state queries
- **`api.exchange`** - Trading operations, transfers, and account management
- **`api.ws`** - Real-time WebSocket subscriptions and operations

## Creating an Api Instance

!!! warning "Use Api.create(), Not Constructor"
    Never instantiate `Api` directly using `Api()`. Always use the `Api.create()` class method, which properly initializes all components and fetches required metadata.

### Basic Creation

```python
import asyncio
from hl import Api

async def main():
    # Create unauthenticated API for public endpoints
    api = await Api.create()

    # Access public market data
    result = await api.info.all_mids()
    if result.is_ok():
        prices = result.unwrap()
        print(f"BTC Price: ${prices.get('BTC', 'N/A')}")

asyncio.run(main())
```

### With Authentication

```python
import asyncio
import os
from hl import Api, Account

async def main():
    # Create account with credentials
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    # Create authenticated API
    api = await Api.create(account=account)

    # Now you can access private endpoints
    result = await api.info.user_state()
    if result.is_ok():
        state = result.unwrap()
        print(f"Available balance: ${state['withdrawable']}")

asyncio.run(main())
```

### Network Selection

```python
from hl import Api, Account, MAINNET, TESTNET

# Specify network explicitly
testnet_api = await Api.create(
    account=account,
    network=TESTNET  # Use testnet for development
)

mainnet_api = await Api.create(
    account=account,
    network=MAINNET  # Use mainnet for production (default)
)

# Default is mainnet
api = await Api.create(account=account)  # Same as network=MAINNET
```

## Core Components

The `Api` class exposes three main components for different types of operations:

### Info Component (`api.info`)

Access read-only market data and user information:

```python
# Market data (no authentication required)
prices_result = await api.info.all_mids()
book_result = await api.info.l2_book(asset="BTC")
meta_result = await api.info.perpetual_meta()

# User data (authentication required)
orders_result = await api.info.user_open_orders()
state_result = await api.info.user_state()
fills_result = await api.info.user_fills()
```

### Exchange Component (`api.exchange`)

Execute trading operations and account management:

```python
from decimal import Decimal

# Place orders
order_result = await api.exchange.place_order(
    asset="BTC",
    is_buy=True,
    size=Decimal("0.001"),
    limit_price=Decimal("65000"),
    order_type={"limit": {"tif": "Gtc"}},
    reduce_only=False
)

# Cancel orders
cancel_result = await api.exchange.cancel_order(asset="BTC", order_id=12345)

# Transfer funds
transfer_result = await api.exchange.transfer_usd(
    destination="0x...",
    amount=Decimal("100")
)
```

### WebSocket Component (`api.ws`)

Real-time data subscriptions and operations:

```python
# Subscribe to real-time data
async with api.ws.run():
    # Price updates
    price_sub, price_queue = await api.ws.subscriptions.all_mids()

    # Order book updates
    book_sub, book_queue = await api.ws.subscriptions.l2_book(asset="BTC")

    # User order updates (authentication required)
    order_sub, order_queue = await api.ws.subscriptions.order_updates()

    # Process updates
    price_update = await price_queue.get()
    print(f"Price update: {price_update}")

    # Clean up subscriptions
    await api.ws.subscriptions.unsubscribe(price_sub)
    await api.ws.subscriptions.unsubscribe(book_sub)
    await api.ws.subscriptions.unsubscribe(order_sub)
```

## Runtime Configuration Changes

The `Api` class allows you to change authentication and universe data during runtime by setting properties. Changes automatically propagate to all components.

### Changing Account at Runtime

```python
from hl import Account

# Create API without authentication
api = await Api.create()

# Add authentication later
trading_account = Account(
    address=os.environ["HL_ADDRESS"],
    secret_key=os.environ["HL_SECRET_KEY"]
)

# Set account - automatically propagates to all components
api.account = trading_account

# Now you can access authenticated endpoints
result = await api.exchange.place_order(...)

# Switch to different account
vault_account = Account(
    address=os.environ["HL_VAULT_ADDRESS"],
    secret_key=os.environ["HL_VAULT_SECRET_KEY"],
    vault_address=os.environ["HL_VAULT_ADDRESS"]
)

api.account = vault_account  # Switch authentication

# Remove authentication
api.account = None  # Back to public endpoints only
```

### Updating Universe at Runtime

```python
# Get fresh universe data
fresh_universe = await api.info.get_universe()

# Update the universe - propagates to all components
api.universe = fresh_universe

# This is useful if new assets are added to the exchange
# or if you want to refresh metadata
```

### Practical Runtime Configuration Example

```python
async def multi_account_trading():
    # Start without authentication
    api = await Api.create(network=TESTNET)

    # Get market data first
    prices = await api.info.all_mids()

    # Switch to trading account
    trading_account = Account(
        address=os.environ["HL_TRADING_ADDRESS"],
        secret_key=os.environ["HL_TRADING_SECRET"]
    )
    api.account = trading_account

    # Place trades
    await api.exchange.place_order(...)

    # Switch to vault account for different strategy
    vault_account = Account(
        address=os.environ["HL_VAULT_ADDRESS"],
        secret_key=os.environ["HL_VAULT_SECRET"],
        vault_address=os.environ["HL_VAULT_ADDRESS"]
    )
    api.account = vault_account

    # Execute vault operations
    await api.exchange.place_order(...)

    # Update universe if needed (e.g., new assets added)
    api.universe = await api.info.get_universe()
```

## Initialization Details

When you call `Api.create()`, the following happens:

1. **Transport Creation**: HTTP transports are created for the specified network
2. **Universe Loading**: Two API calls are made to fetch asset metadata:
   - `perpetual_meta()` - Gets all perpetual trading pairs
   - `spot_meta()` - Gets all spot trading pairs
3. **Component Creation**: Info, Exchange, and WebSocket components are initialized
4. **Property Propagation**: Account and Universe are shared across all components

This ensures all components have consistent access to authentication and asset metadata.

## Next Steps

- Learn about [Authentication](authentication.md) for account management
- Explore [Info endpoints](info.md) for market data
- Review [Exchange operations](exchange.md) for trading
- Understand the [WebSocket API](ws/websocket-api.md) for real-time data
- Check [Universe management](universe.md) for asset handling
