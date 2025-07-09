# Getting Started

Welcome to the `hl-sdk` getting started guide! This section will walk you through the basics of using the Hyperliquid SDK for Python.

## Installation

Install the library using your preferred package manager:

=== "pip"

    ```bash
    pip install hl-sdk
    ```

=== "uv"

    ```bash
    uv add hl-sdk
    ```

## Basic Concepts

### The Api Class

The `Api` class is your main entry point for interacting with Hyperliquid. It provides access to three core components:

- **`api.info`** - Read-only endpoints for market data, user information, and exchange state
- **`api.exchange`** - Authenticated endpoints for trading, transfers, and account management
- **`api.ws`** - WebSocket interface for real-time subscriptions and operations

### Async/Await Pattern

The `hl-sdk` is built with async/await patterns for optimal performance. This means:

1. All API methods are async and must be awaited
2. Your code needs to run inside an async function
3. Use `asyncio.run()` to execute your main function

```python
import asyncio
from hl import Api

async def main():
    api = await Api.create()
    # Your code here

asyncio.run(main())
```

## Creating an Api Instance

### Without Authentication (Public Endpoints)

For public endpoints like market data, you can create an Api instance without credentials:

```python
import asyncio
from hl import Api

async def main():
    # Create API unauthenticated instance for mainnet (default)
    api = await Api.create()

asyncio.run(main())
```

### With Authentication (Private Endpoints)

For trading and account management, you'll need to provide credentials:

```python
import asyncio
import os
from hl import Api, Account

async def main():
    # Create account from environment variables
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    # Create authenticated API instance for mainnet (default)
    api = await Api.create(account=account)

asyncio.run(main())
```

### Choosing Your Network

`hl-sdk` supports both Hyperliquid's mainnet and testnet environments. Always test your strategies on testnet before deploying to mainnet.

```python
import asyncio
from hl import Api, Account, MAINNET, TESTNET

async def main():
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    # For development and testing (recommended first step)
    testnet_api = await Api.create(account=account, network=TESTNET)

    # For production trading (use only after thorough testing)
    mainnet_api = await Api.create(account=account, network=MAINNET)

    # Default is mainnet if not specified
    api = await Api.create(account=account)  # Same as network=MAINNET

asyncio.run(main())
```

## Understanding the Result Pattern

Before diving into the core functionalities, it's important to understand that all API methods in `hl-sdk` return a `Result[T, ApiError]` type instead of raising exceptions. This pattern provides explicit error handling and makes your code more robust.

### Working with Results

Every API call returns a `Result` that can be either:
- **Success**: Contains the expected data of type `T`
- **Error**: Contains an `ApiError` with details about what went wrong

```python
# Basic pattern for handling results
result = await api.info.all_mids()

if result.is_ok():
    # Success - get the data
    data = result.unwrap()
    print(f"Got data: {data}")
else:
    # Error - get the error details
    error = result.unwrap_err()
    print(f"API Error: {error.message}")
```

### Key Methods

- **`result.is_ok()`** - Returns `True` if the operation succeeded
- **`result.is_err()`** - Returns `True` if the operation failed
- **`result.unwrap()`** - Gets the success value (only call after checking `is_ok()`)
- **`result.unwrap_err()`** - Gets the error details (only call after checking `is_err()`)

This approach ensures you always handle both success and failure cases explicitly, making your trading applications more robust.

## Core Functionalities

### Info Endpoints (Market Data)

Access read-only market information:

```python
import asyncio
from hl import Api

async def main():
    api = await Api.create()

    # Get all mid prices
    result = await api.info.all_mids()
    if result.is_ok():
        prices = result.unwrap()
        print(f"BTC price: ${prices.get('BTC', 'N/A')}")

    # Get L2 order book
    result = await api.info.l2_book(asset="ETH")
    if result.is_ok():
        book = result.unwrap()
        print(f"ETH order book: {book}")

    # Get user's open orders (requires authentication)
    # result = await api.info.user_open_orders()

asyncio.run(main())
```

### Exchange Endpoints (Trading)

Execute trades and manage your account:

```python
import asyncio
import os
from decimal import Decimal
from hl import Api, Account, LIMIT_GTC

async def main():
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    api = await Api.create(account=account)

    # Place a limit order
    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        limit_price=Decimal("65000"),
        order_type=LIMIT_GTC,  # Good till canceled
        reduce_only=False
    )

    if result.is_ok():
        response = result.unwrap()
        print(f"Order placed: {response}")
    else:
        print(f"Error: {result.unwrap_err()}")

asyncio.run(main())
```

### WebSocket Operations

Stream real-time data and execute operations via WebSocket:

```python
import asyncio
from hl import Api

async def main():
    api = await Api.create()

    # Use the WebSocket context manager
    async with api.ws.run():
        # Subscribe to price updates
        sub_id, queue = await api.ws.subscriptions.all_mids()

        # Process 5 price updates
        for i in range(5):
            msg = await queue.get()
            print(f"Update {i+1}: {msg}")

        # Unsubscribe when done
        await api.ws.subscriptions.unsubscribe(sub_id)

asyncio.run(main())
```

## Important Notes

### Use Decimal for Prices and Sizes

Always use `Decimal` for numeric values to avoid floating-point precision issues:

```python
from decimal import Decimal

# ❌ Wrong - using float
size = 0.1
price = 65000.0

# ✅ Correct - using Decimal
size = Decimal("0.1")
price = Decimal("65000")
```

### Type Safety

The SDK provides comprehensive type definitions. Use them for better code reliability:

```python
from hl.types import LimitOrderType

order_type = LimitOrderType(type="limit", tif="Gtc")  # or "trigger"
```

## Next Steps

- Learn more about [Authentication](authentication.md) for private endpoints
- Explore [Examples](examples.md) for complete working code
- Check the [API Reference](../reference/api.md) for detailed method documentation
- Review [Types Reference](../reference/types.md) for all available data structures

