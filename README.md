# Unofficial Hyperliquid Python SDK

📚 **[Documentation](https://papicapital.github.io/hl-sdk/)** | **[API Reference](https://papicapital.github.io/hl-sdk/reference/api/)** | **[Examples](./examples/)**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A high-performance, async Python SDK for interacting with the [Hyperliquid](https://hyperliquid.xyz) decentralized exchange.

## Features

- 🚀 **Async/await support** - Built for high-performance async applications
- 📊 **Complete API coverage** - Leverage all available Hyperliquid functionalities
- 🔄 **WebSocket support** - Real-time market data and order updates
- 🛡️ **Type-safe** - Full type hints and runtime error handling

## Installation

### Requirements

- Python 3.11 or higher

### Install from PyPI

```bash
pip install hl-sdk
```

### Install from source

```bash
git clone https://github.com/papicapital/hl-sdk.git
cd hl-sdk
pip install -e .
```

## Quickstart

### Basic Usage

```python
import asyncio
from hl import Api, TESTNET
from hl.account import Account

async def main():
    # Initialize with your credentials
    account = Account(
        address="0xYourAddress",
        secret_key="0xYourSecretKey"
    )

    # Create API client, network defaults to MAINNET if not provided
    api = await Api.create(account=account, network=TESTNET)

    # Get market data
    meta_result = await api.info.perpetual_meta()
    if meta_result.is_ok():
        meta = meta_result.unwrap()
        print(f"Connected to Hyperliquid: {len(meta['universe'])} markets available")

    # Get your open orders
    orders_result = await api.info.user_open_orders()
    if orders_result.is_ok():
        orders = orders_result.unwrap()
        print(f"You have {len(orders)} open orders")

if __name__ == "__main__":
    asyncio.run(main())
```

### Environment Variables

For security, store your credentials in environment variables:

```bash
export HL_ADDRESS="0xYourAddress"
export HL_SECRET_KEY="0xYourSecretKey"
```

Then in your code:

```python
import os
from hl.account import Account

account = Account(
    address=os.environ["HL_ADDRESS"],
    secret_key=os.environ["HL_SECRET_KEY"]
)
```

### Place an Order

```python
from hl import Api, Account, LIMIT_GTC, TESTNET
from hl.types import is_resting_status, is_error_status, is_filled_status

async def place_limit_order():
    # Create API client
    api = await Api.create(account=account, network=TESTNET)

    # Create a limit order
    result = await api.exchange.place_order(
        asset="BTC",
        is_buy=True,
        size=Decimal("0.001"),  # Size in BTC
        limit_price=Decimal("50000.0"),  # Limit price
        order_type=LIMIT_GTC,  # Good till canceled
        reduce_only=False
    )

    # Handle the result
    if result.is_ok():
        response = result.unwrap()
        print(f"Order request sent successfully!")

        # Check individual order statuses
        statuses = response["response"]["data"]["statuses"]
        for status in statuses:
            if is_resting_status(status):
                print(f"Order resting with ID: {status['resting']['oid']}")
            elif is_error_status(status):
                print(f"Order failed: {status['error']}")
            elif is_filled_status(status):
                fill = status["filled"]
                print(f"Order filled: {fill['totalSz']} at ${fill['avgPx']}")
    else:
        error = result.unwrap_err()
        print(f"Error placing order: {error}")
```

### WebSocket Subscriptions

```python
async def stream_orderbook():
    # Create API client, by default on mainnet
    api = await Api.create(account=account)
    
    # Use WebSocket context manager
    async with api.ws.run():
        # Subscribe to the L2 book for BTC
        sub_id, queue = await api.ws.subscriptions.l2_book(asset="BTC")

        # Process incoming messages
        for _ in range(10):  # Process 10 messages
            msg = await queue.get()
            print(f"Orderbook update: {msg}")

        # Unsubscribe when done
        await api.ws.subscriptions.unsubscribe(sub_id)
```

## Examples

Check out the [examples](./examples/) directory for more detailed examples:

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/papicapital/hl-sdk.git
cd hl-sdk

# Install with development dependencies
uv sync --all-groups

# Install pre-commit hooks
uv run pre-commit install
```

### Run Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy hl tests
```

### Code Formatting

```bash
uv run ruff check --fix
uv run ruff format
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://papicapital.github.io/hl-sdk/contributing/) for details.

## Support

- 📚 [Documentation](https://papicapital.github.io/hl-sdk/)
- 🐛 [Issue Tracker](https://github.com/papicapital/hl-sdk/issues)
- 💬 [Discussions](https://github.com/papicapital/hl-sdk/discussions)
- 🗣️ [Discord Community - Papi's Pit](https://discord.gg/rDAG9RTsbj)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial SDK and is not affiliated with Hyperliquid. Use at your own risk.


