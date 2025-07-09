# Examples

The `hl-sdk` repository includes several working examples to help you get started quickly. These examples demonstrate common patterns and best practices for using the SDK.

## Where to Find Examples

All examples are located in the [`examples/`](https://github.com/papicapital/hl-sdk/tree/main/examples) directory of the GitHub repository.

## Available Examples

### Basic Examples

#### `authentication.py`
Demonstrates the fundamentals of authentication:
- Creating an Account from environment variables
- Initializing an authenticated API client
- Making authenticated requests

#### `retrieve_meta.py`
Shows how to retrieve market metadata:
- Fetching perpetual asset information
- Accessing spot market metadata
- Understanding the Universe structure

### Trading Examples

#### `place_order.py`
Demonstrates simple order placement:
- Fetching current market prices
- Calculating order prices with proper rounding
- Placing limit orders with error handling
- Processing order response statuses (resting, filled, error)
- Using type guards for response validation

#### `basic_builder_fee.py`
Illustrates builder fee management:
- Approving builder fees
- Checking maximum builder fees
- Understanding fee structures

### Account Management

#### `monitor_balance.py`
Comprehensive account balance monitoring:
- Displaying perpetual account balances and positions
- Showing spot account balances with USD value calculations
- Listing open orders across all markets
- Displaying recent trading fills
- Calculating total portfolio value
- Detailed account overview with formatted output

### Market Analysis

#### `analyze_orderbook.py`
Advanced order book analysis and market depth:
- Analyzing order books for multiple assets (BTC, ETH, SOL)
- Calculating spread metrics (bid-ask spread, mid price)
- Displaying top order book levels with cumulative depth
- Liquidity analysis at different percentage distances
- Market impact analysis for various trade sizes
- Order book imbalance calculations
- Formatted tabular output for easy reading

### Real-time Data

#### `subscribe_ws.py`
Demonstrates WebSocket subscriptions:
- Connecting to WebSocket streams
- Subscribing to market data
- Handling real-time updates
- Proper connection management

## Running the Examples

1. **Clone the repository:**
   ```bash
   git clone https://github.com/papicapital/hl-sdk.git
   cd hl-sdk
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   # or
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   export HL_ADDRESS="your-wallet-address"
   export HL_SECRET_KEY="your-secret-key"
   ```

4. **Run an example:**
   ```bash
   python examples/authentication.py
   ```

## Example Structure

Each example follows a similar pattern:

```python
import asyncio
import os
from hl import Api, Account

async def main():
    # Setup
    account = Account(
        address=os.environ["HL_ADDRESS"],
        secret_key=os.environ["HL_SECRET_KEY"]
    )

    api = await Api.create(account=account)

    # Main logic
    # ... your code here ...

    # Cleanup (if needed)

if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing Examples

We welcome contributions! If you've built something useful with `hl-sdk`, consider submitting a pull request with your example.

### Guidelines for Examples

1. **Keep it focused**: Each example should demonstrate one concept clearly
2. **Add comments**: Explain what each section does
3. **Handle errors**: Show proper error handling patterns
4. **Use type hints**: Demonstrate the SDK's type safety features
5. **Follow conventions**: Use the same structure as existing examples

## More Complex Examples

For more sophisticated usage patterns, check out:

- **Trading Strategies**: Combining multiple API calls for automated trading
- **Market Making**: Using WebSocket streams for real-time market making
- **Portfolio Management**: Tracking positions and P&L across multiple assets
- **Risk Management**: Implementing position limits and stop losses

These advanced examples are continuously being added to the repository.

## Need Help?

If you can't find an example for your use case:

1. Check the [API Reference](../reference/api.md) for detailed method documentation
2. Browse [GitHub Issues](https://github.com/papicapital/hl-sdk/issues) for similar questions
3. Join the [GitHub Discussions](https://github.com/papicapital/hl-sdk/discussions) to ask the community
4. Submit a [feature request](https://github.com/papicapital/hl-sdk/issues/new) for new examples

## Quick Example Links

- [Simple order placement](https://github.com/papicapital/hl-sdk/blob/main/examples/place_order.py) - Learn how to place limit orders with proper error handling
- [WebSocket price streaming](https://github.com/papicapital/hl-sdk/blob/main/examples/subscribe_ws.py) - Real-time market data subscriptions
- [Account balance monitoring](https://github.com/papicapital/hl-sdk/blob/main/examples/monitor_balance.py) - Comprehensive portfolio and balance overview
- [Order book analysis](https://github.com/papicapital/hl-sdk/blob/main/examples/analyze_orderbook.py) - Advanced market depth and liquidity analysis
- [Authentication patterns](https://github.com/papicapital/hl-sdk/blob/main/examples/authentication.py) - Different ways to authenticate API calls
- [Market metadata](https://github.com/papicapital/hl-sdk/blob/main/examples/retrieve_meta.py) - Fetching asset information and universe data
- [Builder fee management](https://github.com/papicapital/hl-sdk/blob/main/examples/basic_builder_fee.py) - Working with builder fees
